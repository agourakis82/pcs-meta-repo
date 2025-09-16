"""
Rate limiting system for PCS-HELIO MCP API.

This module provides rate limiting with support for:
- Token bucket algorithm for smooth rate limiting
- Per-API-key and per-IP rate limiting
- Configurable rates from settings
- FastAPI middleware integration
- Decorators for endpoint-specific limits
- Burst capacity with gradual recovery
"""

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from functools import wraps
from typing import Callable, Dict, Optional, Tuple

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from .auth import extract_api_key, get_current_api_key
from .config import settings

# Configure module logger
logger = logging.getLogger(__name__)


class RateLimitExceeded(HTTPException):
    """Rate limit exceeded error."""

    def __init__(
        self, detail: str = "Rate limit exceeded", retry_after: Optional[int] = None
    ):
        headers = {}
        if retry_after:
            headers["Retry-After"] = str(retry_after)

        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            headers=headers,
        )


@dataclass
class TokenBucket:
    """
    Token bucket for rate limiting.

    Implements the token bucket algorithm where:
    - Tokens are added at a constant rate (refill_rate)
    - Requests consume tokens
    - Burst capacity allows temporary higher rates
    """

    capacity: int  # Maximum tokens (burst capacity)
    tokens: float  # Current tokens available
    refill_rate: float  # Tokens per second
    last_refill: float = field(default_factory=time.time)

    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from the bucket.

        Args:
            tokens: Number of tokens to consume

        Returns:
            True if tokens were consumed, False if rate limited
        """
        now = time.time()

        # Refill tokens based on time elapsed
        time_elapsed = now - self.last_refill
        self.tokens = min(
            self.capacity, self.tokens + (time_elapsed * self.refill_rate)
        )
        self.last_refill = now

        # Try to consume tokens
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True

        return False

    def time_to_refill(self, tokens: int = 1) -> float:
        """
        Calculate time until enough tokens are available.

        Args:
            tokens: Number of tokens needed

        Returns:
            Seconds until tokens are available
        """
        if self.tokens >= tokens:
            return 0.0

        tokens_needed = tokens - self.tokens
        return tokens_needed / self.refill_rate


class RateLimiter:
    """
    Rate limiter with per-identifier token buckets.

    Manages multiple token buckets for different identifiers
    (API keys, IP addresses, etc.)
    """

    def __init__(
        self,
        requests_per_minute: int = 60,
        burst_capacity: int = 10,
        cleanup_interval: int = 3600,  # 1 hour
    ):
        self.requests_per_minute = requests_per_minute
        self.burst_capacity = burst_capacity
        self.cleanup_interval = cleanup_interval

        # Tokens per second = requests_per_minute / 60
        self.refill_rate = requests_per_minute / 60.0

        # Storage for token buckets per identifier
        self.buckets: Dict[str, TokenBucket] = {}
        self.last_cleanup = time.time()

        logger.info(
            "Rate limiter initialized",
            extra={
                "requests_per_minute": requests_per_minute,
                "burst_capacity": burst_capacity,
                "refill_rate": self.refill_rate,
            },
        )

    def _get_bucket(self, identifier: str) -> TokenBucket:
        """Get or create token bucket for identifier."""
        if identifier not in self.buckets:
            self.buckets[identifier] = TokenBucket(
                capacity=self.burst_capacity,
                tokens=self.burst_capacity,  # Start with full capacity
                refill_rate=self.refill_rate,
            )

        return self.buckets[identifier]

    def _cleanup_old_buckets(self) -> None:
        """Remove unused token buckets to prevent memory leaks."""
        now = time.time()

        if now - self.last_cleanup < self.cleanup_interval:
            return

        # Remove buckets that haven't been used in the cleanup interval
        to_remove = []
        for identifier, bucket in self.buckets.items():
            if now - bucket.last_refill > self.cleanup_interval:
                to_remove.append(identifier)

        for identifier in to_remove:
            del self.buckets[identifier]

        self.last_cleanup = now

        if to_remove:
            logger.debug(
                "Cleaned up old rate limit buckets",
                extra={
                    "removed_count": len(to_remove),
                    "remaining_count": len(self.buckets),
                },
            )

    def is_allowed(
        self, identifier: str, tokens: int = 1
    ) -> Tuple[bool, Optional[float]]:
        """
        Check if request is allowed for identifier.

        Args:
            identifier: Unique identifier (API key, IP, etc.)
            tokens: Number of tokens to consume

        Returns:
            Tuple of (allowed, retry_after_seconds)
        """
        self._cleanup_old_buckets()

        bucket = self._get_bucket(identifier)

        if bucket.consume(tokens):
            logger.debug(
                "Rate limit check passed",
                extra={
                    "identifier": identifier,
                    "tokens_consumed": tokens,
                    "tokens_remaining": bucket.tokens,
                },
            )
            return True, None

        retry_after = bucket.time_to_refill(tokens)

        logger.warning(
            "Rate limit exceeded",
            extra={
                "identifier": identifier,
                "tokens_requested": tokens,
                "tokens_available": bucket.tokens,
                "retry_after": retry_after,
            },
        )

        return False, retry_after

    def get_status(self, identifier: str) -> Dict[str, float]:
        """Get current rate limit status for identifier."""
        bucket = self._get_bucket(identifier)

        # Trigger refill calculation
        bucket.consume(0)

        return {
            "tokens_available": bucket.tokens,
            "capacity": bucket.capacity,
            "refill_rate": bucket.refill_rate,
            "utilization": (bucket.capacity - bucket.tokens) / bucket.capacity,
        }


def get_rate_limit_identifier(request: Request) -> str:
    """
    Get rate limit identifier from request.

    Priority:
    1. API key (if authenticated)
    2. Client IP address

    Args:
        request: FastAPI request object

    Returns:
        Unique identifier for rate limiting
    """
    # Try to get API key first
    api_key = extract_api_key(request)
    if api_key:
        return f"api_key:{api_key}"

    # Fall back to IP address
    client_ip = "unknown"
    if request.client:
        client_ip = request.client.host

    # Check for forwarded headers (proxy support)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        client_ip = real_ip.strip()

    return f"ip:{client_ip}"


# Global rate limiter instance
_global_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get or create global rate limiter instance."""
    global _global_limiter

    if _global_limiter is None:
        _global_limiter = RateLimiter(
            requests_per_minute=settings.RATE_LIMIT_PER_MIN,
            burst_capacity=settings.RATE_LIMIT_BURST,
        )

    return _global_limiter


