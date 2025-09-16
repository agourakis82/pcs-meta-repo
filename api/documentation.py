"""
Documentation and API Discovery system for PCS-HELIO MCP API.

This module provides comprehensive API documentation with:
- OpenAPI schema generation and customization
- Endpoint discovery and categorization
- API versioning and changelog tracking
- Interactive examples and code samples
- Documentation templates and metadata
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, Field

from .config import settings
from .logging import get_logger

logger = get_logger("documentation")


class EndpointInfo(BaseModel):
    """Information about a single API endpoint."""

    path: str = Field(description="Endpoint path")
    method: str = Field(description="HTTP method")
    summary: str = Field(description="Brief description")
    description: Optional[str] = Field(description="Detailed description")
    tags: List[str] = Field(description="Endpoint tags")
    auth_required: bool = Field(description="Authentication required")
    rate_limited: bool = Field(description="Rate limiting applied")
    parameters: List[Dict[str, Any]] = Field(description="Parameters info")
    responses: Dict[str, Dict[str, Any]] = Field(description="Response schemas")


class APIVersionInfo(BaseModel):
    """API version information."""

    version: str = Field(description="Version number")
    release_date: Optional[str] = Field(description="Release date")
    status: str = Field(description="Version status (stable, beta, deprecated)")
    changelog: List[str] = Field(description="Changes in this version")
    breaking_changes: List[str] = Field(description="Breaking changes")
    migration_guide: Optional[str] = Field(
        default="", description="Migration guide URL"
    )


class APIDocumentation(BaseModel):
    """Complete API documentation model."""

    info: Dict[str, Any] = Field(description="API information")
    servers: List[Dict[str, Any]] = Field(description="Server information")
    endpoints: List[EndpointInfo] = Field(description="Available endpoints")
    versions: List[APIVersionInfo] = Field(description="Version history")
    schemas: Dict[str, Any] = Field(description="Data schemas")
    examples: Dict[str, Any] = Field(description="Usage examples")
    guides: Dict[str, str] = Field(description="Documentation guides")


class DocumentationManager:
    """Manages API documentation generation and discovery."""

    def __init__(self, app: FastAPI):
        """
        Initialize documentation manager.

        Args:
            app: FastAPI application instance
        """
        self.app = app
        self.logger = get_logger("doc_manager")
        self._cached_openapi: Optional[Dict[str, Any]] = None
        self._endpoint_cache: Optional[List[EndpointInfo]] = None

    def get_custom_openapi(self) -> Dict[str, Any]:
        """
        Generate customized OpenAPI schema.

        Returns:
            Enhanced OpenAPI schema with additional metadata
        """
        if self._cached_openapi:
            return self._cached_openapi

        try:
            # Generate base OpenAPI schema with error handling
            openapi_schema = get_openapi(
                title=settings.API_NAME,
                version=settings.api_version,
                description=self._get_api_description(),
                routes=self.app.routes,
                tags=self._get_api_tags(),
            )
        except Exception as e:
            self.logger.error(f"Error generating base OpenAPI schema: {e}")
            # Fallback to minimal schema
            openapi_schema = {
                "openapi": "3.0.2",
                "info": {
                    "title": settings.API_NAME,
                    "version": settings.api_version,
                    "description": self._get_api_description(),
                },
                "paths": {},
            }

        # Add custom enhancements
        openapi_schema["info"].update(
            {
                "contact": {
                    "name": "PCS-HELIO Project",
                    "url": "https://github.com/agourakis82/pcs-meta-repo",
                    "email": "support@pcs-helio.org",
                },
                "license": {
                    "name": "MIT",
                    "url": "https://opensource.org/licenses/MIT",
                },
                "termsOfService": "https://pcs-helio.org/terms",
                "x-logo": {
                    "url": "https://pcs-helio.org/logo.png",
                    "altText": "PCS-HELIO Logo",
                },
            }
        )

        # Add server information
        openapi_schema["servers"] = [
            {"url": "http://localhost:8000", "description": "Development server"},
            {"url": "https://api.pcs-helio.org", "description": "Production server"},
        ]

        # Ensure components exists before adding security schemes
        if "components" not in openapi_schema:
            openapi_schema["components"] = {}

        # Add security schemes
        openapi_schema["components"]["securitySchemes"] = {
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "Authorization",
                "description": "API key authentication. Use format: Bearer <api_key>",
            },
            "ApiKeyQuery": {
                "type": "apiKey",
                "in": "query",
                "name": "api_key",
                "description": "API key as query parameter",
            },
        }

        # Add examples to schemas
        self._add_schema_examples(openapi_schema)

        # Add custom extensions
        openapi_schema["x-api-version"] = settings.api_version
        openapi_schema["x-generated-at"] = datetime.now().isoformat()
        openapi_schema["x-features"] = [
            "Authentication",
            "Rate Limiting",
            "Structured Logging",
            "Error Handling",
            "API Versioning",
            "Interactive Documentation",
        ]

        self._cached_openapi = openapi_schema
        return openapi_schema

    def discover_endpoints(self) -> List[EndpointInfo]:
        """
        Discover and analyze all API endpoints.

        Returns:
            List of endpoint information
        """
        if self._endpoint_cache:
            return self._endpoint_cache

        endpoints = []
        openapi_schema = self.get_custom_openapi()

        for path, path_info in openapi_schema.get("paths", {}).items():
            for method, method_info in path_info.items():
                if method.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                    endpoint = EndpointInfo(
                        path=path,
                        method=method.upper(),
                        summary=method_info.get("summary", ""),
                        description=method_info.get("description", ""),
                        tags=method_info.get("tags", []),
                        auth_required=self._is_auth_required(method_info),
                        rate_limited=self._is_rate_limited(path),
                        parameters=self._extract_parameters(method_info),
                        responses=method_info.get("responses", {}),
                    )
                    endpoints.append(endpoint)

        self._endpoint_cache = endpoints
        return endpoints

    def get_api_documentation(self) -> APIDocumentation:
        """
        Generate complete API documentation.

        Returns:
            Comprehensive API documentation
        """
        openapi_schema = self.get_custom_openapi()
        endpoints = self.discover_endpoints()

        return APIDocumentation(
            info=openapi_schema["info"],
            servers=openapi_schema.get("servers", []),
            endpoints=endpoints,
            versions=self._get_version_history(),
            schemas=openapi_schema.get("components", {}).get("schemas", {}),
            examples=self._get_usage_examples(),
            guides=self._get_documentation_guides(),
        )

    def generate_sdk_examples(self, language: str = "python") -> Dict[str, str]:
        """
        Generate SDK usage examples for different languages.

        Args:
            language: Programming language for examples

        Returns:
            Dictionary of endpoint examples
        """
        examples = {}
        endpoints = self.discover_endpoints()

        for endpoint in endpoints:
            if language.lower() == "python":
                examples[f"{endpoint.method}_{endpoint.path}"] = (
                    self._generate_python_example(endpoint)
                )
            elif language.lower() == "javascript":
                examples[f"{endpoint.method}_{endpoint.path}"] = (
                    self._generate_javascript_example(endpoint)
                )
            elif language.lower() == "curl":
                examples[f"{endpoint.method}_{endpoint.path}"] = (
                    self._generate_curl_example(endpoint)
                )

        return examples

    def generate_postman_collection(self) -> Dict[str, Any]:
        """
        Generate Postman collection for API testing.

        Returns:
            Postman collection JSON
        """
        collection = {
            "info": {
                "name": f"{settings.API_NAME} API",
                "description": f"Postman collection for {settings.API_NAME}",
                "version": settings.api_version,
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            },
            "auth": {
                "type": "apikey",
                "apikey": [
                    {"key": "key", "value": "Authorization", "type": "string"},
                    {"key": "value", "value": "Bearer {{api_key}}", "type": "string"},
                ],
            },
            "variable": [
                {"key": "base_url", "value": "http://localhost:8000", "type": "string"},
                {"key": "api_key", "value": "your_api_key_here", "type": "string"},
            ],
            "item": [],
        }

        endpoints = self.discover_endpoints()

        # Group endpoints by tags
        grouped_endpoints: Dict[str, List[EndpointInfo]] = {}
        for endpoint in endpoints:
            for tag in endpoint.tags or ["General"]:
                if tag not in grouped_endpoints:
                    grouped_endpoints[tag] = []
                grouped_endpoints[tag].append(endpoint)

        # Create collection items
        for tag, tag_endpoints in grouped_endpoints.items():
            folder = {"name": tag, "item": []}

            for endpoint in tag_endpoints:
                item = self._create_postman_item(endpoint)
                folder["item"].append(item)

            collection["item"].append(folder)

        return collection

    def _get_api_description(self) -> str:
        """Get enhanced API description."""
        return f"""
        **{settings.API_NAME}** - Model Context Protocol Server
        
        A comprehensive API for academic research data processing with:
        
        🔐 **Security**: API key authentication with rate limiting
        📊 **Monitoring**: Structured logging and performance metrics  
        🛡️ **Reliability**: Comprehensive error handling and validation
        📚 **Documentation**: Interactive OpenAPI documentation
        🔧 **Developer Tools**: SDKs, examples, and testing tools
        
        **Version**: {settings.api_version}
        **Environment**: {settings.ENV}
        """

    def _get_api_tags(self) -> List[Dict[str, str]]:
        """Get API tags with descriptions."""
        return [
            {
                "name": "Core",
                "description": "Essential endpoints for health, status, and basic info",
            },
            {
                "name": "Authentication",
                "description": "API key management and authentication status",
            },
            {
                "name": "Documentation",
                "description": "API documentation, discovery, and examples",
            },
            {
                "name": "Admin",
                "description": "Administrative endpoints for system management",
            },
            {"name": "Data", "description": "Data access and processing endpoints"},
            {"name": "RAG", "description": "Retrieval-Augmented Generation endpoints"},
            {
                "name": "Notebooks",
                "description": "Jupyter notebook management endpoints",
            },
        ]

    def _add_schema_examples(self, openapi_schema: Dict[str, Any]) -> None:
        """Add examples to schema components."""
        schemas = openapi_schema.get("components", {}).get("schemas", {})

        # Add examples for common schemas
        for schema_name, schema_def in schemas.items():
            if schema_name == "ErrorResponse":
                schema_def["example"] = {
                    "error": True,
                    "status_code": 422,
                    "error_type": "validation_error",
                    "message": "Request validation failed",
                    "details": [
                        {
                            "type": "validation_error",
                            "message": "Field 'email' is invalid",
                            "field": "email",
                            "code": "invalid_format",
                        }
                    ],
                    "timestamp": "2025-09-14T19:30:00Z",
                    "request_id": "abc123",
                    "help": "Check the request format and required fields",
                }
            elif schema_name == "HealthCheckResponse":
                schema_def["example"] = {
                    "success": True,
                    "timestamp": "2025-09-14T19:30:00Z",
                    "status": "healthy",
                    "version": settings.api_version,
                    "uptime_seconds": 3600.5,
                    "checks": {"database": True, "cache": True, "external_api": True},
                }

    def _is_auth_required(self, method_info: Dict[str, Any]) -> bool:
        """Check if endpoint requires authentication."""
        return "security" in method_info

    def _is_rate_limited(self, path: str) -> bool:
        """Check if endpoint is rate limited."""
        # Most endpoints are rate limited except health/ping
        exempt_paths = ["/health", "/ping", "/", "/docs", "/redoc"]
        return path not in exempt_paths

    def _extract_parameters(self, method_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract parameter information from method info."""
        parameters = []

        for param in method_info.get("parameters", []):
            parameters.append(
                {
                    "name": param.get("name"),
                    "in": param.get("in"),
                    "required": param.get("required", False),
                    "type": param.get("schema", {}).get("type"),
                    "description": param.get("description", ""),
                }
            )

        return parameters

    def _get_version_history(self) -> List[APIVersionInfo]:
        """Get API version history."""
        return [
            APIVersionInfo(
                version=settings.api_version,
                release_date="2025-09-14",
                status="stable",
                changelog=[
                    "Complete authentication system",
                    "Rate limiting implementation",
                    "Structured logging",
                    "Error handling and validation",
                    "API documentation system",
                ],
                breaking_changes=[],
                migration_guide=None,
            )
        ]

    def _get_usage_examples(self) -> Dict[str, Any]:
        """Get API usage examples."""
        return {
            "authentication": {
                "header": "Authorization: Bearer your_api_key_here",
                "query": "?api_key=your_api_key_here",
            },
            "basic_requests": {
                "health_check": "GET /health",
                "get_info": "GET /info",
                "test_validation": "POST /test-validation",
            },
            "error_handling": {
                "validation_error": {
                    "status": 422,
                    "response": {
                        "error": True,
                        "error_type": "validation_error",
                        "message": "Request validation failed",
                    },
                },
                "auth_error": {
                    "status": 401,
                    "response": {
                        "error": True,
                        "error_type": "authentication_error",
                        "message": "Authentication required",
                    },
                },
            },
        }

    def _get_documentation_guides(self) -> Dict[str, str]:
        """Get documentation guides."""
        return {
            "getting_started": "/docs/getting-started",
            "authentication": "/docs/authentication",
            "rate_limiting": "/docs/rate-limiting",
            "error_handling": "/docs/error-handling",
            "sdk_python": "/docs/sdk/python",
            "sdk_javascript": "/docs/sdk/javascript",
        }

    def _generate_python_example(self, endpoint: EndpointInfo) -> str:
        """Generate Python SDK example."""
        method = endpoint.method.lower()
        path = endpoint.path

        example = f"""
import requests

# {endpoint.summary}
url = "http://localhost:8000{path}"
headers = {{"Authorization": "Bearer your_api_key_here"}}

"""

        if method == "get":
            example += "response = requests.get(url, headers=headers)\n"
        elif method == "post":
            example += """data = {"key": "value"}
response = requests.post(url, json=data, headers=headers)
"""

        example += """
if response.status_code == 200:
    result = response.json()
    print(result)
else:
    print(f"Error: {response.status_code} - {response.text}")
"""

        return example.strip()

    def _generate_javascript_example(self, endpoint: EndpointInfo) -> str:
        """Generate JavaScript example."""
        method = endpoint.method.lower()
        path = endpoint.path

        example = f"""
// {endpoint.summary}
const url = 'http://localhost:8000{path}';
const headers = {{
    'Authorization': 'Bearer your_api_key_here',
    'Content-Type': 'application/json'
}};

"""

        if method == "get":
            example += """
fetch(url, { method: 'GET', headers })
    .then(response => response.json())
    .then(data => console.log(data))
    .catch(error => console.error('Error:', error));
"""
        elif method == "post":
            example += """
const data = { key: 'value' };

fetch(url, {
    method: 'POST',
    headers,
    body: JSON.stringify(data)
})
    .then(response => response.json()) 
    .then(data => console.log(data))
    .catch(error => console.error('Error:', error));
"""

        return example.strip()

    def _generate_curl_example(self, endpoint: EndpointInfo) -> str:
        """Generate cURL example."""
        method = endpoint.method
        path = endpoint.path

        example = f"""
# {endpoint.summary}
curl -X {method} \\
  'http://localhost:8000{path}' \\
  -H 'Authorization: Bearer your_api_key_here' \\
"""

        if method in ["POST", "PUT", "PATCH"]:
            example += """  -H 'Content-Type: application/json' \\
  -d '{"key": "value"}'
"""

        return example.strip()

    def _create_postman_item(self, endpoint: EndpointInfo) -> Dict[str, Any]:
        """Create Postman collection item for endpoint."""
        return {
            "name": endpoint.summary or f"{endpoint.method} {endpoint.path}",
            "request": {
                "method": endpoint.method,
                "header": [
                    {
                        "key": "Authorization",
                        "value": "Bearer {{api_key}}",
                        "type": "text",
                    }
                ]
                if endpoint.auth_required
                else [],
                "url": {
                    "raw": "{{base_url}}" + endpoint.path,
                    "host": ["{{base_url}}"],
                    "path": endpoint.path.strip("/").split("/"),
                },
                "description": endpoint.description,
            },
            "response": [],
        }


