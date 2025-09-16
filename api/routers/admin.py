"""Admin router for health checks and version information."""

import time
from pathlib import Path

from fastapi import APIRouter, Depends

from services.ag5_service import ag5_service
from services.helio_service import helio_service
from services.notebook_service import notebook_service
from services.rag_service import rag_service

from ..auth import optional_api_key
from ..config import settings
from ..logging import get_logger
from ..models import HealthResponse, VersionResponse

logger = get_logger("admin_router")

router = APIRouter(prefix="/admin", tags=["admin"])

# Track application start time for uptime calculation
_start_time = time.time()


@router.get("/health", response_model=HealthResponse)
async def health_check(api_key: str = Depends(optional_api_key)):
    """
    Get application health status.

    Returns overall health and status of individual services.
    """
    logger.debug("Health check requested")

    uptime_s = time.time() - _start_time

    # Gather health status from all services
    services = {}

    try:
        services.update(await rag_service.health_check())
    except Exception as e:
        logger.error("RAG service health check failed", error=str(e))
        services["rag_service"] = "error"

    try:
        services.update(await ag5_service.health_check())
    except Exception as e:
        logger.error("AG5 service health check failed", error=str(e))
        services["ag5_service"] = "error"

    try:
        services.update(await helio_service.health_check())
    except Exception as e:
        logger.error("HELIO service health check failed", error=str(e))
        services["helio_service"] = "error"

    try:
        services.update(await notebook_service.health_check())
    except Exception as e:
        logger.error("Notebook service health check failed", error=str(e))
        services["notebook_service"] = "error"

    # Determine overall health
    overall_health = all(
        status in ["ready", "unavailable"]
        for status in services.values()
        if isinstance(status, str)
    )

    return HealthResponse(
        ok=overall_health,
        uptime_s=uptime_s,
        services=services,
        version=settings.api_version,
    )


@router.get("/version", response_model=VersionResponse)
async def version_info(api_key: str = Depends(optional_api_key)):
    """
    Get API version and build information.

    Returns version details, git information, and repository metadata.
    """
    logger.debug("Version info requested")

    # Try to get git information
    git_sha = None
    build_timestamp = None

    try:
        # Look for git information in common locations
        git_head_path = Path(".git/HEAD")
        if git_head_path.exists():
            head_content = git_head_path.read_text().strip()
            if head_content.startswith("ref: "):
                ref_path = Path(".git") / head_content[5:]
                if ref_path.exists():
                    git_sha = ref_path.read_text().strip()[:8]
    except Exception:
        pass  # Git info is optional

    # Model versions (placeholder)
    model_versions = {
        "openai": settings.openai_model,
        "embedding": "text-embedding-ada-002",  # placeholder
    }

    # Repository information
    repository = {
        "url": settings.repo_url,
        "doi": settings.repo_doi,
        "name": "PCS-Meta-Repo",
        "description": "Research data and analysis repository",
    }

    return VersionResponse(
        api_version=settings.api_version,
        git_sha=git_sha,
        build_timestamp=build_timestamp,
        model_versions=model_versions,
        repository=repository,
    )
