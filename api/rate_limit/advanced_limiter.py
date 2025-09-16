"""
Advanced Rate Limiting System for PCS H3 Integration
Implements multiple rate limiting strategies with Redis backend
"""

import asyncio
import hashlib
import json
import logging
import time
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

# Redis imports with fallback
try:
    import redis.asyncio as redis
    from redis.exceptions import RedisError

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

    class MockRedis:
        async def get(self, key):
            return None

        async def set(self, key, value, ex=None):
            return True

        async def incr(self, key):
            return 1

        async def expire(self, key, seconds):
            return True

        async def delete(self, *keys):
            return 1

        async def pipeline(self):
            return self

        async def execute(self):
            return []

        def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass


logger = logging.getLogger(__name__)


class RateLimitStrategy(Enum):
    """Rate limiting strategies"""

    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"


class RateLimitScope(Enum):
    """Rate limiting scopes"""

    GLOBAL = "global"
    IP = "ip"
    USER = "user"
    ENDPOINT = "endpoint"
    USER_ENDPOINT = "user_endpoint"
    IP_ENDPOINT = "ip_endpoint"


@dataclass
class RateLimitRule:
    """Rate limit rule configuration"""

    scope: RateLimitScope
    strategy: RateLimitStrategy
    limit: int
    window: int  # seconds
    burst: Optional[int] = None  # for token bucket
    leak_rate: Optional[float] = None  # for leaky bucket
    enabled: bool = True
    priority: int = 0  # higher priority rules are checked first


@dataclass
class RateLimitResult:
    """Result of rate limit check"""

    allowed: bool
    limit: int
    remaining: int
    reset_time: int
    retry_after: Optional[int] = None
    rule_matched: Optional[str] = None
    scope: Optional[str] = None


@dataclass
class RateLimitMetrics:
    """Rate limiting metrics"""

    total_requests: int
    blocked_requests: int
    requests_by_scope: Dict[str, int]
    requests_by_strategy: Dict[str, int]
    top_blocked_ips: List[Tuple[str, int]]
    top_blocked_users: List[Tuple[str, int]]