# Global documentation manager instance
_doc_manager: Optional[DocumentationManager] = None


def get_documentation_manager(app: FastAPI) -> DocumentationManager:
    """
    Get or create documentation manager instance.

    Args:
        app: FastAPI application

    Returns:
        Documentation manager instance
    """
    global _doc_manager
    if _doc_manager is None:
        _doc_manager = DocumentationManager(app)
    return _doc_manager


def setup_documentation_routes(app: FastAPI) -> None:
    """
    Setup documentation routes in FastAPI app.

    Args:
        app: FastAPI application to add routes to
    """
    doc_manager = get_documentation_manager(app)

    @app.get("/api-docs", response_model=dict, tags=["Documentation"])
    async def get_api_documentation():
        """Get complete API documentation."""
        docs = doc_manager.get_api_documentation()
        return docs.model_dump()

    @app.get("/endpoints", response_model=List[dict], tags=["Documentation"])
    async def discover_endpoints():
        """Discover all available API endpoints."""
        endpoints = doc_manager.discover_endpoints()
        return [endpoint.model_dump() for endpoint in endpoints]

    @app.get("/examples/{language}", response_model=dict, tags=["Documentation"])
    async def get_sdk_examples(language: str):
        """Get SDK examples for specified language."""
        supported_languages = ["python", "javascript", "curl"]
        if language.lower() not in supported_languages:
            from .errors import ValidationError

            raise ValidationError(
                f"Language '{language}' not supported. "
                f"Supported: {', '.join(supported_languages)}"
            )

        examples = doc_manager.generate_sdk_examples(language)
        return {"language": language, "examples": examples}

    @app.get("/postman", response_model=dict, tags=["Documentation"])
    async def get_postman_collection():
        """Get Postman collection for API testing."""
        collection = doc_manager.generate_postman_collection()
        return collection
