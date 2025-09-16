"""
Sistema H2 - Gerenciador de Cache Multi-Camadas

Módulo principal para gerenciamento centralizado de cache.
"""

import asyncio
import json
import pickle
import time
import zlib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union


class CacheBackend(Enum):
    """Tipos de backend de cache disponíveis."""

    MEMORY = "memory"
    REDIS = "redis"
    HYBRID = "hybrid"


class CompressionType(Enum):
    """Tipos de compressão suportados."""

    NONE = "none"
    ZLIB = "zlib"
    GZIP = "gzip"


@dataclass
class CacheEntry:
    """Entrada de cache com metadados."""

    key: str
    value: Any
    created_at: datetime
    expires_at: Optional[datetime]
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    size_bytes: int = 0
    compressed: bool = False
    backend: str = "memory"


@dataclass
class CacheConfig:
    """Configuração do sistema de cache."""

    default_ttl: int = 3600  # 1 hora
    max_memory_size: int = 100 * 1024 * 1024  # 100MB
    max_entries: int = 10000
    compression_threshold: int = 1024  # Comprimir se > 1KB
    compression_type: CompressionType = CompressionType.ZLIB
    eviction_policy: str = "lru"  # lru, lfu, ttl
    redis_url: Optional[str] = None
    enable_metrics: bool = True


