"""
Automatic Documentation Generation System for PCS H3 Integration
Generates comprehensive OpenAPI 3.0 documentation with examples and versioning
"""
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

# FastAPI and OpenAPI imports
try:
    from fastapi import FastAPI
    from fastapi.openapi.models import Contact, Info, License, OpenAPI, Tag
    from fastapi.openapi.utils import get_openapi
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

logger = logging.getLogger(__name__)


class DocFormat(Enum):
    """Documentation output formats"""
    OPENAPI_JSON = "openapi_json"
    OPENAPI_YAML = "openapi_yaml"
    SWAGGER_HTML = "swagger_html"
    REDOC_HTML = "redoc_html"
    MARKDOWN = "markdown"
    POSTMAN = "postman"


@dataclass
class APIMetadata:
    """API metadata for documentation"""
    title: str = "PCS H3 Integration API"
    description: str = "Unified API for PCS H3 Integration System"
    version: str = "1.0.0"
    terms_of_service: Optional[str] = None
    contact_name: Optional[str] = "PCS Team"
    contact_email: Optional[str] = "pcs@edu.br"
    contact_url: Optional[str] = None
    license_name: Optional[str] = "MIT"
    license_url: Optional[str] = None
    tags: List[Dict[str, str]] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.tags:
            self.tags = [
                {"name": "Authentication", "description": "User authentication and authorization"},
                {"name": "Users", "description": "User management operations"},
                {"name": "Cache", "description": "Cache management and statistics"},
                {"name": "WebSocket", "description": "Real-time WebSocket connections"},
                {"name": "Metrics", "description": "System metrics and monitoring"},
                {"name": "Rate Limiting", "description": "Rate limiting configuration and metrics"},
                {"name": "Health", "description": "System health checks"},
            ]


@dataclass
class DocumentationConfig:
    """Configuration for documentation generation"""
    output_dir: str = "docs/generated"
    include_examples: bool = True
    include_schemas: bool = True
    include_security: bool = True
    generate_postman: bool = True
    generate_markdown: bool = True
    custom_css: Optional[str] = None
    custom_js: Optional[str] = None
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    

