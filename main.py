"""Darwin Platform Main Application

FastAPI application that integrates all Darwin platform components:
- Vertex AI RAG backends
- Project memory with search
- Tree-search PUCT algorithms
- Score contracts execution
- Context caching system
- Security and rate limiting
"""

import logging
import time

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.auth import APIKeyMiddleware, get_api_key_required
from api.routers import (
    bigquery_test,
    context_cache,
    gemini_test,
    health,
    memory,
    rag,
    rag_plus,
    score_contracts,
    tree_search,
)
from services.settings import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize settings
settings = get_settings()

# Create FastAPI application
app = FastAPI(
    title="Darwin Platform",
    description=(
        "Advanced RAG + Tree-Search platform with Vertex AI integration, "
        "project memory, and context caching"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else [settings.BASE_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time header to responses."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.middleware("http")
async def add_darwin_headers(request: Request, call_next):
    """Add Darwin platform headers."""
    response = await call_next(request)
    response.headers["X-Darwin-Platform"] = "1.0.0"
    response.headers["X-Darwin-Instance"] = settings.PROJECT_ID
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "path": str(request.url.path),
        },
    )


# Include routers
app.include_router(health.router)
app.include_router(rag.router)
app.include_router(memory.router)
app.include_router(tree_search.router)
app.include_router(score_contracts.router)
app.include_router(context_cache.router)
app.include_router(rag_plus.router)
app.include_router(gemini_test.router)
app.include_router(bigquery_test.router)

@app.get("/test-auth")
async def test_auth_endpoint():
    """Test endpoint that requires API key authentication."""
    return {"message": "Authentication successful!", "protected": True}


@app.get("/")
async def root(request: Request):
    """Darwin platform root endpoint."""
    # Simple API key authentication
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="API key required")
    
    api_key = auth_header.split(" ")[1]
    valid_keys = ["test-key-123", "another-key-456"]  # Simple list for testing
    if api_key not in valid_keys:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return {
        "platform": "Darwin",
        "version": "1.0.0",
        "description": "Advanced RAG + Tree-Search platform",
        "features": [
            "Vertex AI RAG backends",
            "Project memory with search",
            "Tree-search PUCT algorithms",
            "Score contracts execution",
            "Context caching system",
            "API key authentication",
            "Rate limiting",
        ],
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "rag": "/rag",
            "memory": "/memory",
            "tree_search": "/tree-search",
            "score_contracts": "/score-contracts",
            "context_cache": "/context-cache",
        },
        "integrations": {
            "chatgpt_actions": "/.well-known/ai-plugin.json",
            "gemini_extensions": "/.well-known/gemini-extension.json",
        },
    }


@app.get("/status")
async def platform_status():
    """Get comprehensive platform status."""
    try:
        from services.context_cache import get_context_cache
        from services.rag_vertex import get_rag

        # Check RAG backend
        rag_backend = get_rag()
        rag_health = await rag_backend.health_check()

        # Check context cache
        context_cache = get_context_cache()
        cache_stats = context_cache.get_cache_stats()

        return {
            "status": "operational",
            "timestamp": time.time(),
            "components": {
                "rag_backend": {
                    "healthy": rag_health.healthy,
                    "type": rag_health.backend_type,
                    "response_time_ms": rag_health.response_time_ms,
                },
                "context_cache": {
                    "enabled": settings.CONTEXT_CACHE_ENABLED,
                    "entries": cache_stats["total_entries"],
                    "hit_ratio": cache_stats["hit_ratio"],
                },
                "security": {
                    "api_key_auth": True,
                    "rate_limiting": True,
                    "cors_enabled": True,
                },
                "memory": {"storage_type": "hybrid_jsonl_sqlite", "enabled": True},
                "tree_search": {"algorithm": "PUCT", "enabled": True},
                "score_contracts": {
                    "sandboxed": True,
                    "available_contracts": [
                        "delta_kec_v1",
                        "zuco_reading_v1",
                        "editorial_v1",
                    ],
                },
            },
            "configuration": {
                "project_id": settings.PROJECT_ID,
                "location": settings.LOCATION,
                "debug_mode": settings.DEBUG,
                "base_url": settings.BASE_URL,
            },
        }

    except Exception as e:
        logger.error(f"Status check failed: {e}")
        return {"status": "degraded", "error": str(e), "timestamp": time.time()}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info" if not settings.DEBUG else "debug",
    )

# Configure API Key Authentication (after all routes are defined)
app.add_middleware(APIKeyMiddleware)
