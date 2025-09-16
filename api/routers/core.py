"""
Core endpoints for PCS-HELIO MCP API.

This module provides essential MCP server endpoints including:
- Health and status monitoring
- Server information and capabilities
- Authentication status
- Rate limiting information
- Basic server metadata
"""

import platform
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import psutil
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from ..auth import get_api_key_optional, get_api_key_required
from ..cache import clear_all_cache, get_cache_stats, invalidate_cache_tags
from ..config import settings
from ..errors import NotFoundError, ValidationError
from ..logging import get_logger, log_performance_metric
from ..rate_limit import get_rate_limit_status
from ..validation import ErrorValidationRequest

logger = get_logger("core")

router = APIRouter(tags=["core"])

# Track server start time
_start_time = time.time()
_start_datetime = datetime.now(timezone.utc)


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(description="Overall server status")
    timestamp: str = Field(description="Current timestamp")
    uptime_seconds: float = Field(description="Server uptime in seconds")
    version: str = Field(description="API version")
    environment: str = Field(description="Environment (development/production)")


class ServerInfoResponse(BaseModel):
    """Server information response model."""

    name: str = Field(description="Server name")
    version: str = Field(description="API version")
    description: str = Field(description="Server description")
    environment: str = Field(description="Environment")
    started_at: str = Field(description="Server start timestamp")
    uptime_seconds: float = Field(description="Server uptime")
    python_version: str = Field(description="Python version")
    platform: str = Field(description="Platform information")
    capabilities: Dict[str, Any] = Field(description="Server capabilities")


class StatusResponse(BaseModel):
    """Detailed server status response."""

    server: Dict[str, Any] = Field(description="Server status information")
    authentication: Dict[str, Any] = Field(description="Authentication status")
    rate_limiting: Dict[str, Any] = Field(description="Rate limiting status")
    system: Dict[str, Any] = Field(description="System resource information")
    configuration: Dict[str, Any] = Field(description="Configuration summary")


class AuthStatusResponse(BaseModel):
    """Authentication status response."""

    authenticated: bool = Field(description="Whether request is authenticated")
    api_key_required: bool = Field(description="Whether API key is required")
    api_key_present: bool = Field(description="Whether API key was provided")
    method: Optional[str] = Field(description="Authentication method used")


@router.get("/", summary="Root endpoint", response_model=Dict[str, str])
async def root(request: Request):
    """
    Root endpoint providing basic server information.

    Returns basic server identification and links to documentation.
    """
    log_performance_metric("root_endpoint_accessed", 1, "request")

    return {
        "name": settings.API_NAME,
        "version": "1.0.0",  # TODO: Get from settings
        "description": "PCS-HELIO Model Context Protocol API",
        "status": "running",
        "documentation": "/docs",
        "health": "/health",
        "info": "/info",
    }


@router.get("/health", summary="Health check", response_model=HealthResponse)
async def health_check(request: Request):
    """
    Simple health check endpoint.

    Returns server health status and basic metrics.
    Does not require authentication.
    """
    uptime = time.time() - _start_time
    current_time = datetime.now(timezone.utc).isoformat()

    # Log health check with client info
    logger.debug(
        "Health check accessed",
        extra={
            "client_ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("User-Agent", ""),
            "uptime_seconds": uptime,
        },
    )

    return HealthResponse(
        status="healthy",
        timestamp=current_time,
        uptime_seconds=round(uptime, 2),
        version="1.0.0",  # TODO: Get from settings
        environment=settings.ENV,
    )


