"""Darwin Platform OpenAPI Configuration

OpenAPI setup for ChatGPT Actions and Gemini Extensions integration.
"""

from typing import Any, Dict

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

from services.settings import get_settings


def setup_darwin_openapi(app: FastAPI) -> None:
    """
    Configure OpenAPI for Darwin platform.

    Adds security schemes and tags for ChatGPT Actions and Gemini Extensions.

    Args:
        app: FastAPI application instance
    """

    def custom_openapi() -> Dict[str, Any]:
        """Generate custom OpenAPI schema."""
        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = get_openapi(
            title="Darwin Platform",
            version="4.4.0",
            description=(
                "RAG + Tree-Search platform with Vertex AI backends. "
                "Provides retrieval-augmented generation, project memory, "
                "and tree-search exploration capabilities."
            ),
            routes=app.routes,
        )

        # Add security schemes
        openapi_schema["components"]["securitySchemes"] = {
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
                "description": "API key for authentication",
            },
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "Bearer token authentication",
            },
        }

        # Add global security
        openapi_schema["security"] = [{"ApiKeyAuth": []}, {"BearerAuth": []}]

        # Add server information
        settings = get_settings()
        openapi_schema["servers"] = [
            {
                "url": settings.BASE_URL or "https://darwin-platform.run.app",
                "description": "Production server",
            },
            {"url": "http://localhost:8000", "description": "Development server"},
        ]

        # Add custom tags with descriptions
        openapi_schema["tags"] = [
            {
                "name": "RAG",
                "description": "Retrieval-Augmented Generation endpoints",
                "externalDocs": {
                    "description": "RAG Documentation",
                    "url": "https://cloud.google.com/vertex-ai/docs/generative-ai/rag-overview",
                },
            },
            {
                "name": "Memory",
                "description": "Project memory and session logging",
            },
            {
                "name": "Health",
                "description": "System health and status endpoints",
            },
            {
                "name": "Tree-Search",
                "description": "Tree-Search PUCT exploration algorithms",
            },
        ]

        # Add contact and license info
        openapi_schema["info"]["contact"] = {
            "name": "Darwin Platform Support",
            "url": "https://github.com/pcs-meta-repo",
            "email": "support@darwin-platform.io",
        }

        openapi_schema["info"]["license"] = {
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT",
        }

        # Add custom extensions for ChatGPT Actions
        openapi_schema["info"]["x-chatgpt-actions"] = {
            "name": "Darwin Platform",
            "description": "RAG and Tree-Search capabilities",
            "privacy_policy_url": "https://darwin-platform.io/privacy",
            "legal_info_url": "https://darwin-platform.io/legal",
        }

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi


def create_ai_plugin_manifest() -> Dict[str, Any]:
    """
    Create ai-plugin.json manifest for ChatGPT Actions.

    Returns:
        Plugin manifest dictionary
    """
    settings = get_settings()

    return {
        "schema_version": "v1",
        "name_for_human": "Darwin Platform",
        "name_for_model": "darwin",
        "description_for_human": "RAG + Tree-Search platform with Vertex AI backends",
        "description_for_model": (
            "Darwin platform provides retrieval-augmented generation (RAG) "
            "using Vertex AI, project memory with session logging, and "
            "tree-search exploration with PUCT algorithms. "
            "Use for research queries, document retrieval, and intelligent search."
        ),
        "auth": {
            "type": "service_http",
            "authorization_type": "bearer",
            "verification_tokens": {
                "openai": settings.OPENAI_VERIFICATION_TOKEN or "darwin-openai-token"
            },
        },
        "api": {
            "type": "openapi",
            "url": f"{settings.BASE_URL or 'https://darwin-platform.run.app'}/openapi.json",
        },
        "logo_url": f"{settings.BASE_URL or 'https://darwin-platform.run.app'}/static/logo.png",
        "contact_email": "support@darwin-platform.io",
        "legal_info_url": "https://darwin-platform.io/legal",
    }


def create_gemini_extension_manifest() -> Dict[str, Any]:
    """
    Create manifest for Gemini Extensions.

    Returns:
        Gemini extension manifest dictionary
    """
    settings = get_settings()

    return {
        "name": "Darwin Platform",
        "description": "RAG + Tree-Search platform with Vertex AI backends",
        "version": "4.4.0",
        "api_version": "v1",
        "authentication": {"type": "api_key", "api_key_header": "X-API-Key"},
        "endpoints": {
            "base_url": settings.BASE_URL or "https://darwin-platform.run.app",
            "openapi_spec": "/openapi.json",
        },
        "capabilities": ["text_generation", "document_retrieval", "search", "memory"],
        "rate_limits": {
            "requests_per_minute": settings.RATE_LIMIT_REQUESTS,
            "tokens_per_request": settings.RATE_LIMIT_TOKENS,
        },
    }


def setup_well_known_routes(app: FastAPI) -> None:
    """
    Setup .well-known routes for AI integrations.

    Args:
        app: FastAPI application instance
    """

    @app.get("/.well-known/ai-plugin.json")
    async def ai_plugin_manifest():
        """ChatGPT Actions plugin manifest."""
        return JSONResponse(
            content=create_ai_plugin_manifest(),
            headers={"Content-Type": "application/json"},
        )

    @app.get("/.well-known/gemini-extension.json")
    async def gemini_extension_manifest():
        """Gemini Extensions manifest."""
        return JSONResponse(
            content=create_gemini_extension_manifest(),
            headers={"Content-Type": "application/json"},
        )


def configure_openapi_security(app: FastAPI) -> None:
    """
    Configure OpenAPI security for all endpoints.

    Args:
        app: FastAPI application instance
    """
    # This will be handled by the custom_openapi function
    # Security is added to individual router dependencies
    pass
