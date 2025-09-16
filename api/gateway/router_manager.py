"""
Sistema H3 - Gerenciador de Rotas do Gateway

Gerencia rotas e endpoints de todos os sistemas integrados.
"""

import logging
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from fastapi import APIRouter
from fastapi.routing import APIRoute

from .config import GatewayConfig, get_gateway_config

logger = logging.getLogger(__name__)


class RouteMetadata:
    """Metadados de uma rota."""

    def __init__(
        self,
        path: str,
        methods: List[str],
        tags: List[str] = None,
        description: str = "",
        requires_auth: bool = True,
        rate_limit_override: Optional[Dict[str, int]] = None,
        system: str = "unknown",
    ):
        self.path = path
        self.methods = methods
        self.tags = tags or []
        self.description = description
        self.requires_auth = requires_auth
        self.rate_limit_override = rate_limit_override
        self.system = system


class RouterManager:
    """Gerenciador central de rotas do gateway."""

    def __init__(self, config: Optional[GatewayConfig] = None):
        self.config = config or get_gateway_config()
        self.routers: Dict[str, APIRouter] = {}
        self.route_metadata: Dict[str, RouteMetadata] = {}
        self.main_router = APIRouter()

        # Inicializar routers dos sistemas
        self._init_system_routers()

    def _init_system_routers(self):
        """Inicializa routers dos sistemas."""
        # Router para monitoramento (H1)
        self.routers["monitoring"] = APIRouter(
            prefix="/api/v1/monitoring", tags=["monitoring"]
        )

        # Router para cache (H2)
        self.routers["cache"] = APIRouter(prefix="/api/v1/cache", tags=["cache"])

        # Router para autenticação
        self.routers["auth"] = APIRouter(prefix="/api/v1/auth", tags=["authentication"])

        # Router para WebSockets
        self.routers["websocket"] = APIRouter(prefix="/api/v1/ws", tags=["websocket"])

        # Router para GraphQL
        self.routers["graphql"] = APIRouter(prefix="/api/v1/graphql", tags=["graphql"])

        # Router para documentação
        self.routers["docs"] = APIRouter(prefix="/api/v1/docs", tags=["documentation"])

        # Router para health checks
        self.routers["health"] = APIRouter(prefix="/health", tags=["health"])

    def register_router(
        self,
        name: str,
        router: APIRouter,
        prefix: str = "",
        tags: List[str] = None,
        system: str = "custom",
    ):
        """Registra um router customizado."""
        if prefix:
            router.prefix = prefix

        if tags:
            router.tags = tags

        self.routers[name] = router

        # Registrar metadados das rotas
        for route in router.routes:
            if isinstance(route, APIRoute):
                self._register_route_metadata(route, system)

        logger.info(f"Router '{name}' registrado com sucesso")

    def _register_route_metadata(self, route: APIRoute, system: str):
        """Registra metadados de uma rota."""
        metadata = RouteMetadata(
            path=route.path,
            methods=list(route.methods),
            tags=route.tags or [],
            description=route.description or "",
            system=system,
        )

        self.route_metadata[route.path] = metadata

    def get_router(self, name: str) -> Optional[APIRouter]:
        """Obtém um router por nome."""
        return self.routers.get(name)

    def list_routers(self) -> List[str]:
        """Lista nomes de todos os routers."""
        return list(self.routers.keys())

    def get_route_metadata(self, path: str) -> Optional[RouteMetadata]:
        """Obtém metadados de uma rota."""
        return self.route_metadata.get(path)

    def list_routes(self, system: str = None) -> List[Dict[str, Any]]:
        """Lista todas as rotas registradas."""
        routes = []

        for path, metadata in self.route_metadata.items():
            if system and metadata.system != system:
                continue

            routes.append(
                {
                    "path": path,
                    "methods": metadata.methods,
                    "tags": metadata.tags,
                    "description": metadata.description,
                    "requires_auth": metadata.requires_auth,
                    "system": metadata.system,
                }
            )

        return routes

    def create_unified_router(self) -> APIRouter:
        """Cria router unificado com todos os sub-routers."""
        unified_router = APIRouter()

        # Adicionar routers dos sistemas
        for name, router in self.routers.items():
            unified_router.include_router(router)
            logger.info(f"Router '{name}' incluído no router unificado")

        # Adicionar rotas de informações do gateway
        self._add_gateway_info_routes(unified_router)

        return unified_router

    def _add_gateway_info_routes(self, router: APIRouter):
        """Adiciona rotas de informações do gateway."""

        @router.get("/api/v1/gateway/info", tags=["gateway"])
        async def get_gateway_info():
            """Informações sobre o gateway."""
            return {
                "name": "PCS-Meta-Repo API Gateway",
                "version": "1.0.0",
                "config": {
                    "security_level": self.config.security.level.value,
                    "active_middlewares": self.config.active_middlewares,
                    "cors_enabled": self.config.cors.enabled,
                    "rate_limit_enabled": self.config.rate_limit.enabled,
                },
                "systems": list(self.routers.keys()),
                "total_routes": len(self.route_metadata),
            }

        @router.get("/api/v1/gateway/routes", tags=["gateway"])
        async def list_gateway_routes(system: Optional[str] = None):
            """Lista todas as rotas do gateway."""
            return {
                "routes": self.list_routes(system),
                "total": len(self.route_metadata),
                "systems": list(
                    set(metadata.system for metadata in self.route_metadata.values())
                ),
            }

        @router.get("/api/v1/gateway/health", tags=["gateway"])
        async def gateway_health():
            """Status de saúde do gateway."""
            return {
                "status": "healthy",
                "routers": {name: "active" for name in self.routers.keys()},
                "config_loaded": True,
                "middlewares_active": len(self.config.active_middlewares),
            }