@router.get("/info", summary="Server information", response_model=ServerInfoResponse)
async def server_info(
    request: Request, api_key: Optional[str] = Depends(get_api_key_optional)
):
    """
    Detailed server information endpoint.

    Returns comprehensive server details including capabilities.
    Authentication is optional but provides additional information if authenticated.
    """
    uptime = time.time() - _start_time

    # Basic capabilities
    capabilities = {
        "authentication": {
            "api_key": True,
            "bearer_token": True,
            "query_parameter": True,
        },
        "rate_limiting": {
            "enabled": True,
            "per_api_key": True,
            "per_ip": True,
            "burst_capacity": settings.RATE_LIMIT_BURST_CAPACITY,
        },
        "logging": {
            "structured": True,
            "correlation_ids": True,
            "performance_metrics": True,
        },
        "formats": {
            "json": True,
            "streaming": False,  # TODO: Implement if needed
        },
    }

    # Add authenticated capabilities
    if api_key:
        capabilities["authenticated_features"] = {
            "higher_rate_limits": True,
            "detailed_metrics": True,
            "admin_endpoints": False,  # TODO: Implement role-based access
        }

    logger.info(
        "Server info accessed",
        extra={
            "authenticated": api_key is not None,
            "client_ip": request.client.host if request.client else "unknown",
        },
    )

    return ServerInfoResponse(
        name=settings.API_NAME,
        version="1.0.0",  # TODO: Get from settings
        description=(
            "PCS-HELIO Model Context Protocol API for academic research "
            "data processing"
        ),
        environment=settings.ENV,
        started_at=_start_datetime.isoformat(),
        uptime_seconds=round(uptime, 2),
        python_version=platform.python_version(),
        platform=f"{platform.system()} {platform.release()}",
        capabilities=capabilities,
    )


@router.get("/status", summary="Detailed status", response_model=StatusResponse)
async def detailed_status(
    request: Request, api_key: str = Depends(get_api_key_required)
):
    """
    Detailed server status endpoint.

    Returns comprehensive server status including system resources.
    Requires authentication.
    """
    uptime = time.time() - _start_time

    # Server status
    server_status = {
        "name": settings.API_NAME,
        "version": "1.0.0",  # TODO: Get from settings
        "environment": settings.ENV,
        "uptime_seconds": round(uptime, 2),
        "started_at": _start_datetime.isoformat(),
        "status": "running",
    }

    # Authentication status
    auth_status = {
        "api_key_required": settings.API_KEY_REQUIRED,
        "total_api_keys": len(settings.api_keys_list),
        "current_authenticated": True,
        "authentication_method": "api_key",
    }

    # Rate limiting status
    rate_limit_info = get_rate_limit_status(request)

    # System information
    try:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        system_info = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "percent_used": memory.percent,
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "percent_used": round((disk.used / disk.total) * 100, 1),
            },
            "load_average": list(psutil.getloadavg())
            if hasattr(psutil, "getloadavg")
            else None,
        }
    except Exception as e:
        logger.warning("Failed to get system info", extra={"error": str(e)})
        system_info = {"error": "System information unavailable"}

    # Configuration summary (non-sensitive)
    config_summary = {
        "api_name": settings.API_NAME,
        "environment": settings.ENV,
        "rate_limit_per_minute": settings.RATE_LIMIT_REQUESTS_PER_MINUTE,
        "rate_limit_burst": settings.RATE_LIMIT_BURST_CAPACITY,
        "openai_model": settings.OPENAI_API_KEY[:8] + "..."
        if settings.OPENAI_API_KEY
        else "not_configured",
        "embedding_model": settings.EMBEDDING_MODEL,
        "data_directory": str(settings.data_path),
        "chroma_path": str(settings.chroma_path),
    }

    logger.info(
        "Detailed status accessed",
        extra={
            "api_key_prefix": api_key[:8] + "..." if len(api_key) > 8 else api_key,
            "client_ip": request.client.host if request.client else "unknown",
        },
    )

    return StatusResponse(
        server=server_status,
        authentication=auth_status,
        rate_limiting=rate_limit_info,
        system=system_info,
        configuration=config_summary,
    )


