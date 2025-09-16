#!/usr/bin/env python3
"""
Cache Manager para RAG++ Server
Sistema de cache inteligente para melhorar performance de buscas.
"""

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import dataclass
from threading import Lock
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Entrada do cache com metadados."""

    key: str
    data: Any
    timestamp: float
    ttl: int  # Time to live in seconds
    hits: int = 0
    last_access: float = 0

    def is_expired(self) -> bool:
        """Verifica se a entrada expirou."""
        return time.time() - self.timestamp > self.ttl

    def access(self):
        """Registra acesso à entrada."""
        self.hits += 1
        self.last_access = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário."""
        return {
            "key": self.key,
            "data": self.data,
            "timestamp": self.timestamp,
            "ttl": self.ttl,
            "hits": self.hits,
            "last_access": self.last_access,
        }


class RAGCache:
    """Cache inteligente para sistema RAG++."""

    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        """
        Inicializa o cache.

        Args:
            max_size: Tamanho máximo do cache
            default_ttl: TTL padrão em segundos (1 hora)
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: Dict[str, CacheEntry] = {}
        self.lock = Lock()
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "size": 0,
        }

        logger.info(f"🗄️ Cache inicializado: max_size={max_size}, ttl={default_ttl}s")

    def _generate_key(self, query: str, search_type: str, max_results: int) -> str:
        """Gera chave única para a busca."""
        key_data = f"{query}|{search_type}|{max_results}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _evict_oldest(self):
        """Remove entrada mais antiga quando cache está cheio."""
        if not self.cache:
            return

        # Remove entrada com menor hits ou mais antiga
        oldest_key = min(
            self.cache.keys(),
            key=lambda k: (self.cache[k].hits, self.cache[k].last_access),
        )

        del self.cache[oldest_key]
        self.stats["evictions"] += 1
        self.stats["size"] = len(self.cache)

        logger.debug(f"🗑️ Cache eviction: {oldest_key}")

    def _cleanup_expired(self):
        """Remove entradas expiradas."""
        expired_keys = [key for key, entry in self.cache.items() if entry.is_expired()]

        for key in expired_keys:
            del self.cache[key]

        if expired_keys:
            self.stats["size"] = len(self.cache)
            logger.debug(f"🧹 Cleanup: {len(expired_keys)} entradas expiradas")

    def get(self, query: str, search_type: str, max_results: int) -> Optional[Any]:
        """
        Busca no cache.

        Returns:
            Dados cached ou None se não encontrado
        """
        key = self._generate_key(query, search_type, max_results)

        with self.lock:
            self._cleanup_expired()

            if key in self.cache:
                entry = self.cache[key]
                if not entry.is_expired():
                    entry.access()
                    self.stats["hits"] += 1
                    logger.debug(f"✅ Cache hit: {key}")
                    return entry.data
                else:
                    # Entrada expirada
                    del self.cache[key]
                    self.stats["size"] = len(self.cache)

            self.stats["misses"] += 1
            logger.debug(f"❌ Cache miss: {key}")
            return None

    def set(
        self,
        query: str,
        search_type: str,
        max_results: int,
        data: Any,
        ttl: Optional[int] = None,
    ):
        """
        Armazena no cache.

        Args:
            query: Query de busca
            search_type: Tipo de busca
            max_results: Máximo de resultados
            data: Dados a serem cached
            ttl: Time to live (usa default se None)
        """
        key = self._generate_key(query, search_type, max_results)
        ttl_value = ttl or self.default_ttl

        with self.lock:
            # Verifica se precisa fazer eviction
            if len(self.cache) >= self.max_size and key not in self.cache:
                self._evict_oldest()

            entry = CacheEntry(
                key=key,
                data=data,
                timestamp=time.time(),
                ttl=ttl_value,
                last_access=time.time(),
            )

            self.cache[key] = entry
            self.stats["size"] = len(self.cache)

            logger.debug(f"💾 Cache set: {key} (ttl={ttl_value}s)")

    def clear(self):
        """Limpa todo o cache."""
        with self.lock:
            self.cache.clear()
            self.stats["size"] = 0
            logger.info("🧹 Cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache."""
        with self.lock:
            self._cleanup_expired()

            total_requests = self.stats["hits"] + self.stats["misses"]
            hit_rate = (
                (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0
            )

            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "hits": self.stats["hits"],
                "misses": self.stats["misses"],
                "evictions": self.stats["evictions"],
                "hit_rate": round(hit_rate, 2),
                "entries": [
                    {
                        "key": entry.key[:8] + "...",  # Apenas primeiros 8 chars
                        "hits": entry.hits,
                        "age": round(time.time() - entry.timestamp, 1),
                        "ttl": entry.ttl,
                    }
                    for entry in self.cache.values()
                ],
            }


# Instância global do cache
_cache_instance: Optional[RAGCache] = None


def get_cache() -> RAGCache:
    """Retorna instância global do cache."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = RAGCache()
    return _cache_instance


def init_cache(max_size: int = 1000, default_ttl: int = 3600) -> RAGCache:
    """Inicializa cache global."""
    global _cache_instance
    _cache_instance = RAGCache(max_size=max_size, default_ttl=default_ttl)
    return _cache_instance


# Cache decorator para funções
def cached(ttl: Optional[int] = None):
    """Decorator para cache de funções."""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Gera chave baseada nos argumentos
            key_data = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            cache_key = hashlib.md5(key_data.encode()).hexdigest()

            cache = get_cache()

            # Tenta buscar do cache
            cached_result = cache.get(cache_key, "function", 1)
            if cached_result is not None:
                return cached_result

            # Executa função
            result = await func(*args, **kwargs)

            # Armazena no cache
            cache.set(cache_key, "function", 1, result, ttl)

            return result

        return wrapper

    return decorator
