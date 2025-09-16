"""Darwin Platform Context Cache Router

REST endpoints for context caching analysis and management.
Provides prompt optimization and cache statistics.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from api.security import rate_limit, require_api_key
from services.context_cache import (
    analyze_prompt_caching,
    get_context_cache,
    prepare_cached_prompt,
)
from services.settings import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/context-cache",
    tags=["Context Cache"],
    dependencies=[Depends(require_api_key), Depends(rate_limit)],
)


class PromptAnalysisRequest(BaseModel):
    """Request model for prompt analysis."""

    prompt: str = Field(..., description="Prompt text to analyze")
    model: str = Field(default="gemini-1.5-pro", description="Target model for caching")


class PromptAnalysisResponse(BaseModel):
    """Response model for prompt analysis."""

    cacheable: bool = Field(..., description="Whether prompt is cacheable")
    cache_available: bool = Field(..., description="Whether cache is available")
    prefix_length: int = Field(..., description="Length of stable prefix")
    suffix_length: int = Field(..., description="Length of dynamic suffix")
    recommendations: List[Dict[str, Any]] = Field(
        ..., description="Optimization recommendations"
    )
    estimated_savings: Dict[str, Any] = Field(
        ..., description="Estimated performance savings"
    )


class CacheStatsResponse(BaseModel):
    """Response model for cache statistics."""

    total_entries: int = Field(..., description="Total cache entries")
    hit_ratio: float = Field(..., description="Cache hit ratio")
    cache_utilization: float = Field(..., description="Cache utilization")
    total_hits: int = Field(..., description="Total cache hits")
    total_requests: int = Field(..., description="Total requests")
    top_prefixes: List[Dict[str, Any]] = Field(..., description="Most used prefixes")


class CacheOptimizationResponse(BaseModel):
    """Response model for cache optimization."""

    original_prompt: str = Field(..., description="Original prompt")
    cached_prefix: Optional[str] = Field(..., description="Cached prefix")
    dynamic_suffix: str = Field(..., description="Dynamic suffix")
    cache_key: Optional[str] = Field(..., description="Cache key")
    cache_available: bool = Field(..., description="Cache availability")
    model: str = Field(..., description="Target model")
    optimization: Dict[str, Any] = Field(..., description="Optimization details")


@router.post("/analyze", response_model=PromptAnalysisResponse)
async def analyze_prompt(
    request: PromptAnalysisRequest, settings=Depends(get_settings)
):
    """
    Analyze a prompt for caching opportunities.

    Provides detailed analysis including:
    - Cache availability
    - Optimization recommendations
    - Performance savings estimates
    """
    try:
        if not settings.CONTEXT_CACHE_ENABLED:
            raise HTTPException(status_code=503, detail="Context caching is disabled")

        analysis = analyze_prompt_caching(request.prompt, request.model)

        return PromptAnalysisResponse(**analysis)

    except Exception as e:
        logger.error(f"Error analyzing prompt: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/optimize", response_model=CacheOptimizationResponse)
async def optimize_prompt(
    request: PromptAnalysisRequest, settings=Depends(get_settings)
):
    """
    Optimize a prompt for context caching.

    Prepares the prompt by:
    - Identifying stable prefixes
    - Creating cache entries
    - Providing optimization metadata
    """
    try:
        if not settings.CONTEXT_CACHE_ENABLED:
            raise HTTPException(status_code=503, detail="Context caching is disabled")

        optimization = prepare_cached_prompt(request.prompt, request.model)

        return CacheOptimizationResponse(**optimization)

    except Exception as e:
        logger.error(f"Error optimizing prompt: {e}")
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


@router.get("/stats", response_model=CacheStatsResponse)
async def get_cache_stats(settings=Depends(get_settings)):
    """
    Get context cache statistics.

    Returns:
    - Cache utilization metrics
    - Hit ratio statistics
    - Most frequently used prefixes
    """
    try:
        if not settings.CONTEXT_CACHE_ENABLED:
            raise HTTPException(status_code=503, detail="Context caching is disabled")

        cache = get_context_cache()
        stats = cache.get_cache_stats()

        return CacheStatsResponse(**stats)

    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")


@router.delete("/clear")
async def clear_cache(settings=Depends(get_settings)):
    """
    Clear the context cache.

    Removes all cached prefixes and resets statistics.
    """
    try:
        if not settings.CONTEXT_CACHE_ENABLED:
            raise HTTPException(status_code=503, detail="Context caching is disabled")

        cache = get_context_cache()
        cache.cache.clear()
        cache.prefix_stats.clear()

        logger.info("Context cache cleared")

        return {"message": "Cache cleared successfully"}

    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=f"Cache clear failed: {str(e)}")


@router.get("/config")
async def get_cache_config(settings=Depends(get_settings)):
    """
    Get context cache configuration.

    Returns cache settings and export configuration
    for external systems.
    """
    try:
        if not settings.CONTEXT_CACHE_ENABLED:
            return {"enabled": False, "message": "Context caching is disabled"}

        cache = get_context_cache()
        config = cache.export_cache_config()

        return {
            "enabled": True,
            "max_cache_size": cache.max_cache_size,
            "current_size": len(cache.cache),
            **config,
        }

    except Exception as e:
        logger.error(f"Error getting cache config: {e}")
        raise HTTPException(
            status_code=500, detail=f"Config retrieval failed: {str(e)}"
        )


@router.get("/health")
async def cache_health_check():
    """Health check for context cache service."""
    try:
        cache = get_context_cache()

        return {
            "status": "healthy",
            "cache_size": len(cache.cache),
            "max_size": cache.max_cache_size,
            "utilization": len(cache.cache) / cache.max_cache_size,
        }

    except Exception as e:
        logger.error(f"Context cache health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}
