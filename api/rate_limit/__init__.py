"""
Advanced Rate Limiting System for PCS H3 Integration
Comprehensive rate limiting with multiple strategies and Redis backend
"""

from .advanced_limiter import (
    AdvancedRateLimiter,
    RateLimitMetrics,
    RateLimitResult,
    RateLimitRule,
    RateLimitScope,
    RateLimitStrategy,
    get_rate_limiter,
)
from .config import (
    RATE_LIMIT_TEMPLATES,
    RateLimitConfig,
    RateLimitConfigManager,
    create_config_from_template,
    load_config_from_env,
    save_example_configs,
)
from .middleware import (
    RateLimitMiddleware,
    add_rate_limiting,
    configure_advanced_rate_limiting,
    create_rate_limit_routes,
    get_rate_limit_metrics,
    rate_limit,
    reset_rate_limits,
    update_rate_limit_rules,
)

__all__ = [
    # Core classes
    "AdvancedRateLimiter",
    "RateLimitStrategy",
    "RateLimitScope",
    "RateLimitRule",
    "RateLimitResult",
    "RateLimitMetrics",
    # Middleware
    "RateLimitMiddleware",
    "add_rate_limiting",
    "rate_limit",
    # Configuration
    "RateLimitConfig",
    "RateLimitConfigManager",
    "RATE_LIMIT_TEMPLATES",
    # Utility functions
    "get_rate_limiter",
    "reset_rate_limits",
    "get_rate_limit_metrics",
    "update_rate_limit_rules",
    "create_rate_limit_routes",
    "configure_advanced_rate_limiting",
    "create_config_from_template",
    "load_config_from_env",
    "save_example_configs",
]

__version__ = "1.0.0"
__description__ = "Advanced rate limiting system for PCS H3 Integration"


# Backward-compat dependency used by some routers
async def rate_limit_dependency(request) -> None:
    return None


def get_rate_limit_status(request) -> dict:
    """Compat: return minimal rate limit status."""
    try:
        from ..config import settings  # type: ignore
    except Exception:

        class _S:
            pass

        settings = _S()
        settings.RATE_LIMIT_PER_MIN = 60
        settings.RATE_LIMIT_BURST = 10
    return {
        "identifier": "compat",
        "limit_per_minute": getattr(settings, "RATE_LIMIT_PER_MIN", 60),
        "burst_capacity": getattr(settings, "RATE_LIMIT_BURST", 10),
        "tokens_available": getattr(settings, "RATE_LIMIT_BURST", 10),
        "capacity": getattr(settings, "RATE_LIMIT_BURST", 10),
        "refill_rate_per_second": getattr(settings, "RATE_LIMIT_PER_MIN", 60) / 60.0,
        "utilization_percent": 0.0,
    }


__all__ += ["rate_limit_dependency", "get_rate_limit_status"]
