"""
Sistema H3 - Middleware do Gateway

Middlewares para autenticação, rate limiting, CORS e logging.
"""

import asyncio
import hashlib
import logging
import time
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple

from fastapi import HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware as FastAPICORSMiddleware
from starlette.responses import JSONResponse

from .config import GatewayConfig, RateLimitStrategy, get_gateway_config

logger = logging.getLogger(__name__)


class BaseMiddleware(ABC):
    """Classe base para middlewares."""

    def __init__(self, config: Optional[GatewayConfig] = None):
        self.config = config or get_gateway_config()

    @abstractmethod
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Processa request através do middleware."""
        pass


class LoggingMiddleware(BaseMiddleware):
    """Middleware para logging de requests."""

    def __init__(self, config: Optional[GatewayConfig] = None):
        super().__init__(config)
        self.logger = logging.getLogger("gateway.requests")

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Log requests e responses."""
        if not self.config.logging.enabled:
            return await call_next(request)

        # Gerar request ID
        request_id = hashlib.md5(
            f"{time.time()}{request.client.host if request.client else 'unknown'}".encode()
        ).hexdigest()[:8]

        # Adicionar request ID ao contexto
        request.state.request_id = request_id

        start_time = time.time()

        # Log do request
        if self.config.logging.log_requests:
            self._log_request(request, request_id)

        try:
            # Processar request
            response = await call_next(request)

            # Calcular tempo de processamento
            process_time = time.time() - start_time

            # Adicionar headers de debug
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)

            # Log do response
            if self.config.logging.log_responses:
                self._log_response(response, request_id, process_time)

            return response

        except Exception as e:
            process_time = time.time() - start_time
            self._log_error(request, request_id, str(e), process_time)
            raise

    def _log_request(self, request: Request, request_id: str):
        """Log detalhes do request."""
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")

        log_data = {
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "client_ip": client_ip,
            "user_agent": user_agent,
            "timestamp": datetime.now().isoformat(),
        }

        if self.config.logging.log_headers:
            log_data["headers"] = dict(request.headers)

        self.logger.info(f"Request: {log_data}")

    def _log_response(self, response: Response, request_id: str, process_time: float):
        """Log detalhes do response."""
        log_data = {
            "request_id": request_id,
            "status_code": response.status_code,
            "process_time": f"{process_time:.3f}s",
            "timestamp": datetime.now().isoformat(),
        }

        if self.config.logging.log_headers and hasattr(response, "headers"):
            log_data["headers"] = dict(response.headers)

        self.logger.info(f"Response: {log_data}")

    def _log_error(
        self, request: Request, request_id: str, error: str, process_time: float
    ):
        """Log erros."""
        log_data = {
            "request_id": request_id,
            "method": request.method,
            "url": str(request.url),
            "error": error,
            "process_time": f"{process_time:.3f}s",
            "timestamp": datetime.now().isoformat(),
        }

        self.logger.error(f"Error: {log_data}")


