"""
Sistema H3 - API Gateway Central

Gateway unificado para todas as APIs do sistema com roteamento,
autenticação e middleware integrados.
"""

from .config import GatewayConfig, get_gateway_config
from .gateway_main import APIGateway, create_gateway, get_gateway_instance
from .middleware import (
    AuthenticationMiddleware,
    CompressionMiddleware,
    CORSMiddleware,
    LoggingMiddleware,
    RateLimitMiddleware,
    SecurityMiddleware,
)
from .router_manager import RouteMetadata, RouterManager

__all__ = [
    # Configuração
    "GatewayConfig",
    "get_gateway_config",
    # Gateway principal
    "APIGateway",
    "create_gateway",
    "get_gateway_instance",
    # Middlewares
    "LoggingMiddleware",
    "SecurityMiddleware",
    "RateLimitMiddleware",
    "AuthenticationMiddleware",
    "CORSMiddleware",
    "CompressionMiddleware",
    # Gerenciamento de rotas
    "RouterManager",
    "RouteMetadata",
]
