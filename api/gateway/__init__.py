"""
Sistema H3 - API Gateway Central

Gateway unificado para todas as APIs do sistema com roteamento, 
autenticação e middleware integrados.
"""

from .gateway_main import APIGateway, get_api_gateway
from .middleware import (
    AuthenticationMiddleware,
    RateLimitMiddleware,
    CORSMiddleware,
    LoggingMiddleware
)
from .router_manager import RouterManager, get_router_manager
from .config import GatewayConfig, SecurityConfig

__all__ = [
    "APIGateway",
    "get_api_gateway",
    "AuthenticationMiddleware",
    "RateLimitMiddleware", 
    "CORSMiddleware",
    "LoggingMiddleware",
    "RouterManager",
    "get_router_manager",
    "GatewayConfig",
    "SecurityConfig"
]