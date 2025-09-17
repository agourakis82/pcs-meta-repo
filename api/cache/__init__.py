"""
Sistema H2 - Cache e Performance

Módulo de inicialização do sistema de cache multi-camadas.
"""

from .manager import CacheManager, get_cache_manager
from .memory_cache import MemoryCache
from .metrics import CacheMetrics, get_cache_metrics
from .redis_cache import RedisCache
from .strategies import (
    InvalidationStrategy,
    LFUStrategy,
    LRUStrategy,
    TagStrategy,
    TTLStrategy,
    get_invalidation_manager,
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
    "get_invalidation_manager",
]

# Compat exports from cache_core (legacy API used by routers)
try:
    from .cache_core import (
        cache_manager,
        clear_all_cache,
        get_cache_stats,
        invalidate_cache_tags,
    )
    __all__ += [
        "cache_manager",
        "get_cache_stats",
        "invalidate_cache_tags",
        "clear_all_cache",
    ]
except Exception:
    # Allow package to load even if optional compat layer fails
    # For test compatibility: alias get_cache_stats to get_cache_metrics if missing
    def get_cache_stats(*args, **kwargs):
        """Compat: Alias para get_cache_metrics (usado em testes antigos)."""
        return get_cache_metrics(*args, **kwargs)