@router.get(
    "/auth/status", summary="Authentication status", response_model=AuthStatusResponse
)
async def auth_status(
    request: Request, api_key: Optional[str] = Depends(get_api_key_optional)
):
    """
    Check authentication status for current request.

    Returns information about authentication state and requirements.
    """
    authenticated = api_key is not None
    api_key_present = api_key is not None

    auth_method = None
    if authenticated:
        # Determine authentication method used
        if request.headers.get("Authorization", "").startswith("Bearer"):
            auth_method = "bearer_token"
        elif "api_key" in request.query_params:
            auth_method = "query_parameter"
        elif "key" in request.query_params:
            auth_method = "query_parameter"
        else:
            auth_method = "header"

    logger.debug(
        "Authentication status checked",
        extra={
            "authenticated": authenticated,
            "method": auth_method,
            "client_ip": request.client.host if request.client else "unknown",
        },
    )

    return AuthStatusResponse(
        authenticated=authenticated,
        api_key_required=settings.API_KEY_REQUIRED,
        api_key_present=api_key_present,
        method=auth_method,
    )


@router.get("/ping", summary="Simple ping", response_model=Dict[str, str])
async def ping():
    """
    Simple ping endpoint for connectivity testing.

    Returns a basic pong response with timestamp.
    """
    return {
        "message": "pong",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "server": settings.API_NAME,
    }