def check_rate_limit(request: Request, tokens: int = 1) -> None:
    """
    Check rate limit for request.

    Args:
        request: FastAPI request object
        tokens: Number of tokens to consume

    Raises:
        RateLimitExceeded: If rate limit is exceeded
    """
    limiter = get_rate_limiter()
    identifier = get_rate_limit_identifier(request)

    allowed, retry_after = limiter.is_allowed(identifier, tokens)

    if not allowed:
        raise RateLimitExceeded(
            detail=f"Rate limit exceeded for {identifier.split(':', 1)[0]}",
            retry_after=int(retry_after) if retry_after else None,
        )


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware for automatic rate limiting.

    Applies rate limiting to all requests unless exempted.
    """

    def __init__(
        self, app, exempt_paths: Optional[list[str]] = None, tokens_per_request: int = 1
    ):
        super().__init__(app)
        self.exempt_paths = exempt_paths or [
            "/",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
        ]
        self.tokens_per_request = tokens_per_request

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and apply rate limiting.

        Args:
            request: Incoming request
            call_next: Next middleware/endpoint

        Returns:
            Response from next middleware/endpoint
        """
        # Skip rate limiting for exempt paths
        if request.url.path in self.exempt_paths:
            return await call_next(request)

        try:
            # Check rate limit
            check_rate_limit(request, self.tokens_per_request)

        except RateLimitExceeded as e:
            # Return rate limit error
            return Response(
                content=f'{{"detail": "{e.detail}"}}',
                status_code=e.status_code,
                headers=e.headers,
                media_type="application/json",
            )

        # Continue to next middleware/endpoint
        response = await call_next(request)

        # Add rate limit headers to response
        identifier = get_rate_limit_identifier(request)
        limiter = get_rate_limiter()
        status = limiter.get_status(identifier)

        response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_PER_MIN)
        response.headers["X-RateLimit-Remaining"] = str(int(status["tokens_available"]))
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + 60))

        return response


def rate_limit(tokens: int = 1):
    """
    Decorator for endpoint-specific rate limiting.

    Args:
        tokens: Number of tokens to consume for this endpoint

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find request object
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if "request" in kwargs:
                request = kwargs["request"]

            if not request:
                raise ValueError("Request object not found in endpoint arguments")

            # Check rate limit
            check_rate_limit(request, tokens)

            # Call original function
            return await func(*args, **kwargs)

        return wrapper

    return decorator


def get_rate_limit_status(request: Request) -> Dict[str, any]:
    """
    Get current rate limit status for request.

    Args:
        request: FastAPI request object

    Returns:
        Dictionary with rate limit status information
    """
    limiter = get_rate_limiter()
    identifier = get_rate_limit_identifier(request)
    status = limiter.get_status(identifier)

    return {
        "identifier": identifier,
        "limit_per_minute": settings.RATE_LIMIT_PER_MIN,
        "burst_capacity": settings.RATE_LIMIT_BURST,
        "tokens_available": status["tokens_available"],
        "capacity": status["capacity"],
        "refill_rate_per_second": status["refill_rate"],
        "utilization_percent": status["utilization"] * 100,
    }


# Backward compatibility function
async def rate_limit_dependency(request: Request) -> None:
    """
    FastAPI dependency for rate limiting (backward compatibility).

    This function maintains compatibility with existing router code.
    In the new architecture, rate limiting is handled by middleware.
    """
    # Rate limiting is now handled by middleware, so this is a no-op
    # but we keep it for backward compatibility
    pass
