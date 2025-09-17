"""
FastAPI Middleware for Advanced Rate Limiting
Integrates the advanced rate limiter with FastAPI applications
"""
import asyncio
import logging
import time
from typing import Callable, Optional

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse

from .advanced_limiter import RateLimitResult, get_rate_limiter

logger = logging.getLogger(__name__)


class RateLimitMiddleware:
    """FastAPI middleware for rate limiting"""
    
    def __init__(self, app: FastAPI, 
                 exclude_paths: Optional[list] = None,
                 header_prefix: str = "X-RateLimit"):
        self.app = app
        self.exclude_paths = exclude_paths or ["/health", "/docs", "/redoc", "/openapi.json"]
        self.header_prefix = header_prefix
        
    async def __call__(self, request: Request, call_next: Callable):
        """Process request through rate limiting"""
        
        # Skip rate limiting for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        
        # Extract client information
        client_ip = self._get_client_ip(request)
        user_id = self._get_user_id(request)
        endpoint = f"{request.method} {request.url.path}"
        
        try:
            # Get rate limiter and check limits
            limiter = await get_rate_limiter()
            result = await limiter.check_rate_limit(
                ip=client_ip,
                user_id=user_id,
                endpoint=endpoint
            )
            
            # If rate limited, return 429 response
            if not result.allowed:
                return self._create_rate_limit_response(result)
            
            # Process request
            response = await call_next(request)
            
            # Add rate limit headers
            self._add_rate_limit_headers(response, result)
            
            return response
            
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # On error, allow request to proceed
            return await call_next(request)
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        # Check X-Forwarded-For header (for proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        # Check X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fall back to client host
        return request.client.host if request.client else "unknown"
    
    def _get_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from request"""
        # Try to get user from request state (set by auth middleware)
        if hasattr(request.state, 'user') and request.state.user:
            user = request.state.user
            if hasattr(user, 'id'):
                return str(user.id)
            elif hasattr(user, 'user_id'):
                return str(user.user_id)
            elif isinstance(user, dict):
                return str(user.get('id') or user.get('user_id'))
        
        # Try to get from Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            # This would require JWT decoding - simplified for now
            return None
        
        return None
    
    def _create_rate_limit_response(self, result: RateLimitResult) -> JSONResponse:
        """Create rate limit exceeded response"""
        headers = {
            f"{self.header_prefix}-Limit": str(result.limit),
            f"{self.header_prefix}-Remaining": str(result.remaining),
            f"{self.header_prefix}-Reset": str(result.reset_time),
        }
        
        if result.retry_after:
            headers["Retry-After"] = str(result.retry_after)
        
        content = {
            "error": "Rate limit exceeded",
            "message": f"Too many requests. Limit: {result.limit}, "
                      f"Remaining: {result.remaining}",
            "retry_after": result.retry_after,
            "reset_time": result.reset_time
        }
        
        if result.rule_matched:
            content["rule"] = result.rule_matched
        
        if result.scope:
            content["scope"] = result.scope
        
        return JSONResponse(
            status_code=429,
            content=content,
            headers=headers
        )
    
    def _add_rate_limit_headers(self, response: Response, result: RateLimitResult):
        """Add rate limit headers to successful response"""
        if hasattr(result, 'limit') and result.limit != float('inf'):
            response.headers[f"{self.header_prefix}-Limit"] = str(result.limit)
            response.headers[f"{self.header_prefix}-Remaining"] = str(result.remaining)
            response.headers[f"{self.header_prefix}-Reset"] = str(result.reset_time)


def add_rate_limiting(app: FastAPI, 
                     exclude_paths: Optional[list] = None,
                     header_prefix: str = "X-RateLimit"):
    """Add rate limiting middleware to FastAPI app"""
    middleware = RateLimitMiddleware(
        app=app,
        exclude_paths=exclude_paths,
        header_prefix=header_prefix
    )
    app.middleware("http")(middleware)
    return app


# Rate limiting decorator for specific endpoints
def rate_limit(limit: int, window: int, scope: str = "endpoint"):
    """Decorator for endpoint-specific rate limiting"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # This would be implemented for specific endpoint limiting
            # For now, it's a placeholder
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Utility functions for rate limit management
async def reset_rate_limits(identifier: str, identifier_type: str = "user"):
    """Reset rate limits for a user or IP"""
    try:
        limiter = await get_rate_limiter()
        if identifier_type == "user":
            await limiter.reset_user_limits(identifier)
        elif identifier_type == "ip":
            await limiter.reset_ip_limits(identifier)
        return True
    except Exception as e:
        logger.error(f"Error resetting rate limits: {e}")
        return False


