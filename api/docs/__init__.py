"""
Sistema H3 - Documentação Automática

Módulo de geração automática de documentação OpenAPI 3.0
"""

from .auto_generator import (
    APIMetadata,
    AutoDocumentationGenerator,
    DocFormat,
    DocumentationConfig,
)

__all__ = [
    "AutoDocumentationGenerator",
    "DocFormat",
    "APIMetadata",
    "DocumentationConfig",
]
