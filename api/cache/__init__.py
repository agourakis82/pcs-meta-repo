"""
Sistema H2 - Cache e Performance

Módulo de inicialização do sistema de cache multi-camadas.
"""

from .manager import CacheManager, get_cache_manager
from .redis_cache import RedisCache
from .memory_cache import MemoryCache
from .metrics import CacheMetrics, get_cache_metrics
from .strategies import (
    InvalidationStrategy,
    TTLStrategy,
    LRUStrategy,
    LFUStrategy,
    TagStrategy,
    get_invalidation_manager
)

__all__ = [
    "CacheManager",
    "get_cache_manager",
    "RedisCache", 
    "MemoryCache",
    "CacheMetrics",
    "get_cache_metrics",
    "InvalidationStrategy",
    "TTLStrategy",
    "LRUStrategy",
    "LFUStrategy",
    "TagStrategy",
    "get_invalidation_manager"
]