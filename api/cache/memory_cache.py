"""
Sistema H2 - Cache em Memória

Implementação de cache em memória com LRU e TTL.
"""

import asyncio
import threading
import time
from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .manager import CacheBackendInterface, CacheConfig, CacheEntry


class LRUCache:
    """Cache LRU (Least Recently Used) thread-safe."""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache: OrderedDict = OrderedDict()
        self.lock = threading.RLock()

    def get(self, key: str) -> Optional[Any]:
        """Obtém item do cache LRU."""
        with self.lock:
            if key in self.cache:
                # Mover para o final (mais recente)
                value = self.cache.pop(key)
                self.cache[key] = value
                return value
            return None

    def set(self, key: str, value: Any) -> bool:
        """Define item no cache LRU."""
        with self.lock:
            if key in self.cache:
                # Atualizar valor existente
                self.cache.pop(key)
            elif len(self.cache) >= self.max_size:
                # Remover item mais antigo
                self.cache.popitem(last=False)

            self.cache[key] = value
            return True

    def delete(self, key: str) -> bool:
        """Remove item do cache."""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False

    def clear(self) -> bool:
        """Limpa todo o cache."""
        with self.lock:
            self.cache.clear()
            return True

    def keys(self) -> List[str]:
        """Lista todas as chaves."""
        with self.lock:
            return list(self.cache.keys())

    def size(self) -> int:
        """Retorna número de itens."""
        with self.lock:
            return len(self.cache)


