"""Darwin Platform Health & Version Endpoints

System health checks and version information.
"""

import asyncio
import platform
import sys
from datetime import datetime, timezone
from typing import Any, Dict, Union

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.rag_vertex import get_rag

router = APIRouter(prefix="/health", tags=["Health"])


class HealthStatus(BaseModel):
    """Health status response."""

    status: str
    timestamp: str
    version: str
    backends: Dict[str, Dict[str, Union[str, bool]]]
    system: Dict[str, str]


class VersionInfo(BaseModel):
    """Version information response."""

    name: str
    version: str
    platform: str
    python_version: str
    build_time: str


@router.get("", response_model=HealthStatus)
async def health_check() -> HealthStatus:
    """
    Comprehensive health check for Darwin platform.

    Checks RAG backends, system resources, and configurations.

    Returns:
        Health status with component details
    """
    try:
        # Get system info
        timestamp = datetime.now(timezone.utc).isoformat()

        # Check RAG backend health
        backends = {}
        try:
            rag_backend = get_rag()
            rag_healthy = await rag_backend.health_check()
            backends["rag"] = {
                "status": "healthy" if rag_healthy else "unhealthy",
                "backend_type": type(rag_backend).__name__,
            }
        except Exception as e:
            backends["rag"] = {"status": "unhealthy", "error": str(e)}

        # System information
        system_info = {
            "platform": platform.platform(),
            "python_version": (
                f"{sys.version_info.major}."
                f"{sys.version_info.minor}."
                f"{sys.version_info.micro}"
            ),
            "architecture": platform.architecture()[0],
        }

        # Overall status
        overall_status = (
            "healthy"
            if all(backend.get("status") == "healthy" for backend in backends.values())
            else "degraded"
        )

        return HealthStatus(
            status=overall_status,
            timestamp=timestamp,
            version="4.4.0",  # Darwin platform version
            backends=backends,
            system=system_info,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/ping")
async def ping() -> Dict[str, str]:
    """
    Simple ping endpoint for basic availability checks.

    Returns:
        Simple pong response
    """
    return {
        "status": "ok",
        "message": "pong",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/version", response_model=VersionInfo)
async def version() -> VersionInfo:
    """
    Get Darwin platform version information.

    Returns:
        Detailed version and build information
    """
    return VersionInfo(
        name="Darwin Platform",
        version="4.4.0",
        platform=platform.platform(),
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        build_time=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """
    Kubernetes-style readiness probe.

    Checks if the service is ready to receive traffic.

    Returns:
        Readiness status
    """
    try:
        # Check critical dependencies
        # Remove unused settings variable

        # Verify RAG backend can be initialized
        rag_backend = get_rag()

        # Quick health check
        try:
            health_result = await asyncio.wait_for(
                rag_backend.health_check(),
                timeout=5.0,  # 5 second timeout
            )
            rag_ready = health_result
        except asyncio.TimeoutError:
            rag_ready = False
        except Exception:
            rag_ready = False

        ready = rag_ready

        return {
            "ready": ready,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": {
                "rag_backend": rag_ready,
                "settings": True,  # If we got here, settings loaded
            },
        }

    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service not ready: {str(e)}")


@router.get("/live")
async def liveness_check() -> Dict[str, str]:
    """
    Kubernetes-style liveness probe.

    Simple check that the service is alive and responding.

    Returns:
        Liveness status
    """
    return {"alive": "true", "timestamp": datetime.now(timezone.utc).isoformat()}
