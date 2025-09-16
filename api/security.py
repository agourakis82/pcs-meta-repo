"""
Darwin Platform Security

API key authentication and rate limiting implementation.
Provides secure access control with token bucket rate limiting.
"""

import logging
import time
from typing import Dict

from fastapi import HTTPException, Request
from fastapi.security import APIKeyHeader

from services.settings import get_settings

logger = logging.getLogger(__name__)

# API Key Security
api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)


class TokenBucket:
    """Token bucket for rate limiting."""

    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket.

        Args:
            capacity: Maximum tokens
            refill_rate: Tokens per second refill rate
        """
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.last_refill = time.time()

    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens.

        Args:
            tokens: Number of tokens to consume

        Returns:
            True if tokens consumed, False if insufficient
        """
        now = time.time()

        # Refill tokens based on time elapsed
        time_passed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + time_passed * self.refill_rate)
        self.last_refill = now

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False


class RateLimiter:
    """In-memory rate limiter using token buckets."""

    def __init__(self):
        self.settings = get_settings()
        self.buckets: Dict[str, TokenBucket] = {}
        self.cleanup_interval = 3600  # 1 hour
        self.last_cleanup = time.time()

    def _cleanup_old_buckets(self):
        """Remove old unused buckets."""
        now = time.time()
        if now - self.last_cleanup < self.cleanup_interval:
            return

        # Remove buckets older than 1 hour
        cutoff = now - 3600
        keys_to_remove = [
            key for key, bucket in self.buckets.items() if bucket.last_refill < cutoff
        ]

        for key in keys_to_remove:
            del self.buckets[key]

        self.last_cleanup = now
        logger.debug(f"Cleaned up {len(keys_to_remove)} old rate limit buckets")

    def _get_bucket_key(self, request: Request, route: str) -> str:
        """Generate bucket key for request."""
        client_ip = request.client.host if request.client else "unknown"
        return f"{client_ip}:{route}"

    def is_allowed(self, request: Request, route: str) -> bool:
        """
        Check if request is allowed by rate limits.

        Args:
            request: FastAPI request
            route: Route path

        Returns:
            True if allowed, False if rate limited
        """
        self._cleanup_old_buckets()

        bucket_key = self._get_bucket_key(request, route)

        if bucket_key not in self.buckets:
            # Create new bucket with per-minute rate (converted to per-second)
            refill_rate = self.settings.RATE_LIMIT_PER_MIN / 60.0
            self.buckets[bucket_key] = TokenBucket(
                capacity=self.settings.RATE_LIMIT_BURST, refill_rate=refill_rate
            )

        bucket = self.buckets[bucket_key]
        return bucket.consume(1)

    def get_bucket_status(self, request: Request, route: str) -> Dict[str, float]:
        """Get current bucket status for debugging."""
        bucket_key = self._get_bucket_key(request, route)
        if bucket_key in self.buckets:
            bucket = self.buckets[bucket_key]
            return {
                "tokens": bucket.tokens,
                "capacity": bucket.capacity,
                "refill_rate": bucket.refill_rate,
            }
        return {"tokens": 0, "capacity": 0, "refill_rate": 0}


# Global rate limiter instance
rate_limiter = RateLimiter()


async def require_api_key(api_key: str = api_key_header) -> str:
    """
    Validate API key.

    Args:
        api_key: API key from header

    Returns:
        Validated API key

    Raises:
        HTTPException: If API key is invalid
    """
    settings = get_settings()

    if not settings.API_KEY_REQUIRED:
        return "development"

    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if not settings.API_KEYS or api_key not in settings.API_KEYS:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return api_key


async def rate_limit(request: Request) -> None:
    """
    Rate limit middleware.

    Args:
        request: FastAPI request

    Raises:
        HTTPException: If rate limit exceeded
    """
    route_path = request.url.path

    # Skip rate limiting for health and version endpoints
    if route_path in ["/health", "/version"]:
        return

    if not rate_limiter.is_allowed(request, route_path):
        # Get bucket status for rate limit info
        bucket_status = rate_limiter.get_bucket_status(request, route_path)

        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={
                "Retry-After": "60",
                "X-RateLimit-Limit": str(get_settings().RATE_LIMIT_PER_MIN),
                "X-RateLimit-Remaining": str(int(bucket_status.get("tokens", 0))),
                "X-RateLimit-Reset": str(int(time.time() + 60)),
            },
        )


def get_rate_limiter() -> RateLimiter:
    """Get rate limiter instance."""
    return rate_limiter