class CacheBackendInterface(ABC):
    """Interface base para backends de cache."""

    @abstractmethod
    async def get(self, key: str) -> Optional[CacheEntry]:
        """Obtém item do cache."""
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Define item no cache."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Remove item do cache."""
        pass

    @abstractmethod
    async def clear(self) -> bool:
        """Limpa todo o cache."""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Verifica se chave existe."""
        pass

    @abstractmethod
    async def keys(self, pattern: str = "*") -> List[str]:
        """Lista chaves que correspondem ao padrão."""
        pass

    @abstractmethod
    async def stats(self) -> Dict[str, Any]:
        """Obtém estatísticas do backend."""
        pass


class CacheManager:
    """Gerenciador principal do sistema de cache multi-camadas."""

    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig()
        self.backends: Dict[str, CacheBackendInterface] = {}
        self.metrics_enabled = self.config.enable_metrics

        # Métricas internas
        self._hits = 0
        self._misses = 0
        self._sets = 0
        self._deletes = 0
        self._errors = 0

        # Inicializar sistema de métricas
        self._initialize_metrics()

        # Cache local para metadados
        self._metadata: Dict[str, CacheEntry] = {}

    def _initialize_metrics(self):
        """Inicializa sistema de métricas."""
        try:
            from .metrics import get_cache_metrics

            self.metrics_system = get_cache_metrics()
        except ImportError:
            self.metrics_system = None

    async def initialize(self):
        """Inicializa o sistema de cache."""
        try:
            # Inicializar backend de memória (sempre disponível)
            from .memory_cache import MemoryCache

            memory_cache = MemoryCache(self.config)
            await memory_cache.initialize()
            self.backends["memory"] = memory_cache

            # Inicializar Redis se configurado
            if self.config.redis_url:
                try:
                    from .redis_cache import RedisCache

                    redis_cache = RedisCache(self.config)
                    await redis_cache.initialize()
                    self.backends["redis"] = redis_cache
                except Exception as e:
                    print(f"Warning: Failed to initialize Redis cache: {e}")

            print(
                f"Cache system initialized with backends: {list(self.backends.keys())}"
            )

        except Exception as e:
            print(f"Error initializing cache system: {e}")
            raise

    async def get(self, key: str, backend: Optional[str] = None) -> Optional[Any]:
        """
        Obtém valor do cache.

        Args:
            key: Chave do cache
            backend: Backend específico (opcional)

        Returns:
            Valor do cache ou None se não encontrado
        """
        try:
            # Determinar backends a consultar
            backends_to_check = []
            if backend:
                if backend in self.backends:
                    backends_to_check = [backend]
                else:
                    self._record_error()
                    return None
            else:
                # Ordem de prioridade: memory -> redis
                backends_to_check = ["memory", "redis"]

            # Consultar backends
            for backend_name in backends_to_check:
                if backend_name not in self.backends:
                    continue

                backend_obj = self.backends[backend_name]
                entry = await backend_obj.get(key)

                if entry is not None:
                    # Verificar expiração
                    if entry.expires_at and datetime.now() > entry.expires_at:
                        await self.delete(key)
                        continue

                    # Atualizar metadados
                    entry.access_count += 1
                    entry.last_accessed = datetime.now()

                    # Cache hit
                    self._record_hit()

                    # Registrar hit no sistema de métricas
                    if hasattr(self, "metrics_system") and self.metrics_system:
                        self.metrics_system.record_hit(key, backend_name, 0.0)

                    # Verificar se valor foi comprimido usando metadados
                    final_value = entry.value
                    if key in self._metadata and self._metadata[key].compressed:
                        try:
                            final_value = self._decompress_value(entry.value)
                        except Exception as e:
                            print(f"Error decompressing value for key {key}: {e}")
                            return None

                    # Promover para cache de memória se veio do Redis
                    if backend_name == "redis" and "memory" in self.backends:
                        await self.backends["memory"].set(
                            key, final_value, self._get_ttl_seconds(entry)
                        )

                    return final_value

            # Cache miss
            self._record_miss()

            # Registrar miss no sistema de métricas
            if hasattr(self, "metrics_system") and self.metrics_system:
                self.metrics_system.record_miss(key, "unknown", 0.0)

            return None

        except Exception as e:
            self._record_error()
            print(f"Error getting cache key {key}: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        backend: Optional[str] = None,
        compress: bool = False,
    ) -> bool:
        """
        Define valor no cache.

        Args:
            key: Chave do cache
            value: Valor a ser armazenado
            ttl: Time to live em segundos
            backend: Backend específico (opcional)
            compress: Forçar compressão

        Returns:
            True se sucesso, False caso contrário
        """
        try:
            # Aplicar compressão se necessário
            processed_value = value
            compressed = False

            if compress or self._should_compress(value):
                try:
                    processed_value = self._compress_value(value)
                    compressed = True
                except Exception as e:
                    print(f"Compression failed for key {key}: {e}")
                    processed_value = value

            # Determinar TTL
            effective_ttl = ttl or self.config.default_ttl
            expires_at = datetime.now() + timedelta(seconds=effective_ttl)

            # Determinar backends
            backends_to_use = []
            if backend:
                if backend in self.backends:
                    backends_to_use = [backend]
                else:
                    self._record_error()
                    return False
            else:
                # Escrever em todos os backends disponíveis
                backends_to_use = list(self.backends.keys())

            # Escrever nos backends
            success = True
            entry = None  # Initialize entry

            for backend_name in backends_to_use:
                backend_obj = self.backends[backend_name]

                # Criar entrada de cache (uma vez)
                if entry is None:
                    entry = CacheEntry(
                        key=key,
                        value=processed_value,
                        created_at=datetime.now(),
                        expires_at=expires_at,
                        size_bytes=self._calculate_size(processed_value),
                        compressed=compressed,
                        backend=backend_name,
                    )

                result = await backend_obj.set(key, processed_value, effective_ttl)
                if not result:
                    success = False
                    print(f"Failed to set key {key} in backend {backend_name}")

            if success and entry is not None:
                self._record_set()
                # Atualizar metadados
                self._metadata[key] = entry

                # Registrar set no sistema de métricas
                if hasattr(self, "metrics_system") and self.metrics_system:
                    self.metrics_system.record_set(
                        key,
                        backends_to_use[0] if backends_to_use else "unknown",
                        0.0,
                        entry.size_bytes,
                    )
            else:
                self._record_error()

            return success

        except Exception as e:
            self._record_error()
            print(f"Error setting cache key {key}: {e}")
            return False

    async def delete(self, key: str, backend: Optional[str] = None) -> bool:
        """
        Remove valor do cache.

        Args:
            key: Chave a ser removida
            backend: Backend específico (opcional)

        Returns:
            True se sucesso, False caso contrário
        """
        try:
            # Determinar backends
            backends_to_use = []
            if backend:
                if backend in self.backends:
                    backends_to_use = [backend]
                else:
                    return False
            else:
                backends_to_use = list(self.backends.keys())

            # Remover dos backends
            success = True
            for backend_name in backends_to_use:
                backend_obj = self.backends[backend_name]
                result = await backend_obj.delete(key)
                if not result:
                    success = False

            # Remover metadados
            if key in self._metadata:
                del self._metadata[key]

            if success:
                self._record_delete()
            else:
                self._record_error()

            return success

        except Exception as e:
            self._record_error()
            print(f"Error deleting cache key {key}: {e}")
            return False

    async def clear(self, backend: Optional[str] = None) -> bool:
        """
        Limpa o cache.

        Args:
            backend: Backend específico (opcional)

        Returns:
            True se sucesso, False caso contrário
        """
        try:
            backends_to_clear = []
            if backend:
                if backend in self.backends:
                    backends_to_clear = [backend]
                else:
                    return False
            else:
                backends_to_clear = list(self.backends.keys())

            success = True
            for backend_name in backends_to_clear:
                backend_obj = self.backends[backend_name]
                result = await backend_obj.clear()
                if not result:
                    success = False

            # Limpar metadados
            if not backend:  # Se limpou todos os backends
                self._metadata.clear()

            return success

        except Exception as e:
            self._record_error()
            print(f"Error clearing cache: {e}")
            return False

    async def exists(self, key: str, backend: Optional[str] = None) -> bool:
        """Verifica se chave existe no cache."""
        try:
            value = await self.get(key, backend)
            return value is not None
        except Exception:
            return False

    async def keys(
        self, pattern: str = "*", backend: Optional[str] = None
    ) -> List[str]:
        """Lista chaves que correspondem ao padrão."""
        try:
            if backend:
                if backend in self.backends:
                    return await self.backends[backend].keys(pattern)
                else:
                    return []
            else:
                # Combinar chaves de todos os backends
                all_keys = set()
                for backend_obj in self.backends.values():
                    keys = await backend_obj.keys(pattern)
                    all_keys.update(keys)
                return list(all_keys)
        except Exception as e:
            print(f"Error listing keys: {e}")
            return []

    async def get_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas completas do cache."""
        try:
            # Estatísticas gerais
            total_requests = self._hits + self._misses
            hit_rate = (self._hits / total_requests) if total_requests > 0 else 0

            stats = {
                "general": {
                    "hits": self._hits,
                    "misses": self._misses,
                    "hit_rate": hit_rate,
                    "sets": self._sets,
                    "deletes": self._deletes,
                    "errors": self._errors,
                    "total_requests": total_requests,
                },
                "backends": {},
                "metadata": {
                    "total_entries": len(self._metadata),
                    "config": {
                        "default_ttl": self.config.default_ttl,
                        "max_memory_size": self.config.max_memory_size,
                        "max_entries": self.config.max_entries,
                        "compression_threshold": self.config.compression_threshold,
                    },
                },
            }

            # Estatísticas por backend
            for name, backend in self.backends.items():
                backend_stats = await backend.stats()
                stats["backends"][name] = backend_stats

            return stats

        except Exception as e:
            print(f"Error getting cache stats: {e}")
            return {}

    def _should_compress(self, value: Any) -> bool:
        """Determina se valor deve ser comprimido."""
        try:
            size = self._calculate_size(value)
            return size > self.config.compression_threshold
        except Exception:
            return False

    def _compress_value(self, value: Any) -> bytes:
        """Comprime valor usando algoritmo configurado."""
        try:
            # Serializar valor
            if isinstance(value, (str, bytes)):
                data = value.encode() if isinstance(value, str) else value
            else:
                data = pickle.dumps(value)

            # Aplicar compressão
            if self.config.compression_type == CompressionType.ZLIB:
                return zlib.compress(data)
            else:
                return data  # Sem compressão

        except Exception as e:
            print(f"Error compressing value: {e}")
            raise

    def _decompress_value(self, compressed_data: bytes) -> Any:
        """Descomprime valor."""
        try:
            if self.config.compression_type == CompressionType.ZLIB:
                data = zlib.decompress(compressed_data)
            else:
                data = compressed_data

            # Tentar deserializar
            try:
                return pickle.loads(data)
            except Exception:
                return data.decode() if isinstance(data, bytes) else data

        except Exception as e:
            print(f"Error decompressing value: {e}")
            raise

    def _calculate_size(self, value: Any) -> int:
        """Calcula tamanho aproximado do valor."""
        try:
            if isinstance(value, str):
                return len(value.encode())
            elif isinstance(value, bytes):
                return len(value)
            else:
                return len(pickle.dumps(value))
        except Exception:
            return 0

    def _get_ttl_seconds(self, entry: CacheEntry) -> Optional[int]:
        """Calcula TTL restante em segundos."""
        if not entry.expires_at:
            return None

        remaining = entry.expires_at - datetime.now()
        return max(0, int(remaining.total_seconds()))

    def _record_hit(self):
        """Registra cache hit."""
        if self.metrics_enabled:
            self._hits += 1
            # Integrar com sistema de métricas global
            if hasattr(self, "metrics_system") and self.metrics_system:
                # Métrica será registrada nos métodos de get/set
                pass

    def _record_miss(self):
        """Registra cache miss."""
        if self.metrics_enabled:
            self._misses += 1
            # Integrar com sistema de métricas global
            if hasattr(self, "metrics_system") and self.metrics_system:
                # Métrica será registrada nos métodos de get/set
                pass

    def _record_set(self):
        """Registra operação de set."""
        if self.metrics_enabled:
            self._sets += 1

    def _record_delete(self):
        """Registra operação de delete."""
        if self.metrics_enabled:
            self._deletes += 1

    def _record_error(self):
        """Registra erro."""
        if self.metrics_enabled:
            self._errors += 1

    def get_backend_name(self) -> str:
        """Obtém nome do backend ativo."""
        if "redis" in self.backends:
            return "redis"
        elif "memory" in self.backends:
            return "memory"
        else:
            return "unknown"


# Instância global
_cache_manager: Optional[CacheManager] = None


async def get_cache_manager(config: Optional[CacheConfig] = None) -> CacheManager:
    """Obtém instância global do cache manager (async)."""
    global _cache_manager

    if _cache_manager is None:
        if config is None:
            config = CacheConfig()

        _cache_manager = CacheManager(config)
        await _cache_manager.initialize()

    return _cache_manager


def get_cache_manager_sync(config: Optional[CacheConfig] = None) -> CacheManager:
    """Obtém instância global do cache manager (síncrono)."""
    global _cache_manager

    if _cache_manager is None:
        if config is None:
            config = CacheConfig()

        _cache_manager = CacheManager(config)
        # Para uso síncrono, não inicializa async

    return _cache_manager


def reset_cache_manager():
    """Reseta instância global (para testes)."""
    global _cache_manager
    _cache_manager = None