class RouteValidator:
    """Validador de rotas."""

    def __init__(self, config: Optional[GatewayConfig] = None):
        self.config = config or get_gateway_config()

    def validate_route_path(self, path: str) -> bool:
        """Valida formato do path da rota."""
        if not path.startswith("/"):
            return False

        # Verificar caracteres não permitidos
        forbidden_chars = ["<", ">", ":", '"', "|", "?", "*"]
        return not any(char in path for char in forbidden_chars)

    def validate_route_methods(self, methods: List[str]) -> bool:
        """Valida métodos HTTP."""
        allowed_methods = {
            "GET",
            "POST",
            "PUT",
            "DELETE",
            "PATCH",
            "HEAD",
            "OPTIONS",
            "TRACE",
        }
        return all(method.upper() in allowed_methods for method in methods)

    def validate_router(self, router: APIRouter) -> Dict[str, Any]:
        """Valida um router completo."""
        issues = []
        route_count = 0

        for route in router.routes:
            if isinstance(route, APIRoute):
                route_count += 1

                # Validar path
                if not self.validate_route_path(route.path):
                    issues.append(f"Invalid path format: {route.path}")

                # Validar métodos
                if not self.validate_route_methods(list(route.methods)):
                    issues.append(f"Invalid methods for {route.path}: {route.methods}")

                # Verificar duplicatas
                # (implementação simples, em produção usar algoritmo mais sofisticado)

        return {"valid": len(issues) == 0, "issues": issues, "route_count": route_count}


class HealthCheckManager:
    """Gerenciador de health checks."""

    def __init__(self, router_manager: RouterManager):
        self.router_manager = router_manager
        self.health_checks: Dict[str, Callable] = {}

    def register_health_check(self, name: str, check_func: Callable):
        """Registra um health check."""
        self.health_checks[name] = check_func

    async def run_health_checks(self) -> Dict[str, Any]:
        """Executa todos os health checks."""
        results = {}
        overall_status = "healthy"

        for name, check_func in self.health_checks.items():
            try:
                result = await check_func()
                results[name] = {
                    "status": "healthy" if result else "unhealthy",
                    "details": result if isinstance(result, dict) else {},
                }

                if not result:
                    overall_status = "degraded"

            except Exception as e:
                results[name] = {"status": "error", "error": str(e)}
                overall_status = "unhealthy"

        return {
            "overall_status": overall_status,
            "checks": results,
            "timestamp": str(datetime.now()),
        }


# Factory functions
def create_router_manager(config: Optional[GatewayConfig] = None) -> RouterManager:
    """Cria gerenciador de rotas."""
    return RouterManager(config)


def create_route_validator(config: Optional[GatewayConfig] = None) -> RouteValidator:
    """Cria validador de rotas."""
    return RouteValidator(config)


def create_health_check_manager(router_manager: RouterManager) -> HealthCheckManager:
    """Cria gerenciador de health checks."""
    return HealthCheckManager(router_manager)


# Exemplo de health checks
async def check_database_connection() -> bool:
    """Health check para conexão com banco de dados."""
    # Implementação placeholder
    return True


async def check_cache_connection() -> bool:
    """Health check para conexão com cache."""
    # Implementação placeholder
    return True


async def check_external_apis() -> Dict[str, Any]:
    """Health check para APIs externas."""
    # Implementação placeholder
    return {"api1": True, "api2": True, "response_time": "150ms"}