class AdvancedRateLimiter:
    """Advanced rate limiter with multiple strategies and Redis backend"""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        key_prefix: str = "pcs_h3_rate_limit",
    ):
        self.redis_url = redis_url
        self.key_prefix = key_prefix
        self.redis_client: Optional[redis.Redis] = None
        self.rules: Dict[str, RateLimitRule] = {}
        self.metrics_enabled = True
        self._lock = asyncio.Lock()

    async def initialize(self):
        """Initialize Redis connection"""
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    max_connections=20,
                )
                # Test connection
                await self.redis_client.ping()
                logger.info("Rate limiter Redis connection established")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}. Using fallback.")
                self.redis_client = MockRedis()
        else:
            logger.warning("Redis not available. Using fallback rate limiter.")
            self.redis_client = MockRedis()

    async def close(self):
        """Close Redis connection"""
        if self.redis_client and hasattr(self.redis_client, "close"):
            await self.redis_client.close()

    def add_rule(self, name: str, rule: RateLimitRule):
        """Add a rate limiting rule"""
        self.rules[name] = rule
        logger.info(
            f"Added rate limit rule: {name} - {rule.scope.value} "
            f"{rule.limit}/{rule.window}s using {rule.strategy.value}"
        )

    def remove_rule(self, name: str):
        """Remove a rate limiting rule"""
        if name in self.rules:
            del self.rules[name]
            logger.info(f"Removed rate limit rule: {name}")

    def configure_default_rules(self):
        """Configure default rate limiting rules"""
        default_rules = [
            (
                "global_burst",
                RateLimitRule(
                    scope=RateLimitScope.GLOBAL,
                    strategy=RateLimitStrategy.SLIDING_WINDOW,
                    limit=10000,
                    window=60,
                    priority=10,
                ),
            ),
            (
                "ip_moderate",
                RateLimitRule(
                    scope=RateLimitScope.IP,
                    strategy=RateLimitStrategy.SLIDING_WINDOW,
                    limit=1000,
                    window=60,
                    priority=20,
                ),
            ),
            (
                "user_standard",
                RateLimitRule(
                    scope=RateLimitScope.USER,
                    strategy=RateLimitStrategy.TOKEN_BUCKET,
                    limit=500,
                    window=60,
                    burst=100,
                    priority=30,
                ),
            ),
            (
                "endpoint_protection",
                RateLimitRule(
                    scope=RateLimitScope.ENDPOINT,
                    strategy=RateLimitStrategy.FIXED_WINDOW,
                    limit=100,
                    window=60,
                    priority=25,
                ),
            ),
            (
                "user_endpoint_strict",
                RateLimitRule(
                    scope=RateLimitScope.USER_ENDPOINT,
                    strategy=RateLimitStrategy.LEAKY_BUCKET,
                    limit=50,
                    window=60,
                    leak_rate=1.0,
                    priority=40,
                ),
            ),
        ]

        for name, rule in default_rules:
            self.add_rule(name, rule)

    def _generate_key(
        self,
        scope: RateLimitScope,
        identifier: str,
        endpoint: Optional[str] = None,
        window_start: Optional[int] = None,
    ) -> str:
        """Generate Redis key for rate limiting"""
        parts = [self.key_prefix, scope.value]

        if scope in [RateLimitScope.IP, RateLimitScope.USER]:
            parts.append(identifier)
        elif scope == RateLimitScope.ENDPOINT and endpoint:
            parts.append(hashlib.md5(endpoint.encode()).hexdigest()[:8])
        elif scope == RateLimitScope.USER_ENDPOINT and endpoint:
            parts.extend([identifier, hashlib.md5(endpoint.encode()).hexdigest()[:8]])
        elif scope == RateLimitScope.IP_ENDPOINT and endpoint:
            parts.extend([identifier, hashlib.md5(endpoint.encode()).hexdigest()[:8]])
        elif scope == RateLimitScope.GLOBAL:
            parts.append("global")

        if window_start:
            parts.append(str(window_start))

        return ":".join(parts)

    async def _check_fixed_window(
        self, key: str, limit: int, window: int
    ) -> RateLimitResult:
        """Fixed window rate limiting"""
        current_time = int(time.time())
        window_start = (current_time // window) * window
        window_key = f"{key}:{window_start}"

        async with self.redis_client.pipeline() as pipe:
            current_count = await self.redis_client.get(window_key)
            current_count = int(current_count) if current_count else 0

            if current_count >= limit:
                reset_time = window_start + window
                return RateLimitResult(
                    allowed=False,
                    limit=limit,
                    remaining=0,
                    reset_time=reset_time,
                    retry_after=reset_time - current_time,
                )

            # Increment counter
            pipe.incr(window_key)
            pipe.expire(window_key, window + 1)
            await pipe.execute()

            return RateLimitResult(
                allowed=True,
                limit=limit,
                remaining=limit - current_count - 1,
                reset_time=window_start + window,
            )

    async def _check_sliding_window(
        self, key: str, limit: int, window: int
    ) -> RateLimitResult:
        """Sliding window rate limiting using sorted sets"""
        current_time = time.time()
        window_start = current_time - window

        # Clean old entries and count current
        async with self.redis_client.pipeline() as pipe:
            # Remove expired entries
            pipe.zremrangebyscore(key, 0, window_start)
            # Count current entries
            pipe.zcard(key)
            # Add current request
            pipe.zadd(key, {str(current_time): current_time})
            # Set expiration
            pipe.expire(key, window + 1)

            results = await pipe.execute()
            current_count = results[1] if len(results) > 1 else 0

            if current_count >= limit:
                return RateLimitResult(
                    allowed=False,
                    limit=limit,
                    remaining=0,
                    reset_time=int(current_time + window),
                    retry_after=1,
                )

            return RateLimitResult(
                allowed=True,
                limit=limit,
                remaining=limit - current_count - 1,
                reset_time=int(current_time + window),
            )

    async def _check_token_bucket(
        self, key: str, limit: int, window: int, burst: Optional[int] = None
    ) -> RateLimitResult:
        """Token bucket rate limiting"""
        burst = burst or limit
        current_time = time.time()

        # Get current bucket state
        bucket_data = await self.redis_client.get(key)
        if bucket_data:
            bucket_info = json.loads(bucket_data)
            tokens = bucket_info.get("tokens", burst)
            last_refill = bucket_info.get("last_refill", current_time)
        else:
            tokens = burst
            last_refill = current_time

        # Calculate tokens to add based on time passed
        time_passed = current_time - last_refill
        tokens_to_add = (time_passed / window) * limit
        tokens = min(burst, tokens + tokens_to_add)

        if tokens < 1:
            # Calculate when next token will be available
            retry_after = (1 - tokens) * (window / limit)
            return RateLimitResult(
                allowed=False,
                limit=limit,
                remaining=0,
                reset_time=int(current_time + retry_after),
                retry_after=int(retry_after) + 1,
            )

        # Consume one token
        tokens -= 1

        # Update bucket state
        bucket_info = {"tokens": tokens, "last_refill": current_time}
        await self.redis_client.set(key, json.dumps(bucket_info), ex=window * 2)

        return RateLimitResult(
            allowed=True,
            limit=limit,
            remaining=int(tokens),
            reset_time=int(current_time + window),
        )

    async def _check_leaky_bucket(
        self, key: str, limit: int, window: int, leak_rate: float = 1.0
    ) -> RateLimitResult:
        """Leaky bucket rate limiting"""
        current_time = time.time()

        # Get current bucket state
        bucket_data = await self.redis_client.get(key)
        if bucket_data:
            bucket_info = json.loads(bucket_data)
            level = bucket_info.get("level", 0)
            last_leak = bucket_info.get("last_leak", current_time)
        else:
            level = 0
            last_leak = current_time

        # Calculate leakage
        time_passed = current_time - last_leak
        leaked = time_passed * leak_rate
        level = max(0, level - leaked)

        if level >= limit:
            return RateLimitResult(
                allowed=False,
                limit=limit,
                remaining=0,
                reset_time=int(current_time + (level - limit + 1) / leak_rate),
                retry_after=int((level - limit + 1) / leak_rate) + 1,
            )

        # Add request to bucket
        level += 1

        # Update bucket state
        bucket_info = {"level": level, "last_leak": current_time}
        await self.redis_client.set(key, json.dumps(bucket_info), ex=window * 2)

        return RateLimitResult(
            allowed=True,
            limit=limit,
            remaining=limit - int(level),
            reset_time=int(current_time + window),
        )

    async def check_rate_limit(
        self, ip: str, user_id: Optional[str] = None, endpoint: Optional[str] = None
    ) -> RateLimitResult:
        """Check rate limits for a request"""
        if not self.redis_client:
            await self.initialize()

        # Sort rules by priority (highest first)
        sorted_rules = sorted(
            self.rules.items(), key=lambda x: x[1].priority, reverse=True
        )

        for rule_name, rule in sorted_rules:
            if not rule.enabled:
                continue

            # Determine identifier based on scope
            identifier = None
            if rule.scope in [RateLimitScope.IP, RateLimitScope.IP_ENDPOINT]:
                identifier = ip
            elif rule.scope in [RateLimitScope.USER, RateLimitScope.USER_ENDPOINT]:
                if not user_id:
                    continue  # Skip user-based rules if no user
                identifier = user_id
            elif rule.scope == RateLimitScope.GLOBAL:
                identifier = "global"
            elif rule.scope == RateLimitScope.ENDPOINT:
                if not endpoint:
                    continue
                identifier = endpoint

            if identifier is None:
                continue

            # Generate key
            key = self._generate_key(rule.scope, identifier, endpoint)

            # Check rate limit based on strategy
            try:
                if rule.strategy == RateLimitStrategy.FIXED_WINDOW:
                    result = await self._check_fixed_window(
                        key, rule.limit, rule.window
                    )
                elif rule.strategy == RateLimitStrategy.SLIDING_WINDOW:
                    result = await self._check_sliding_window(
                        key, rule.limit, rule.window
                    )
                elif rule.strategy == RateLimitStrategy.TOKEN_BUCKET:
                    result = await self._check_token_bucket(
                        key, rule.limit, rule.window, rule.burst
                    )
                elif rule.strategy == RateLimitStrategy.LEAKY_BUCKET:
                    result = await self._check_leaky_bucket(
                        key, rule.limit, rule.window, rule.leak_rate or 1.0
                    )
                else:
                    continue

                # If rate limit exceeded, return immediately
                if not result.allowed:
                    result.rule_matched = rule_name
                    result.scope = rule.scope.value

                    # Record metrics
                    if self.metrics_enabled:
                        await self._record_blocked_request(rule.scope, identifier)

                    return result

            except Exception as e:
                logger.error(f"Error checking rate limit for rule {rule_name}: {e}")
                continue

        # If no rate limits exceeded, record successful request
        if self.metrics_enabled:
            await self._record_successful_request()

        # Return default allowed result
        return RateLimitResult(
            allowed=True, limit=float("inf"), remaining=float("inf"), reset_time=0
        )

    async def _record_blocked_request(self, scope: RateLimitScope, identifier: str):
        """Record blocked request for metrics"""
        try:
            metrics_key = f"{self.key_prefix}:metrics"
            current_time = int(time.time())
            day_key = f"{metrics_key}:day:{current_time // 86400}"

            async with self.redis_client.pipeline() as pipe:
                # Increment counters
                pipe.hincrby(day_key, "blocked_requests", 1)
                pipe.hincrby(day_key, f"blocked_by_scope:{scope.value}", 1)

                if scope in [RateLimitScope.IP, RateLimitScope.IP_ENDPOINT]:
                    pipe.zincrby(f"{day_key}:blocked_ips", 1, identifier)
                elif scope in [RateLimitScope.USER, RateLimitScope.USER_ENDPOINT]:
                    pipe.zincrby(f"{day_key}:blocked_users", 1, identifier)

                # Set expiration
                pipe.expire(day_key, 86400 * 7)  # Keep for 7 days
                pipe.expire(f"{day_key}:blocked_ips", 86400 * 7)
                pipe.expire(f"{day_key}:blocked_users", 86400 * 7)

                await pipe.execute()
        except Exception as e:
            logger.error(f"Error recording blocked request metrics: {e}")

    async def _record_successful_request(self):
        """Record successful request for metrics"""
        try:
            metrics_key = f"{self.key_prefix}:metrics"
            current_time = int(time.time())
            day_key = f"{metrics_key}:day:{current_time // 86400}"

            await self.redis_client.hincrby(day_key, "total_requests", 1)
            await self.redis_client.expire(day_key, 86400 * 7)
        except Exception as e:
            logger.error(f"Error recording successful request metrics: {e}")

    async def get_metrics(self, days: int = 1) -> RateLimitMetrics:
        """Get rate limiting metrics"""
        try:
            current_time = int(time.time())
            total_requests = 0
            blocked_requests = 0
            requests_by_scope = {}
            requests_by_strategy = {}
            blocked_ips = {}
            blocked_users = {}

            for day_offset in range(days):
                day = (current_time // 86400) - day_offset
                day_key = f"{self.key_prefix}:metrics:day:{day}"

                # Get day metrics
                day_metrics = await self.redis_client.hgetall(day_key)
                if not day_metrics:
                    continue

                total_requests += int(day_metrics.get("total_requests", 0))
                blocked_requests += int(day_metrics.get("blocked_requests", 0))

                # Aggregate scope metrics
                for key, value in day_metrics.items():
                    if key.startswith("blocked_by_scope:"):
                        scope = key.replace("blocked_by_scope:", "")
                        requests_by_scope[scope] = requests_by_scope.get(
                            scope, 0
                        ) + int(value)

                # Get top blocked IPs and users
                day_blocked_ips = await self.redis_client.zrevrange(
                    f"{day_key}:blocked_ips", 0, 9, withscores=True
                )
                day_blocked_users = await self.redis_client.zrevrange(
                    f"{day_key}:blocked_users", 0, 9, withscores=True
                )

                for ip, count in day_blocked_ips:
                    blocked_ips[ip] = blocked_ips.get(ip, 0) + int(count)

                for user, count in day_blocked_users:
                    blocked_users[user] = blocked_users.get(user, 0) + int(count)

            # Convert to top lists
            top_blocked_ips = sorted(
                blocked_ips.items(), key=lambda x: x[1], reverse=True
            )[:10]
            top_blocked_users = sorted(
                blocked_users.items(), key=lambda x: x[1], reverse=True
            )[:10]

            return RateLimitMetrics(
                total_requests=total_requests,
                blocked_requests=blocked_requests,
                requests_by_scope=requests_by_scope,
                requests_by_strategy=requests_by_strategy,
                top_blocked_ips=top_blocked_ips,
                top_blocked_users=top_blocked_users,
            )

        except Exception as e:
            logger.error(f"Error getting rate limiting metrics: {e}")
            return RateLimitMetrics(
                total_requests=0,
                blocked_requests=0,
                requests_by_scope={},
                requests_by_strategy={},
                top_blocked_ips=[],
                top_blocked_users=[],
            )

    async def reset_user_limits(self, user_id: str):
        """Reset rate limits for a specific user"""
        try:
            pattern = f"{self.key_prefix}:user:{user_id}*"
            keys = await self.redis_client.keys(pattern)
            if keys:
                await self.redis_client.delete(*keys)
                logger.info(f"Reset rate limits for user: {user_id}")
        except Exception as e:
            logger.error(f"Error resetting user limits: {e}")

    async def reset_ip_limits(self, ip: str):
        """Reset rate limits for a specific IP"""
        try:
            pattern = f"{self.key_prefix}:ip:{ip}*"
            keys = await self.redis_client.keys(pattern)
            if keys:
                await self.redis_client.delete(*keys)
                logger.info(f"Reset rate limits for IP: {ip}")
        except Exception as e:
            logger.error(f"Error resetting IP limits: {e}")

    @asynccontextmanager
    async def get_client(self):
        """Context manager for Redis client"""
        if not self.redis_client:
            await self.initialize()
        try:
            yield self.redis_client
        finally:
            pass  # Keep connection alive for reuse


# Global rate limiter instance
rate_limiter = AdvancedRateLimiter()


async def get_rate_limiter() -> AdvancedRateLimiter:
    """Get configured rate limiter instance"""
    if not rate_limiter.redis_client:
        await rate_limiter.initialize()
        rate_limiter.configure_default_rules()
    return rate_limiter