@router.post("/test-validation", summary="Test validation system")
async def test_validation(request_data: ErrorValidationRequest) -> Dict[str, Any]:
    """
    Test endpoint for validation system.

    This endpoint demonstrates comprehensive request validation including:
    - Required field validation
    - Type checking
    - Format validation (email)
    - Choice constraints

    Args:
        request_data: Test request with various validation rules

    Returns:
        Success response if validation passes

    Raises:
        ValidationError: If any validation rules fail
    """
    log_performance_metric("validation_test_passed", 1)

    return {
        "success": True,
        "message": "Validation test passed",
        "data": {
            "required_field": request_data.required_field,
            "positive_number": request_data.positive_number,
            "email": request_data.email,
            "choice": request_data.choice,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


class CacheStatsResponse(BaseModel):
    """Cache statistics response model."""

    success: bool = Field(..., description="Operation success status")
    memory_cache: Dict[str, Any] = Field(..., description="Memory cache statistics")
    redis_cache: Optional[Dict[str, Any]] = Field(
        None, description="Redis cache statistics"
    )
    redis_available: bool = Field(..., description="Redis availability status")
    timestamp: datetime = Field(..., description="Response timestamp")


class CacheInvalidationResponse(BaseModel):
    """Cache invalidation response model."""

    success: bool = Field(..., description="Operation success status")
    entries_removed: int = Field(..., description="Number of entries removed")
    message: str = Field(..., description="Operation message")
    timestamp: datetime = Field(..., description="Response timestamp")


@router.get(
    "/cache/stats", summary="Cache statistics", response_model=CacheStatsResponse
)
async def get_cache_statistics(
    request: Request, api_key: str = Depends(get_api_key_required)
) -> CacheStatsResponse:
    """
    Get comprehensive cache statistics.

    Returns detailed information about cache performance including:
    - Hit/miss rates
    - Memory usage
    - Cache sizes
    - Redis availability
    """
    start_time = time.time()

    try:
        # Get cache statistics
        stats = await get_cache_stats()

        # Log performance
        processing_time = time.time() - start_time
        log_performance_metric(
            metric_name="cache_stats_request",
            value=processing_time * 1000,  # Convert to milliseconds
            unit="ms",
            context={
                "endpoint": "/cache/stats",
                "cache_hit": True,
                "request_size": 0,
                "response_size": len(str(stats)),
            },
        )

        logger.info(
            "Cache statistics retrieved",
            extra={
                "api_key_prefix": api_key[:8] + "..." if len(api_key) > 8 else api_key,
                "processing_time": f"{processing_time:.3f}s",
                "memory_cache_size": stats.get("memory_cache", {}).get("cache_size", 0),
                "redis_available": stats.get("redis_available", False),
            },
        )

        return CacheStatsResponse(
            success=True,
            memory_cache=stats["memory_cache"],
            redis_cache=stats["redis_cache"],
            redis_available=stats["redis_available"],
            timestamp=datetime.now(timezone.utc),
        )

    except Exception as e:
        logger.error(
            f"Error retrieving cache statistics: {e}",
            extra={
                "api_key_prefix": api_key[:8] + "..." if len(api_key) > 8 else api_key,
                "error_type": type(e).__name__,
            },
        )
        raise NotFoundError(f"Failed to retrieve cache statistics: {e}")


class CacheInvalidationRequest(BaseModel):
    """Cache invalidation request model."""

    tags: List[str] = Field(..., description="List of tags to invalidate")


@router.post("/cache/invalidate", summary="Invalidate cache by tags")
async def invalidate_cache_by_tags(
    request: Request,
    cache_request: CacheInvalidationRequest,
    api_key: str = Depends(get_api_key_required),
) -> CacheInvalidationResponse:
    """
    Invalidate cache entries by tags.

    Body should contain:
    {
        "tags": ["tag1", "tag2"]
    }
    """
    start_time = time.time()

    try:
        # Get tags from request body
        tag_list = cache_request.tags

        # Invalidate cache
        entries_removed = await invalidate_cache_tags(tag_list)

        # Log performance
        processing_time = time.time() - start_time
        log_performance_metric(
            metric_name="cache_invalidate_request",
            value=processing_time * 1000,  # Convert to milliseconds
            unit="ms",
            context={
                "endpoint": "/cache/invalidate",
                "cache_hit": False,
                "request_size": len(str(tag_list)),
                "response_size": 50,
            },
        )

        logger.info(
            "Cache invalidated by tags",
            extra={
                "api_key_prefix": api_key[:8] + "..." if len(api_key) > 8 else api_key,
                "tags": tag_list,
                "entries_removed": entries_removed,
                "processing_time": f"{processing_time:.3f}s",
            },
        )

        return CacheInvalidationResponse(
            success=True,
            entries_removed=entries_removed,
            message=f"Invalidated {entries_removed} cache entries for tags: {tag_list}",
            timestamp=datetime.now(timezone.utc),
        )

    except Exception as e:
        logger.error(
            f"Error invalidating cache: {e}",
            extra={
                "api_key_prefix": api_key[:8] + "..." if len(api_key) > 8 else api_key,
                "error_type": type(e).__name__,
            },
        )
        raise ValidationError(f"Failed to invalidate cache: {e}")


@router.delete("/cache/clear", summary="Clear all cache")
async def clear_cache(
    request: Request, api_key: str = Depends(get_api_key_required)
) -> CacheInvalidationResponse:
    """
    Clear all cache entries.

    ⚠️ Warning: This will remove all cached data.
    """
    start_time = time.time()

    try:
        # Clear all cache
        await clear_all_cache()

        # Log performance
        processing_time = time.time() - start_time
        log_performance_metric(
            metric_name="cache_clear_request",
            value=processing_time * 1000,  # Convert to milliseconds
            unit="ms",
            context={
                "endpoint": "/cache/clear",
                "cache_hit": False,
                "request_size": 0,
                "response_size": 50,
            },
        )

        logger.warning(
            "All cache cleared",
            extra={
                "api_key_prefix": api_key[:8] + "..." if len(api_key) > 8 else api_key,
                "processing_time": f"{processing_time:.3f}s",
            },
        )

        return CacheInvalidationResponse(
            success=True,
            entries_removed=-1,  # Unknown count for full clear
            message="All cache entries cleared successfully",
            timestamp=datetime.now(timezone.utc),
        )

    except Exception as e:
        logger.error(
            f"Error clearing cache: {e}",
            extra={
                "api_key_prefix": api_key[:8] + "..." if len(api_key) > 8 else api_key,
                "error_type": type(e).__name__,
            },
        )
        raise ValidationError(f"Failed to clear cache: {e}")
