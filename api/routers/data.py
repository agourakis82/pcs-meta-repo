"""Data router for AG5 and HELIO data endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from services.ag5_service import ag5_service
from services.helio_service import helio_service

from ..auth import optional_api_key, require_api_key
from ..logging import get_logger
from ..models import HELIOSummary, PaginationParams
from ..rate_limit import rate_limit_dependency

logger = get_logger("data_router")

router = APIRouter(prefix="/data", tags=["data"])


@router.get("/ag5/datasets")
async def list_ag5_datasets(
    api_key: str = Depends(optional_api_key),
    _rate_limit: None = Depends(rate_limit_dependency),
):
    """List available AG5 datasets."""
    logger.info("AG5 datasets list requested")

    try:
        datasets = await ag5_service.list_datasets()
        return {"datasets": datasets, "count": len(datasets)}

    except Exception as e:
        logger.error("Failed to list AG5 datasets", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve datasets")


@router.get("/ag5/datasets/{dataset_name}")
async def get_ag5_dataset_info(
    dataset_name: str,
    api_key: str = Depends(require_api_key),
    _rate_limit: None = Depends(rate_limit_dependency),
):
    """Get information about a specific AG5 dataset."""
    logger.info("AG5 dataset info requested", dataset=dataset_name)

    try:
        info = await ag5_service.get_dataset_info(dataset_name)
        return info

    except Exception as e:
        logger.error(
            "Failed to get AG5 dataset info", dataset=dataset_name, error=str(e)
        )
        raise HTTPException(
            status_code=404, detail="Dataset not found or error occurred"
        )


@router.get("/ag5/search")
async def search_ag5_datasets(
    q: str = Query(..., description="Search query"),
    api_key: str = Depends(optional_api_key),
    _rate_limit: None = Depends(rate_limit_dependency),
):
    """Search AG5 datasets."""
    logger.info("AG5 dataset search requested", query=q)

    try:
        results = await ag5_service.search_datasets(q)
        return {"results": results, "count": len(results), "query": q}

    except Exception as e:
        logger.error("AG5 dataset search failed", query=q, error=str(e))
        raise HTTPException(status_code=500, detail="Search failed")


@router.get("/helio/summaries", response_model=List[HELIOSummary])
async def get_helio_summaries(
    limit: Optional[int] = Query(
        None, ge=1, le=100, description="Limit number of results"
    ),
    api_key: str = Depends(optional_api_key),
    _rate_limit: None = Depends(rate_limit_dependency),
):
    """Get HELIO summaries."""
    logger.info("HELIO summaries requested", limit=limit)

    try:
        summaries = await helio_service.get_summaries(limit=limit)
        return summaries

    except Exception as e:
        logger.error("Failed to get HELIO summaries", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve summaries")


@router.get("/health")
async def data_health():
    """Get data services health status."""
    try:
        ag5_health = await ag5_service.health_check()
        helio_health = await helio_service.health_check()

        return {"ag5": ag5_health, "helio": helio_health}

    except Exception as e:
        logger.error("Data services health check failed", error=str(e))
        raise HTTPException(status_code=500, detail="Health check failed")
