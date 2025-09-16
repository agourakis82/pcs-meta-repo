"""Main FastAPI application factory for the PCS-HELIO MCP API."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .auth import APIKeyMiddleware
from .cache import cache_manager
from .config import settings
from .documentation import get_documentation_manager, setup_documentation_routes
from .errors import (
    APIError,
    api_error_handler,
    general_exception_handler,
    validation_error_handler,
)
from .logging import RequestLoggingMiddleware, get_logger
from .monitoring import initialize_monitoring, shutdown_monitoring
from .processing import start_processing, stop_processing
from .rate_limit import RateLimitMiddleware
from .routers import admin, core, data, monitoring, notebooks, rag, rag_plus
from .routers.processing import router as processing_router

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events for the FastAPI application.
    """
    logger.info("Starting PCS-HELIO MCP API")

    # Initialize cache manager
    await cache_manager.initialize()
    logger.info("Cache manager initialized")

    # Initialize monitoring system
    await initialize_monitoring()
    logger.info("Monitoring system initialized")

    # Initialize processing system
    await start_processing()
    logger.info("Processing system initialized")

    # Log configuration details
    logger.info(f"Environment: {settings.ENV}")
    logger.info(f"API Version: {settings.api_version}")
    logger.info(f"Authentication required: {settings.API_KEY_REQUIRED}")
    logger.info(
        f"Rate limiting enabled: {settings.RATE_LIMIT_REQUESTS_PER_MINUTE} req/min"
    )
    logger.info(f"Cache enabled: {getattr(settings, 'CACHE_ENABLED', True)}")

    yield

    logger.info("Shutting down PCS-HELIO MCP API")

    # Shutdown processing system
    await stop_processing()
    logger.info("Processing system shutdown")

    # Shutdown monitoring system
    await shutdown_monitoring()
    logger.info("Monitoring system shutdown")

    # Shutdown cache manager
    await cache_manager.shutdown()
    logger.info("Cache manager shutdown")

    # Shutdown cache manager
    await cache_manager.shutdown()
    logger.info("Cache manager shutdown complete")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance
    """
    # Create FastAPI app with OpenAPI configuration
    app = FastAPI(
        title=settings.api_title,
        description=settings.api_description,
        version=settings.api_version,
        lifespan=lifespan,
        openapi_tags=[
            {
                "name": "admin",
                "description": "Administrative endpoints for health and version",
            },
            {
                "name": "rag",
                "description": "Retrieval-Augmented Generation for documents",
            },
            {
                "name": "RAG++ Enhanced Research",
                "description": "Advanced RAG with iterative reasoning and discovery",
            },
            {
                "name": "data",
                "description": "Data access endpoints for AG5 and HELIO datasets",
            },
            {
                "name": "notebooks",
                "description": "Jupyter notebook management endpoints",
            },
        ],
        contact={
            "name": "PCS-HELIO Project",
            "url": settings.repo_url,
        },
        license_info={
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT",
        },
    )

    # Add CORS middleware if enabled
    if settings.cors_enabled:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins or ["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        logger.info("CORS enabled", extra={"origins": settings.cors_origins or ["*"]})

    # Add middleware pipeline in reverse order (last added = first executed)

    # 1. Request logging (outermost - logs everything)
    app.add_middleware(
        RequestLoggingMiddleware,
        logger_name="http.access",
        exempt_paths=["/health", "/ping"],
    )

    # 2. Rate limiting (before authentication to limit all requests)
    app.add_middleware(
        RateLimitMiddleware,
        exempt_paths=["/", "/health", "/ping", "/docs", "/redoc", "/openapi.json"],
        tokens_per_request=1,
    )

    # 3. Authentication (innermost - only applies to protected endpoints)
    app.add_middleware(
        APIKeyMiddleware,
        exempt_paths=["/", "/health", "/ping", "/docs", "/redoc", "/openapi.json"],
        require_auth=False,  # Let individual endpoints decide
    )

    # Add exception handlers for comprehensive error handling
    app.add_exception_handler(APIError, api_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    # Include routers
    app.include_router(core.router)  # Core endpoints at root level
    app.include_router(admin.router)
    app.include_router(rag.router)
    app.include_router(rag_plus.router)  # RAG++ Enhanced Research endpoints
    app.include_router(data.router)
    app.include_router(notebooks.router)
    app.include_router(monitoring.router, prefix="/monitoring")  # Monitoring endpoints
    app.include_router(processing_router)  # Processing endpoints

    # Setup documentation routes
    setup_documentation_routes(app)

    # Customize OpenAPI schema
    doc_manager = get_documentation_manager(app)
    app.openapi = doc_manager.get_custom_openapi

    # Mount static files if directory exists
    if settings.static_path.exists():
        app.mount("/static", StaticFiles(directory=settings.static_path), name="static")
        logger.info("Static files mounted", extra={"path": str(settings.static_path)})

    logger.info("FastAPI application created", extra={"title": settings.api_title})
    return app


# Create application instance
app = create_app()