class AutoDocumentationGenerator:
    """Automatic documentation generator for FastAPI applications"""
    
    def __init__(self, config: Optional[DocumentationConfig] = None):
        self.config = config or DocumentationConfig()
        self.metadata = APIMetadata()
        self.examples = {}
        self.custom_schemas = {}
        
    def set_metadata(self, metadata: APIMetadata):
        """Set API metadata"""
        self.metadata = metadata
    
    def add_example(self, endpoint: str, method: str, example_data: Dict[str, Any]):
        """Add example for specific endpoint"""
        key = f"{method.upper()} {endpoint}"
        self.examples[key] = example_data
    
    def add_custom_schema(self, name: str, schema: Dict[str, Any]):
        """Add custom schema definition"""
        self.custom_schemas[name] = schema
    
    def generate_openapi_spec(self, app: FastAPI) -> Dict[str, Any]:
        """Generate OpenAPI 3.0 specification"""
        if not FASTAPI_AVAILABLE:
            raise ImportError("FastAPI is required for OpenAPI generation")
        
        # Generate base OpenAPI spec
        openapi_schema = get_openapi(
            title=self.metadata.title,
            version=self.metadata.version,
            description=self.metadata.description,
            routes=app.routes,
        )
        
        # Enhance with additional metadata
        self._enhance_openapi_spec(openapi_schema)
        
        # Add examples if configured
        if self.config.include_examples:
            self._add_examples_to_spec(openapi_schema)
        
        # Add custom schemas
        if self.custom_schemas:
            self._add_custom_schemas(openapi_schema)
        
        return openapi_schema
    
    def _enhance_openapi_spec(self, spec: Dict[str, Any]):
        """Enhance OpenAPI spec with additional metadata"""
        info = spec.get("info", {})
        
        # Add contact information
        if self.metadata.contact_name or self.metadata.contact_email:
            contact = {}
            if self.metadata.contact_name:
                contact["name"] = self.metadata.contact_name
            if self.metadata.contact_email:
                contact["email"] = self.metadata.contact_email
            if self.metadata.contact_url:
                contact["url"] = self.metadata.contact_url
            info["contact"] = contact
        
        # Add license information
        if self.metadata.license_name:
            license_info = {"name": self.metadata.license_name}
            if self.metadata.license_url:
                license_info["url"] = self.metadata.license_url
            info["license"] = license_info
        
        # Add terms of service
        if self.metadata.terms_of_service:
            info["termsOfService"] = self.metadata.terms_of_service
        
        # Add tags
        if self.metadata.tags:
            spec["tags"] = self.metadata.tags
        
        # Add servers
        spec["servers"] = [
            {"url": "/", "description": "Current server"},
            {"url": "http://localhost:8000", "description": "Development server"},
            {"url": "https://api.pcs.edu", "description": "Production server"}
        ]
        
        # Add security schemes
        if self.config.include_security:
            self._add_security_schemes(spec)
    
    def _add_security_schemes(self, spec: Dict[str, Any]):
        """Add security schemes to OpenAPI spec"""
        if "components" not in spec:
            spec["components"] = {}
        
        spec["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "JWT token authentication"
            },
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
                "description": "API key authentication"
            },
            "OAuth2": {
                "type": "oauth2",
                "flows": {
                    "authorizationCode": {
                        "authorizationUrl": "/oauth/authorize",
                        "tokenUrl": "/oauth/token",
                        "scopes": {
                            "read": "Read access",
                            "write": "Write access",
                            "admin": "Admin access"
                        }
                    }
                }
            }
        }
    
    def _add_examples_to_spec(self, spec: Dict[str, Any]):
        """Add examples to OpenAPI specification"""
        paths = spec.get("paths", {})
        
        for path, methods in paths.items():
            for method, operation in methods.items():
                if method.upper() == "GET":
                    continue
                
                key = f"{method.upper()} {path}"
                if key in self.examples:
                    example_data = self.examples[key]
                    
                    # Add request body example
                    if "requestBody" in operation:
                        content = operation["requestBody"].get("content", {})
                        for media_type in content:
                            if "example" not in content[media_type]:
                                content[media_type]["example"] = example_data.get("request")
                    
                    # Add response examples
                    if "responses" in operation:
                        for status_code, response in operation["responses"].items():
                            if "content" in response:
                                for media_type in response["content"]:
                                    if "example" not in response["content"][media_type]:
                                        response["content"][media_type]["example"] = example_data.get("response")
    
    def _add_custom_schemas(self, spec: Dict[str, Any]):
        """Add custom schemas to OpenAPI specification"""
        if "components" not in spec:
            spec["components"] = {}
        
        if "schemas" not in spec["components"]:
            spec["components"]["schemas"] = {}
        
        spec["components"]["schemas"].update(self.custom_schemas)
    
    def generate_documentation(self, app: FastAPI, formats: List[DocFormat] = None) -> Dict[DocFormat, str]:
        """Generate documentation in multiple formats"""
        if formats is None:
            formats = [DocFormat.OPENAPI_JSON, DocFormat.SWAGGER_HTML, DocFormat.REDOC_HTML]
        
        results = {}
        
        # Generate OpenAPI spec
        openapi_spec = self.generate_openapi_spec(app)
        
        # Ensure output directory exists
        output_dir = Path(self.config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for doc_format in formats:
            try:
                if doc_format == DocFormat.OPENAPI_JSON:
                    file_path = output_dir / "openapi.json"
                    with open(file_path, 'w') as f:
                        json.dump(openapi_spec, f, indent=2)
                    results[doc_format] = str(file_path)
                
                elif doc_format == DocFormat.OPENAPI_YAML:
                    file_path = output_dir / "openapi.yaml"
                    with open(file_path, 'w') as f:
                        yaml.dump(openapi_spec, f, default_flow_style=False)
                    results[doc_format] = str(file_path)
                
                elif doc_format == DocFormat.SWAGGER_HTML:
                    file_path = output_dir / "swagger.html"
                    html_content = self._generate_swagger_html()
                    with open(file_path, 'w') as f:
                        f.write(html_content)
                    results[doc_format] = str(file_path)
                
                elif doc_format == DocFormat.REDOC_HTML:
                    file_path = output_dir / "redoc.html"
                    html_content = self._generate_redoc_html()
                    with open(file_path, 'w') as f:
                        f.write(html_content)
                    results[doc_format] = str(file_path)
                
                elif doc_format == DocFormat.MARKDOWN:
                    file_path = output_dir / "api_documentation.md"
                    markdown_content = self._generate_markdown_docs(openapi_spec)
                    with open(file_path, 'w') as f:
                        f.write(markdown_content)
                    results[doc_format] = str(file_path)
                
                elif doc_format == DocFormat.POSTMAN:
                    file_path = output_dir / "postman_collection.json"
                    postman_collection = self._generate_postman_collection(openapi_spec)
                    with open(file_path, 'w') as f:
                        json.dump(postman_collection, f, indent=2)
                    results[doc_format] = str(file_path)
                
            except Exception as e:
                logger.error(f"Error generating {doc_format.value}: {e}")
        
        return results
    
    def _generate_swagger_html(self) -> str:
        """Generate Swagger UI HTML"""
        custom_css = ""
        if self.config.custom_css:
            custom_css = f'<link rel="stylesheet" type="text/css" href="{self.config.custom_css}">'
        
        custom_js = ""
        if self.config.custom_js:
            custom_js = f'<script src="{self.config.custom_js}"></script>'
        
        favicon = ""
        if self.config.favicon_url:
            favicon = f'<link rel="icon" type="image/x-icon" href="{self.config.favicon_url}">'
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>{self.metadata.title} - Swagger UI</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui.css" />
    {favicon}
    {custom_css}
    <style>
        html {{
            box-sizing: border-box;
            overflow: -moz-scrollbars-vertical;
            overflow-y: scroll;
        }}
        *, *:before, *:after {{
            box-sizing: inherit;
        }}
        body {{
            margin:0;
            background: #fafafa;
        }}
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui-bundle.js"></script>
    <script src="https://unpkg.com/swagger-ui-dist@4.15.5/swagger-ui-standalone-preset.js"></script>
    <script>
        window.onload = function() {{
            const ui = SwaggerUIBundle({{
                url: 'openapi.json',
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "StandaloneLayout"
            }});
        }};
    </script>
    {custom_js}
</body>
</html>
        """
    
    def _generate_redoc_html(self) -> str:
        """Generate ReDoc HTML"""
        custom_css = ""
        if self.config.custom_css:
            custom_css = f'<link rel="stylesheet" type="text/css" href="{self.config.custom_css}">'
        
        favicon = ""
        if self.config.favicon_url:
            favicon = f'<link rel="icon" type="image/x-icon" href="{self.config.favicon_url}">'
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>{self.metadata.title} - ReDoc</title>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
    {favicon}
    {custom_css}
    <style>
        body {{
            margin: 0;
            padding: 0;
        }}
    </style>
</head>
<body>
    <redoc spec-url='openapi.json'></redoc>
    <script src="https://cdn.jsdelivr.net/npm/redoc@2.0.0/bundles/redoc.standalone.js"></script>
</body>
</html>
        """
    
    def _generate_markdown_docs(self, openapi_spec: Dict[str, Any]) -> str:
        """Generate Markdown documentation"""
        info = openapi_spec.get("info", {})
        paths = openapi_spec.get("paths", {})
        
        md_content = f"""# {info.get('title', 'API Documentation')}

{info.get('description', '')}

**Version:** {info.get('version', '1.0.0')}

---

## Table of Contents

"""
        
        # Generate table of contents
        for path, methods in paths.items():
            for method in methods.keys():
                if method in ['get', 'post', 'put', 'delete', 'patch']:
                    operation = methods[method]
                    summary = operation.get('summary', f"{method.upper()} {path}")
                    anchor = f"{method}-{path}".replace('/', '-').replace('{', '').replace('}', '')
                    md_content += f"- [{summary}](#{anchor})\n"
        
        md_content += "\n---\n\n## Endpoints\n\n"
        
        # Generate endpoint documentation
        for path, methods in paths.items():
            for method, operation in methods.items():
                if method in ['get', 'post', 'put', 'delete', 'patch']:
                    md_content += self._generate_endpoint_markdown(path, method, operation)
        
        return md_content
    
    def _generate_endpoint_markdown(self, path: str, method: str, operation: Dict[str, Any]) -> str:
        """Generate Markdown for a single endpoint"""
        summary = operation.get('summary', f"{method.upper()} {path}")
        description = operation.get('description', '')
        
        md = f"""### {summary}

**{method.upper()}** `{path}`

{description}

"""
        
        # Parameters
        parameters = operation.get('parameters', [])
        if parameters:
            md += "**Parameters:**\n\n"
            for param in parameters:
                param_name = param.get('name', '')
                param_type = param.get('schema', {}).get('type', 'string')
                param_desc = param.get('description', '')
                required = "Required" if param.get('required', False) else "Optional"
                md += f"- `{param_name}` ({param_type}, {required}): {param_desc}\n"
            md += "\n"
        
        # Request body
        request_body = operation.get('requestBody')
        if request_body:
            md += "**Request Body:**\n\n"
            content = request_body.get('content', {})
            for media_type, schema_info in content.items():
                md += f"Content-Type: `{media_type}`\n\n"
                if 'example' in schema_info:
                    md += "```json\n"
                    md += json.dumps(schema_info['example'], indent=2)
                    md += "\n```\n\n"
        
        # Responses
        responses = operation.get('responses', {})
        if responses:
            md += "**Responses:**\n\n"
            for status_code, response in responses.items():
                description = response.get('description', '')
                md += f"- `{status_code}`: {description}\n"
            md += "\n"
        
        md += "---\n\n"
        return md
    
    def _generate_postman_collection(self, openapi_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Postman collection from OpenAPI spec"""
        info = openapi_spec.get("info", {})
        paths = openapi_spec.get("paths", {})
        
        collection = {
            "info": {
                "name": info.get('title', 'API Collection'),
                "description": info.get('description', ''),
                "version": info.get('version', '1.0.0'),
                "_postman_id": f"pcs-h3-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            },
            "item": []
        }
        
        # Group endpoints by tags
        tag_groups = {}
        
        for path, methods in paths.items():
            for method, operation in methods.items():
                if method in ['get', 'post', 'put', 'delete', 'patch']:
                    tags = operation.get('tags', ['Default'])
                    tag = tags[0] if tags else 'Default'
                    
                    if tag not in tag_groups:
                        tag_groups[tag] = []
                    
                    # Create Postman request
                    request = {
                        "name": operation.get('summary', f"{method.upper()} {path}"),
                        "request": {
                            "method": method.upper(),
                            "header": [],
                            "url": {
                                "raw": f"{{{{base_url}}}}{path}",
                                "host": ["{{base_url}}"],
                                "path": path.strip('/').split('/') if path != '/' else []
                            }
                        }
                    }
                    
                    # Add request body if present
                    request_body = operation.get('requestBody')
                    if request_body and method.upper() in ['POST', 'PUT', 'PATCH']:
                        content = request_body.get('content', {})
                        if 'application/json' in content:
                            request["request"]["body"] = {
                                "mode": "raw",
                                "raw": json.dumps(content['application/json'].get('example', {}), indent=2),
                                "options": {
                                    "raw": {
                                        "language": "json"
                                    }
                                }
                            }
                            request["request"]["header"].append({
                                "key": "Content-Type",
                                "value": "application/json"
                            })
                    
                    tag_groups[tag].append(request)
        
        # Create folder structure
        for tag, requests in tag_groups.items():
            folder = {
                "name": tag,
                "item": requests
            }
            collection["item"].append(folder)
        
        # Add environment variables
        collection["variable"] = [
            {
                "key": "base_url",
                "value": "http://localhost:8000",
                "type": "string"
            }
        ]
        
        return collection


def create_documentation_examples():
    """Create examples for common API operations"""
    examples = {
        "POST /auth/login": {
            "request": {
                "username": "admin",
                "password": "admin123"
            },
            "response": {
                "success": True,
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                "expires_in": 3600,
                "user": {
                    "id": "1",
                    "username": "admin",
                    "email": "admin@pcs.edu"
                }
            }
        },
        "POST /users": {
            "request": {
                "username": "newuser",
                "email": "user@pcs.edu",
                "password": "password123",
                "full_name": "New User"
            },
            "response": {
                "success": True,
                "message": "User created successfully",
                "data": "user_id=123"
            }
        },
        "GET /metrics": {
            "response": [
                {
                    "name": "cpu_usage",
                    "value": 45.5,
                    "timestamp": "2024-01-01T12:00:00Z",
                    "labels": "component=api"
                }
            ]
        }
    }
    return examples


# Global documentation generator instance
doc_generator = AutoDocumentationGenerator()


def setup_documentation(app: FastAPI, 
                       metadata: Optional[APIMetadata] = None,
                       config: Optional[DocumentationConfig] = None):
    """Setup automatic documentation for FastAPI app"""
    global doc_generator
    
    if config:
        doc_generator.config = config
    
    if metadata:
        doc_generator.set_metadata(metadata)
    
    # Add examples
    examples = create_documentation_examples()
    for endpoint, example_data in examples.items():
        method, path = endpoint.split(" ", 1)
        doc_generator.add_example(path, method, example_data)
    
    # Override the OpenAPI schema
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        
        app.openapi_schema = doc_generator.generate_openapi_spec(app)
        return app.openapi_schema
    
    app.openapi = custom_openapi
    
    return doc_generator    return doc_generator