"""
Compat shim to expose cache API expected by tests.
Delegates to `api.cache` package exports.
"""

from api.cache import (
    CacheManager,
    MemoryCache,
    RedisCache,
    cache_manager,
    get_cache_stats,
    invalidate_cache_tags,
    clear_all_cache,
)

__all__ = [
    "CacheManager",
    "MemoryCache",
    "RedisCache",
    "cache_manager",
    "get_cache_stats",
    "invalidate_cache_tags",
    "clear_all_cache",
]

