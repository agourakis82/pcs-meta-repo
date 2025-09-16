"""
Sistema H2 - Router de Cache

API endpoints para operações de cache e monitoramento.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from .manager import CacheManager, get_cache_manager
from .metrics import CacheMetrics, get_cache_metrics
from .strategies import InvalidationManager, get_invalidation_manager

logger = logging.getLogger(__name__)

# Modelos de dados
class CacheSetRequest(BaseModel):
    key: str
    value: Any
    ttl: Optional[int] = None
    tags: Optional[List[str]] = None
    dependencies: Optional[List[str]] = None


class CacheGetResponse(BaseModel):
    value: Any
    hit: bool
    backend: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class CacheDeleteRequest(BaseModel):
    key: str


class CacheStatsResponse(BaseModel):
    total_requests: int
    hits: int
    misses: int
    hit_rate: float
    avg_response_time: float
    total_size_bytes: int
    backend_stats: Dict[str, Dict[str, Any]]
    top_keys: List[Dict[str, Any]]
    error_rate: float
    operations_per_second: float


class CacheHealthResponse(BaseModel):
    status: str
    backends: Dict[str, Dict[str, Any]]
    metrics: Dict[str, Any]
    strategy: Optional[str] = None


# Router
router = APIRouter(prefix="/cache", tags=["cache"])


# Dependências
def get_cache() -> CacheManager:
    """Dependência para obter cache manager."""
    return get_cache_manager()


def get_metrics() -> CacheMetrics:
    """Dependência para obter métricas."""
    return get_cache_metrics()


def get_strategies() -> InvalidationManager:
    """Dependência para obter estratégias."""
    return get_invalidation_manager()


# Endpoints principais
@router.get("/get/{key}", response_model=CacheGetResponse)
async def cache_get(
    key: str,
    cache: CacheManager = Depends(get_cache)
):
    """Obtém valor do cache."""
    try:
        result = await cache.get(key)
        
        if result is not None:
            return CacheGetResponse(
                value=result,
                hit=True,
                backend=cache.get_backend_name(),
                metadata={"timestamp": cache._get_timestamp()}
            )
        else:
            return CacheGetResponse(
                value=None,
                hit=False,
                backend=None,
                metadata=None
            )
    
    except Exception as e:
        logger.error(f"Error getting cache key {key}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/set", response_model=Dict[str, str])
async def cache_set(
    request: CacheSetRequest,
    cache: CacheManager = Depends(get_cache)
):
    """Define valor no cache."""
    try:
        # Preparar metadados
        metadata = {}
        if request.ttl:
            metadata['ttl'] = request.ttl
        if request.tags:
            metadata['tags'] = request.tags
        if request.dependencies:
            metadata['dependencies'] = request.dependencies
        
        success = await cache.set(
            request.key,
            request.value,
            ttl=request.ttl,
            metadata=metadata
        )
        
        if success:
            return {"status": "success", "key": request.key}
        else:
            raise HTTPException(status_code=500, detail="Failed to set cache")
    
    except Exception as e:
        logger.error(f"Error setting cache key {request.key}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete/{key}")
async def cache_delete(
    key: str,
    cache: CacheManager = Depends(get_cache)
):
    """Remove valor do cache."""
    try:
        success = await cache.delete(key)
        
        if success:
            return {"status": "success", "key": key}
        else:
            return {"status": "not_found", "key": key}
    
    except Exception as e:
        logger.error(f"Error deleting cache key {key}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/delete", response_model=Dict[str, Any])
async def cache_delete_multiple(
    request: CacheDeleteRequest,
    cache: CacheManager = Depends(get_cache)
):
    """Remove múltiplas chaves do cache."""
    try:
        success = await cache.delete(request.key)
        
        return {
            "status": "success" if success else "not_found",
            "key": request.key,
            "deleted": success
        }
    
    except Exception as e:
        logger.error(f"Error deleting cache key {request.key}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/exists/{key}")
async def cache_exists(
    key: str,
    cache: CacheManager = Depends(get_cache)
):
    """Verifica se chave existe no cache."""
    try:
        exists = await cache.exists(key)
        return {"key": key, "exists": exists}
    
    except Exception as e:
        logger.error(f"Error checking cache key {key}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/keys")
async def cache_keys(
    pattern: Optional[str] = Query(None, description="Pattern to filter keys"),
    limit: Optional[int] = Query(100, description="Maximum number of keys"),
    cache: CacheManager = Depends(get_cache)
):
    """Lista chaves do cache."""
    try:
        keys = await cache.keys(pattern or "*")
        
        # Aplicar limite
        if limit and len(keys) > limit:
            keys = keys[:limit]
        
        return {
            "keys": keys,
            "count": len(keys),
            "pattern": pattern,
            "limit": limit
        }
    
    except Exception as e:
        logger.error(f"Error listing cache keys: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear")
async def cache_clear(
    confirm: bool = Query(False, description="Confirmation required"),
    cache: CacheManager = Depends(get_cache)
):
    """Limpa todo o cache."""
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Confirmation required. Set confirm=true"
        )
    
    try:
        success = await cache.clear()
        
        return {
            "status": "success" if success else "failed",
            "message": "Cache cleared" if success else "Failed to clear cache"
        }
    
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Endpoints de métricas
@router.get("/stats", response_model=CacheStatsResponse)
async def cache_stats(
    metrics: CacheMetrics = Depends(get_metrics)
):
    """Obtém estatísticas do cache."""
    try:
        stats = metrics.get_stats()
        
        return CacheStatsResponse(
            total_requests=stats.total_requests,
            hits=stats.hits,
            misses=stats.misses,
            hit_rate=stats.hit_rate,
            avg_response_time=stats.avg_response_time,
            total_size_bytes=stats.total_size_bytes,
            backend_stats=stats.backend_stats,
            top_keys=stats.top_keys,
            error_rate=stats.error_rate,
            operations_per_second=stats.operations_per_second
        )
    
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/time-series")
async def cache_time_series(
    metric: str = Query("hit_rate", description="Metric name"),
    interval_minutes: int = Query(5, description="Interval in minutes"),
    hours: int = Query(1, description="Hours of history"),
    metrics: CacheMetrics = Depends(get_metrics)
):
    """Obtém série temporal de métricas."""
    try:
        data = metrics.get_time_series(metric, interval_minutes, hours)
        return data
    
    except Exception as e:
        logger.error(f"Error getting time series for {metric}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/backends")
async def cache_backend_comparison(
    metrics: CacheMetrics = Depends(get_metrics)
):
    """Compara performance entre backends."""
    try:
        comparison = metrics.get_backend_comparison()
        return {"backends": comparison}
    
    except Exception as e:
        logger.error(f"Error getting backend comparison: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/keys")
async def cache_key_analytics(
    limit: int = Query(20, description="Number of top keys"),
    metrics: CacheMetrics = Depends(get_metrics)
):
    """Analisa uso das chaves."""
    try:
        analytics = metrics.get_key_analytics(limit)
        return analytics
    
    except Exception as e:
        logger.error(f"Error getting key analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/export")
async def cache_export_metrics(
    format: str = Query("json", description="Export format"),
    hours: int = Query(1, description="Hours of history"),
    metrics: CacheMetrics = Depends(get_metrics)
):
    """Exporta métricas."""
    try:
        data = metrics.export_metrics(format, hours)
        return data
    
    except Exception as e:
        logger.error(f"Error exporting metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Endpoints de estratégias
@router.get("/strategies")
async def list_strategies(
    strategies: InvalidationManager = Depends(get_strategies)
):
    """Lista estratégias disponíveis."""
    try:
        strategy_names = list(strategies.strategies.keys())
        active_strategy = strategies.active_strategy
        
        return {
            "strategies": strategy_names,
            "active": active_strategy,
            "count": len(strategy_names)
        }
    
    except Exception as e:
        logger.error(f"Error listing strategies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/strategies/{strategy_name}/activate")
async def activate_strategy(
    strategy_name: str,
    strategies: InvalidationManager = Depends(get_strategies)
):
    """Ativa uma estratégia de invalidação."""
    try:
        strategies.set_active_strategy(strategy_name)
        
        return {
            "status": "success",
            "active_strategy": strategy_name
        }
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error activating strategy {strategy_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/strategies/cleanup")
async def manual_cleanup(
    strategies: InvalidationManager = Depends(get_strategies),
    cache: CacheManager = Depends(get_cache)
):
    """Executa limpeza manual."""
    try:
        keys_to_remove = await strategies.cleanup()
        
        removed_count = 0
        for key in keys_to_remove:
            success = await cache.delete(key)
            if success:
                removed_count += 1
        
        return {
            "status": "success",
            "keys_found": len(keys_to_remove),
            "keys_removed": removed_count
        }
    
    except Exception as e:
        logger.error(f"Error during manual cleanup: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Endpoint de health check
@router.get("/health", response_model=CacheHealthResponse)
async def cache_health(
    cache: CacheManager = Depends(get_cache),
    metrics: CacheMetrics = Depends(get_metrics),
    strategies: InvalidationManager = Depends(get_strategies)
):
    """Verifica saúde do sistema de cache."""
    try:
        # Verificar backends
        backend_health = {}
        
        # Test basic operations
        test_key = "__health_check__"
        test_value = "ok"
        
        try:
            # Test set
            await cache.set(test_key, test_value, ttl=60)
            
            # Test get
            result = await cache.get(test_key)
            
            # Test delete
            await cache.delete(test_key)
            
            backend_health[cache.get_backend_name()] = {
                "status": "healthy",
                "operations": {
                    "set": True,
                    "get": result == test_value,
                    "delete": True
                }
            }
        
        except Exception as e:
            backend_health[cache.get_backend_name()] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # Métricas básicas
        stats = metrics.get_stats()
        metrics_summary = {
            "total_requests": stats.total_requests,
            "hit_rate": stats.hit_rate,
            "avg_response_time": stats.avg_response_time,
            "error_rate": stats.error_rate
        }
        
        # Status geral
        all_healthy = all(
            backend.get("status") == "healthy"
            for backend in backend_health.values()
        )
        
        return CacheHealthResponse(
            status="healthy" if all_healthy else "degraded",
            backends=backend_health,
            metrics=metrics_summary,
            strategy=strategies.active_strategy
        )
    
    except Exception as e:
        logger.error(f"Error during health check: {e}")
        return CacheHealthResponse(
            status="unhealthy",
            backends={},
            metrics={},
            strategy=None
        )        )