async def get_rate_limit_metrics(days: int = 1):
    """Get rate limiting metrics"""
    try:
        limiter = await get_rate_limiter()
        return await limiter.get_metrics(days)
    except Exception as e:
        logger.error(f"Error getting rate limit metrics: {e}")
        return None


async def update_rate_limit_rules(rules: dict):
    """Update rate limiting rules"""
    try:
        limiter = await get_rate_limiter()
        
        # Clear existing rules
        limiter.rules.clear()
        
        # Add new rules
        from .advanced_limiter import RateLimitRule, RateLimitScope, RateLimitStrategy
        
        for name, rule_config in rules.items():
            rule = RateLimitRule(
                scope=RateLimitScope(rule_config["scope"]),
                strategy=RateLimitStrategy(rule_config["strategy"]),
                limit=rule_config["limit"],
                window=rule_config["window"],
                burst=rule_config.get("burst"),
                leak_rate=rule_config.get("leak_rate"),
                enabled=rule_config.get("enabled", True),
                priority=rule_config.get("priority", 0)
            )
            limiter.add_rule(name, rule)
        
        return True
    except Exception as e:
        logger.error(f"Error updating rate limit rules: {e}")
        return False


# FastAPI endpoints for rate limit management
def create_rate_limit_routes(app: FastAPI, prefix: str = "/admin/rate-limits"):
    """Create rate limit management endpoints"""
    
    @app.get(f"{prefix}/metrics")
    async def get_metrics(days: int = 1):
        """Get rate limiting metrics"""
        metrics = await get_rate_limit_metrics(days)
        if metrics:
            return metrics
        raise HTTPException(status_code=500, detail="Failed to get metrics")
    
    @app.post(f"{prefix}/reset/user/{{user_id}}")
    async def reset_user_limits(user_id: str):
        """Reset rate limits for a user"""
        success = await reset_rate_limits(user_id, "user")
        if success:
            return {"message": f"Rate limits reset for user {user_id}"}
        raise HTTPException(status_code=500, detail="Failed to reset limits")
    
    @app.post(f"{prefix}/reset/ip/{{ip}}")
    async def reset_ip_limits(ip: str):
        """Reset rate limits for an IP"""
        success = await reset_rate_limits(ip, "ip")
        if success:
            return {"message": f"Rate limits reset for IP {ip}"}
        raise HTTPException(status_code=500, detail="Failed to reset limits")
    
    @app.get(f"{prefix}/rules")
    async def get_rules():
        """Get current rate limiting rules"""
        try:
            limiter = await get_rate_limiter()
            rules = {}
            for name, rule in limiter.rules.items():
                rules[name] = {
                    "scope": rule.scope.value,
                    "strategy": rule.strategy.value,
                    "limit": rule.limit,
                    "window": rule.window,
                    "burst": rule.burst,
                    "leak_rate": rule.leak_rate,
                    "enabled": rule.enabled,
                    "priority": rule.priority
                }
            return rules
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post(f"{prefix}/rules")
    async def update_rules(rules: dict):
        """Update rate limiting rules"""
        success = await update_rate_limit_rules(rules)
        if success:
            return {"message": "Rate limiting rules updated"}
        raise HTTPException(status_code=500, detail="Failed to update rules")


# Example usage configuration
def configure_advanced_rate_limiting(app: FastAPI):
    """Complete configuration for advanced rate limiting"""
    
    # Add rate limiting middleware
    add_rate_limiting(app, exclude_paths=[
        "/health",
        "/docs", 
        "/redoc",
        "/openapi.json",
        "/admin/rate-limits"
    ])
    
    # Add management endpoints
    create_rate_limit_routes(app)
    
    # Initialize with default rules
    async def startup_event():
        limiter = await get_rate_limiter()
        logger.info("Advanced rate limiting initialized")
    
    app.add_event_handler("startup", startup_event)
    
    return app