class SecurityMiddleware(BaseMiddleware):
    """Middleware para headers de segurança."""

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Adiciona headers de segurança."""
        response = await call_next(request)

        # Adicionar headers de segurança
        security_headers = self.config.get_security_headers()
        for header, value in security_headers.items():
            response.headers[header] = value

        return response


class RateLimitMiddleware(BaseMiddleware):
    """Middleware para rate limiting."""

    def __init__(self, config: Optional[GatewayConfig] = None):
        super().__init__(config)
        self.request_counts: Dict[str, deque[datetime]] = defaultdict(deque)
        self.blocked_ips: Dict[str, datetime] = {}
        self.lock = asyncio.Lock()

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Controla rate limiting."""
        if not self.config.rate_limit.enabled:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"

        # Verificar se IP está na whitelist
        if client_ip in self.config.rate_limit.ip_whitelist:
            return await call_next(request)

        # Verificar se IP está na blacklist
        if client_ip in self.config.rate_limit.ip_blacklist:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="IP address is blacklisted",
            )

        # Verificar se IP está temporariamente bloqueado
        if await self._is_blocked(client_ip):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Try again later.",
            )

        # Verificar rate limit
        if await self._is_rate_limited(client_ip, str(request.url.path)):
            await self._block_ip(client_ip)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={"Retry-After": "60"},
            )

        # Registrar request
        await self._record_request(client_ip)

        return await call_next(request)

    async def _is_blocked(self, client_ip: str) -> bool:
        """Verifica se IP está bloqueado."""
        async with self.lock:
            if client_ip in self.blocked_ips:
                # Verificar se bloqueio expirou
                if datetime.now() > self.blocked_ips[client_ip]:
                    del self.blocked_ips[client_ip]
                    return False
                return True
            return False

    async def _block_ip(self, client_ip: str):
        """Bloqueia IP temporariamente."""
        async with self.lock:
            # Bloquear por 5 minutos
            self.blocked_ips[client_ip] = datetime.now() + timedelta(minutes=5)

    async def _is_rate_limited(self, client_ip: str, endpoint: str) -> bool:
        """Verifica se rate limit foi excedido."""
        async with self.lock:
            now = datetime.now()

            # Obter limites para o endpoint
            limits = self.config.get_rate_limit_for_endpoint(endpoint)

            # Limpar requests antigos
            self._cleanup_old_requests(client_ip, now)

            # Verificar diferentes janelas de tempo
            recent_requests = self.request_counts[client_ip]

            # Verificar limite por minuto
            minute_ago = now - timedelta(minutes=1)
            minute_count = sum(
                1 for req_time in recent_requests if req_time >= minute_ago
            )

            if minute_count >= limits.get(
                "requests_per_minute", self.config.rate_limit.requests_per_minute
            ):
                return True

            # Verificar limite por hora
            hour_ago = now - timedelta(hours=1)
            hour_count = sum(1 for req_time in recent_requests if req_time >= hour_ago)

            if hour_count >= limits.get(
                "requests_per_hour", self.config.rate_limit.requests_per_hour
            ):
                return True

            # Verificar limite por dia
            day_ago = now - timedelta(days=1)
            day_count = sum(1 for req_time in recent_requests if req_time >= day_ago)

            if day_count >= limits.get(
                "requests_per_day", self.config.rate_limit.requests_per_day
            ):
                return True

            return False

    async def _record_request(self, client_ip: str):
        """Registra um request."""
        async with self.lock:
            self.request_counts[client_ip].append(datetime.now())

    def _cleanup_old_requests(self, client_ip: str, now: datetime):
        """Remove requests antigos da contagem."""
        # Manter apenas últimas 24 horas
        cutoff = now - timedelta(days=1)

        recent_requests = deque()
        for req_time in self.request_counts[client_ip]:
            if req_time >= cutoff:
                recent_requests.append(req_time)

        self.request_counts[client_ip] = recent_requests


