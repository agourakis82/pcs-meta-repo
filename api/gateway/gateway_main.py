"""
Sistema H3 - API Gateway Principal

Gateway central que coordena todos os sistemas e middlewares.
"""

import logging
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import GatewayConfig, get_gateway_config
from .middleware import (
    AuthenticationMiddleware,
    CompressionMiddleware,
    LoggingMiddleware,
    RateLimitMiddleware,
    SecurityMiddleware,
    create_cors_middleware,
    get_active_middlewares,
)
from .router_manager import RouterManager, create_router_manager

logger = logging.getLogger(__name__)


class APIGateway:
    """Gateway principal da API."""

    def __init__(self, config: Optional[GatewayConfig] = None):
        self.config = config or get_gateway_config()
        self.app: Optional[FastAPI] = None
        self.router_manager: Optional[RouterManager] = None
        self._initialized = False

    async def initialize(self):
        """Inicializa o gateway."""
        if self._initialized:
            return

        logger.info("Inicializando API Gateway...")

        # Criar aplicação FastAPI
        self.app = FastAPI(
            title="PCS-Meta-Repo API Gateway",
            description="Gateway unificado para todos os sistemas do PCS-Meta-Repo",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc",
            openapi_url="/openapi.json",
        )

        # Inicializar gerenciador de rotas
        self.router_manager = create_router_manager(self.config)

        # Configurar middlewares
        await self._setup_middlewares()

        # Configurar rotas
        await self._setup_routes()

        # Configurar handlers de eventos
        self._setup_event_handlers()

        self._initialized = True
        logger.info("API Gateway inicializado com sucesso")

    async def _setup_middlewares(self):
        """Configura middlewares do gateway."""
        if not self.app:
            raise RuntimeError("App não foi inicializado")

        # CORS (deve ser o primeiro)
        if self.config.cors.enabled:
            cors_middleware = create_cors_middleware(self.config)
            self.app.add_middleware(
                cors_middleware.get_middleware_class(),
                **cors_middleware.get_middleware_kwargs(),
            )
            logger.info("CORS middleware configurado")

        # Middlewares customizados
        active_middlewares = get_active_middlewares(self.config)

        for middleware_name, middleware in active_middlewares:
            # Pular CORS pois já foi configurado
            if middleware_name == "cors":
                continue

            # Adicionar middleware
            if isinstance(
                middleware,
                (
                    LoggingMiddleware,
                    SecurityMiddleware,
                    RateLimitMiddleware,
                    AuthenticationMiddleware,
                    CompressionMiddleware,
                ),
            ):
                self.app.middleware("http")(middleware)
                logger.info(f"Middleware '{middleware_name}' configurado")

    async def _setup_routes(self):
        """Configura rotas do gateway."""
        if not self.app or not self.router_manager:
            raise RuntimeError("App ou RouterManager não foram inicializados")

        # Incluir router unificado
        unified_router = self.router_manager.create_unified_router()
        self.app.include_router(unified_router)

        logger.info("Rotas configuradas com sucesso")

    def _setup_event_handlers(self):
        """Configura handlers de eventos do ciclo de vida."""
        if not self.app:
            raise RuntimeError("App não foi inicializado")

        @self.app.on_event("startup")
        async def startup_event():
            """Handler de startup."""
            logger.info("Gateway iniciando...")
            # Aqui você pode adicionar lógica de inicialização adicional
            # como conexões com banco de dados, cache, etc.

        @self.app.on_event("shutdown")
        async def shutdown_event():
            """Handler de shutdown."""
            logger.info("Gateway finalizando...")
            # Aqui você pode adicionar lógica de limpeza
            # como fechamento de conexões, etc.

    def get_app(self) -> FastAPI:
        """Retorna a instância do FastAPI."""
        if not self.app:
            raise RuntimeError("Gateway não foi inicializado")

        return self.app

    def get_router_manager(self) -> RouterManager:
        """Retorna o gerenciador de rotas."""
        if not self.router_manager:
            raise RuntimeError("RouterManager não foi inicializado")

        return self.router_manager

    async def add_custom_router(
        self, name: str, router, prefix: str = "", tags: List[str] = None
    ):
        """Adiciona um router customizado."""
        if not self.router_manager:
            raise RuntimeError("RouterManager não foi inicializado")

        self.router_manager.register_router(name, router, prefix, tags or [])

        # Re-configurar rotas se já inicializado
        if self._initialized and self.app:
            # Remover rotas antigas e adicionar novas
            # Em produção, implementar lógica mais sofisticada
            await self._setup_routes()

    def is_initialized(self) -> bool:
        """Verifica se o gateway foi inicializado."""
        return self._initialized


# Factory function
async def create_gateway(config: Optional[GatewayConfig] = None) -> APIGateway:
    """Cria e inicializa um gateway."""
    gateway = APIGateway(config)
    await gateway.initialize()
    return gateway


# Context manager para gateway
@asynccontextmanager
async def gateway_context(config: Optional[GatewayConfig] = None):
    """Context manager para uso do gateway."""
    gateway = None
    try:
        gateway = await create_gateway(config)
        yield gateway
    finally:
        # Cleanup se necessário
        if gateway:
            logger.info("Gateway context finalizado")


# Instância global do gateway (singleton)
_gateway_instance: Optional[APIGateway] = None


async def get_gateway_instance(config: Optional[GatewayConfig] = None) -> APIGateway:
    """Obtém instância singleton do gateway."""
    global _gateway_instance

    if _gateway_instance is None:
        _gateway_instance = await create_gateway(config)

    return _gateway_instance


def reset_gateway_instance():
    """Reseta a instância singleton (útil para testes)."""
    global _gateway_instance
    _gateway_instance = None


# Função para usar em aplicações
async def get_configured_app(config: Optional[GatewayConfig] = None) -> FastAPI:
    """Obtém aplicação FastAPI configurada."""
    gateway = await get_gateway_instance(config)
    return gateway.get_app()


# Health check simples
async def gateway_health_check() -> bool:
    """Health check simples do gateway."""
    try:
        gateway = await get_gateway_instance()
        return gateway.is_initialized()
    except Exception:
        return False
