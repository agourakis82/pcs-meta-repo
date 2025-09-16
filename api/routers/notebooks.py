"""Notebooks router for Jupyter notebook operations."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException

from services.notebook_service import notebook_service

from ..auth import optional_api_key
from ..logging import get_logger
from ..rate_limit import rate_limit_dependency

logger = get_logger("notebooks_router")

router = APIRouter(prefix="/notebooks", tags=["notebooks"])


@router.get("/")
async def list_notebooks(
    api_key: str = Depends(optional_api_key),
    _rate_limit: None = Depends(rate_limit_dependency),
):
    """List available Jupyter notebooks."""
    logger.info("Notebooks list requested")

    try:
        notebooks = await notebook_service.list_notebooks()
        return {"notebooks": notebooks, "count": len(notebooks)}

    except Exception as e:
        logger.error("Failed to list notebooks", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve notebooks")


@router.get("/health")
async def notebooks_health():
    """Get notebooks service health status."""
    try:
        health = await notebook_service.health_check()
        return health

    except Exception as e:
        logger.error("Notebooks health check failed", error=str(e))
        raise HTTPException(status_code=500, detail="Health check failed")