class AuthenticationMiddleware(BaseMiddleware):
    """Middleware para autenticação."""

    def __init__(self, config: Optional[GatewayConfig] = None):
        super().__init__(config)
        self.public_paths = {
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/metrics",
            "/auth/login",
            "/auth/register",
        }

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Verifica autenticação."""
        # Pular autenticação para rotas públicas
        if self._is_public_path(request.url.path):
            return await call_next(request)

        # Verificar autenticação
        user = await self._authenticate_request(request)

        if not user:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Authentication required"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Adicionar usuário ao contexto
        request.state.user = user

        return await call_next(request)

    def _is_public_path(self, path: str) -> bool:
        """Verifica se path é público."""
        return any(path.startswith(public_path) for public_path in self.public_paths)

    async def _authenticate_request(self, request: Request) -> Optional[Dict[str, Any]]:
        """Autentica request."""
        # Verificar API Key
        if self.config.security.api_keys_enabled:
            api_key = request.headers.get(self.config.security.api_key_header)
            if api_key:
                return await self._validate_api_key(api_key)

        # Verificar JWT Token
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            return await self._validate_jwt_token(token)

        return None

    async def _validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Valida API key."""
        # Implementação simples - em produção usar banco de dados
        valid_keys = {
            "test-api-key": {"user_id": "test", "role": "admin"},
            "demo-api-key": {"user_id": "demo", "role": "user"},
        }

        return valid_keys.get(api_key)

    async def _validate_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Valida JWT token."""
        try:
            # Implementação simples - em produção usar JWT library
            # Por ora, aceitar qualquer token não vazio
            if token and len(token) > 10:
                return {"user_id": "jwt_user", "role": "user", "token": token}
            return None
        except Exception:
            return None


class CORSMiddleware:
    """Wrapper para CORS middleware do FastAPI."""

    def __init__(self, config: Optional[GatewayConfig] = None):
        self.config = config or get_gateway_config()

    def get_middleware_class(self):
        """Retorna classe de middleware CORS configurada."""
        return FastAPICORSMiddleware

    def get_middleware_kwargs(self) -> Dict[str, Any]:
        """Retorna argumentos para o middleware CORS."""
        cors_config = self.config.cors

        return {
            "allow_origins": self.config.get_cors_origins(),
            "allow_credentials": cors_config.allow_credentials,
            "allow_methods": cors_config.allow_methods,
            "allow_headers": cors_config.allow_headers,
            "expose_headers": cors_config.expose_headers,
            "max_age": cors_config.max_age,
        }


class CompressionMiddleware(BaseMiddleware):
    """Middleware para compressão de responses."""

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Aplica compressão se necessário."""
        response = await call_next(request)

        # Verificar se deve comprimir
        if not self.config.performance.enable_compression:
            return response

        # Verificar Accept-Encoding
        accept_encoding = request.headers.get("accept-encoding", "")
        if "gzip" not in accept_encoding.lower():
            return response

        # Verificar tamanho mínimo
        content_length = response.headers.get("content-length")
        if content_length:
            size = int(content_length)
            if size < self.config.performance.compression_minimum_size:
                return response

        # Adicionar header de compressão
        response.headers["content-encoding"] = "gzip"

        return response


# Factory functions para criar middlewares
def create_logging_middleware(
    config: Optional[GatewayConfig] = None,
) -> LoggingMiddleware:
    """Cria middleware de logging."""
    return LoggingMiddleware(config)


def create_security_middleware(
    config: Optional[GatewayConfig] = None,
) -> SecurityMiddleware:
    """Cria middleware de segurança."""
    return SecurityMiddleware(config)


def create_rate_limit_middleware(
    config: Optional[GatewayConfig] = None,
) -> RateLimitMiddleware:
    """Cria middleware de rate limiting."""
    return RateLimitMiddleware(config)


def create_auth_middleware(
    config: Optional[GatewayConfig] = None,
) -> AuthenticationMiddleware:
    """Cria middleware de autenticação."""
    return AuthenticationMiddleware(config)


def create_cors_middleware(config: Optional[GatewayConfig] = None) -> CORSMiddleware:
    """Cria middleware CORS."""
    return CORSMiddleware(config)


def create_compression_middleware(
    config: Optional[GatewayConfig] = None,
) -> CompressionMiddleware:
    """Cria middleware de compressão."""
    return CompressionMiddleware(config)


def get_active_middlewares(
    config: Optional[GatewayConfig] = None,
) -> List[Tuple[str, BaseMiddleware]]:
    """Retorna lista de middlewares ativos."""
    config = config or get_gateway_config()
    middlewares = []

    middleware_map = {
        "logging": create_logging_middleware,
        "security": create_security_middleware,
        "rate_limit": create_rate_limit_middleware,
        "authentication": create_auth_middleware,
        "compression": create_compression_middleware,
    }

    for middleware_name in config.active_middlewares:
        if middleware_name in middleware_map:
            middleware = middleware_map[middleware_name](config)
            middlewares.append((middleware_name, middleware))

    return middlewares