class MemoryCache(CacheBackendInterface):
    """Cache em memória com TTL e LRU."""

    def __init__(self, config: CacheConfig):
        self.config = config
        self.cache = LRUCache(config.max_entries)
        self.ttl_cache: Dict[str, datetime] = {}
        self.metadata: Dict[str, CacheEntry] = {}
        self.lock = threading.RLock()

        # Estatísticas
        self.stats_hits = 0
        self.stats_misses = 0
        self.stats_sets = 0
        self.stats_deletes = 0
        self.stats_evictions = 0

        # Limpeza automática
        self.cleanup_task: Optional[asyncio.Task] = None
        self.cleanup_interval = 60  # segundos

    async def initialize(self):
        """Inicializa o cache de memória."""
        # Iniciar tarefa de limpeza automática
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        print("Memory cache initialized")

    async def get(self, key: str) -> Optional[CacheEntry]:
        """Obtém item do cache."""
        with self.lock:
            # Verificar se chave existe
            if key not in self.metadata:
                self.stats_misses += 1
                return None

            # Verificar TTL
            if self._is_expired(key):
                self._remove_expired(key)
                self.stats_misses += 1
                return None

            # Obter valor do cache LRU
            value = self.cache.get(key)
            if value is None:
                self.stats_misses += 1
                return None

            # Atualizar metadados
            entry = self.metadata[key]
            entry.access_count += 1
            entry.last_accessed = datetime.now()

            self.stats_hits += 1
            return entry

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Define item no cache."""
        with self.lock:
            try:
                # Calcular expiração
                expires_at = None
                if ttl is not None:
                    expires_at = datetime.now() + timedelta(seconds=ttl)
                elif self.config.default_ttl > 0:
                    expires_at = datetime.now() + timedelta(
                        seconds=self.config.default_ttl
                    )

                # Criar entrada
                entry = CacheEntry(
                    key=key,
                    value=value,
                    created_at=datetime.now(),
                    expires_at=expires_at,
                    access_count=0,
                    last_accessed=datetime.now(),
                    size_bytes=self._calculate_size(value),
                    backend="memory",
                )

                # Verificar limite de memória
                if not self._check_memory_limit(entry):
                    # Tentar liberar espaço
                    self._evict_if_needed()
                    if not self._check_memory_limit(entry):
                        return False  # Não foi possível liberar espaço suficiente

                # Armazenar no cache LRU
                success = self.cache.set(key, value)
                if not success:
                    return False

                # Armazenar metadados
                self.metadata[key] = entry

                # Armazenar TTL se necessário
                if expires_at:
                    self.ttl_cache[key] = expires_at

                self.stats_sets += 1
                return True

            except Exception as e:
                print(f"Error setting memory cache key {key}: {e}")
                return False

    async def delete(self, key: str) -> bool:
        """Remove item do cache."""
        with self.lock:
            try:
                # Remover do cache LRU
                cache_success = self.cache.delete(key)

                # Remover metadados
                if key in self.metadata:
                    del self.metadata[key]

                # Remover TTL
                if key in self.ttl_cache:
                    del self.ttl_cache[key]

                if cache_success:
                    self.stats_deletes += 1

                return cache_success

            except Exception as e:
                print(f"Error deleting memory cache key {key}: {e}")
                return False

    async def clear(self) -> bool:
        """Limpa todo o cache."""
        with self.lock:
            try:
                self.cache.clear()
                self.metadata.clear()
                self.ttl_cache.clear()
                return True
            except Exception as e:
                print(f"Error clearing memory cache: {e}")
                return False

    async def exists(self, key: str) -> bool:
        """Verifica se chave existe."""
        with self.lock:
            if key not in self.metadata:
                return False

            if self._is_expired(key):
                self._remove_expired(key)
                return False

            return True

    async def keys(self, pattern: str = "*") -> List[str]:
        """Lista chaves que correspondem ao padrão."""
        with self.lock:
            try:
                all_keys = []

                for key in self.metadata.keys():
                    # Verificar expiração
                    if self._is_expired(key):
                        continue

                    # Aplicar padrão (implementação simples)
                    if pattern == "*" or pattern in key:
                        all_keys.append(key)

                return all_keys

            except Exception as e:
                print(f"Error listing memory cache keys: {e}")
                return []

    async def stats(self) -> Dict[str, Any]:
        """Obtém estatísticas do cache."""
        with self.lock:
            total_requests = self.stats_hits + self.stats_misses
            hit_rate = (self.stats_hits / total_requests) if total_requests > 0 else 0

            # Calcular uso de memória
            total_memory = sum(entry.size_bytes for entry in self.metadata.values())
            memory_usage_pct = (total_memory / self.config.max_memory_size) * 100

            return {
                "backend": "memory",
                "hits": self.stats_hits,
                "misses": self.stats_misses,
                "hit_rate": hit_rate,
                "sets": self.stats_sets,
                "deletes": self.stats_deletes,
                "evictions": self.stats_evictions,
                "total_entries": len(self.metadata),
                "max_entries": self.config.max_entries,
                "memory_usage_bytes": total_memory,
                "memory_usage_pct": memory_usage_pct,
                "max_memory_bytes": self.config.max_memory_size,
            }

    def _is_expired(self, key: str) -> bool:
        """Verifica se chave expirou."""
        if key not in self.ttl_cache:
            return False

        return datetime.now() > self.ttl_cache[key]

    def _remove_expired(self, key: str):
        """Remove chave expirada."""
        self.cache.delete(key)
        if key in self.metadata:
            del self.metadata[key]
        if key in self.ttl_cache:
            del self.ttl_cache[key]

    def _calculate_size(self, value: Any) -> int:
        """Calcula tamanho aproximado do valor."""
        try:
            import sys

            return sys.getsizeof(value)
        except Exception:
            return len(str(value))

    def _check_memory_limit(self, new_entry: CacheEntry) -> bool:
        """Verifica se nova entrada cabe no limite de memória."""
        current_memory = sum(entry.size_bytes for entry in self.metadata.values())
        return (current_memory + new_entry.size_bytes) <= self.config.max_memory_size

    def _evict_if_needed(self):
        """Remove entradas para liberar espaço."""
        # Implementar estratégia de remoção (LRU)
        while len(self.metadata) > 0:
            # Encontrar entrada menos recentemente usada
            oldest_key = None
            oldest_time = datetime.now()

            for key, entry in self.metadata.items():
                if entry.last_accessed and entry.last_accessed < oldest_time:
                    oldest_time = entry.last_accessed
                    oldest_key = key

            if oldest_key:
                self._remove_expired(oldest_key)
                self.stats_evictions += 1

                # Verificar se liberou espaço suficiente
                current_memory = sum(
                    entry.size_bytes for entry in self.metadata.values()
                )
                if current_memory < (
                    self.config.max_memory_size * 0.8
                ):  # 80% do limite
                    break
            else:
                break

    async def _cleanup_loop(self):
        """Loop de limpeza automática de itens expirados."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in cleanup loop: {e}")

    async def _cleanup_expired(self):
        """Remove todos os itens expirados."""
        with self.lock:
            expired_keys = []

            for key in list(self.ttl_cache.keys()):
                if self._is_expired(key):
                    expired_keys.append(key)

            for key in expired_keys:
                self._remove_expired(key)

            if expired_keys:
                print(f"Cleaned up {len(expired_keys)} expired cache entries")

    async def shutdown(self):
        """Finaliza o cache de memória."""
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass

        await self.clear()
        print("Memory cache shutdown complete")
