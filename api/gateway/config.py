"""
Sistema H3 - Configurações do Gateway

Configurações centralizadas para o API Gateway.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class SecurityLevel(Enum):
    """Níveis de segurança."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RateLimitStrategy(Enum):
    """Estratégias de rate limiting."""

    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"


@dataclass
class CORSConfig:
    """Configuração CORS."""

    allow_origins: List[str] = field(default_factory=lambda: ["*"])
    allow_methods: List[str] = field(default_factory=lambda: ["*"])
    allow_headers: List[str] = field(default_factory=lambda: ["*"])
    allow_credentials: bool = True
    expose_headers: List[str] = field(default_factory=list)
    max_age: int = 600


@dataclass
class RateLimitConfig:
    """Configuração de rate limiting."""

    enabled: bool = True
    strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst_limit: int = 10

    # Configurações por endpoint
    endpoint_limits: Dict[str, Dict[str, int]] = field(default_factory=dict)

    # Configurações por usuário/IP
    user_limits: Dict[str, Dict[str, int]] = field(default_factory=dict)
    ip_whitelist: List[str] = field(default_factory=list)
    ip_blacklist: List[str] = field(default_factory=list)


@dataclass
class SecurityConfig:
    """Configuração de segurança."""

    security_level: SecurityLevel = SecurityLevel.MEDIUM

    # JWT
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 30
    jwt_refresh_expiration_days: int = 7

    # OAuth2
    oauth2_enabled: bool = False
    oauth2_providers: Dict[str, Dict[str, str]] = field(default_factory=dict)

    # API Keys
    api_keys_enabled: bool = True
    api_key_header: str = "X-API-Key"

    # Session
    session_secret_key: str = "your-session-secret-change-in-production"
    session_cookie_name: str = "pcs_session"
    session_max_age: int = 3600

    # HTTPS
    force_https: bool = False
    ssl_cert_path: Optional[str] = None
    ssl_key_path: Optional[str] = None

    # Headers de segurança
    security_headers: Dict[str, str] = field(
        default_factory=lambda: {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
        }
    )


@dataclass
class LoggingConfig:
    """Configuração de logging."""

    enabled: bool = True
    level: str = "INFO"

    # Formato de logs
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Logs de request/response
    log_requests: bool = True
    log_responses: bool = False
    log_headers: bool = False
    log_body: bool = False

    # Arquivos de log
    log_file: Optional[str] = None
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5

    # Logs estruturados
    structured_logging: bool = True
    include_request_id: bool = True


@dataclass
class PerformanceConfig:
    """Configuração de performance."""

    # Cache
    enable_response_cache: bool = True
    cache_ttl_seconds: int = 300
    cache_max_size: int = 1000

    # Compressão
    enable_compression: bool = True
    compression_level: int = 6
    compression_minimum_size: int = 1024

    # Timeouts
    request_timeout: int = 30
    keepalive_timeout: int = 5

    # Pool de conexões
    max_connections: int = 1000
    connection_pool_size: int = 100


@dataclass
class MonitoringConfig:
    """Configuração de monitoramento."""

    enabled: bool = True

    # Métricas
    collect_metrics: bool = True
    metrics_endpoint: str = "/metrics"

    # Health check
    health_endpoint: str = "/health"
    health_check_interval: int = 30

    # Tracing
    enable_tracing: bool = False
    tracing_sample_rate: float = 0.1

    # Alertas
    enable_alerts: bool = False
    alert_thresholds: Dict[str, float] = field(
        default_factory=lambda: {
            "error_rate": 0.05,  # 5%
            "response_time_p95": 1000,  # 1s
            "memory_usage": 0.8,  # 80%
            "cpu_usage": 0.7,  # 70%
        }
    )


@dataclass
class GatewayConfig:
    """Configuração principal do gateway."""

    # Servidor
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # Título e versão
    title: str = "PCS Meta Repo API Gateway"
    description: str = "Gateway unificado para todas as APIs do sistema"
    version: str = "1.0.0"

    # Prefixos de API
    api_prefix: str = "/api"
    api_version: str = "v1"

    # Configurações específicas
    cors: CORSConfig = field(default_factory=CORSConfig)
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)

    # Rotas customizadas
    custom_routes: Dict[str, str] = field(default_factory=dict)

    # Middlewares ativos
    active_middlewares: List[str] = field(
        default_factory=lambda: [
            "cors",
            "security",
            "rate_limit",
            "logging",
            "authentication",
        ]
    )

    def get_full_api_prefix(self) -> str:
        """Retorna prefixo completo da API."""
        return f"{self.api_prefix}/{self.api_version}"

    def is_development(self) -> bool:
        """Verifica se está em modo desenvolvimento."""
        return self.debug

    def is_production(self) -> bool:
        """Verifica se está em modo produção."""
        return not self.debug and self.security.force_https

    def get_cors_origins(self) -> List[str]:
        """Retorna origens CORS permitidas."""
        if self.is_development():
            return ["*"]
        return self.cors.allow_origins

    def get_rate_limit_for_endpoint(self, endpoint: str) -> Dict[str, int]:
        """Retorna limites específicos para um endpoint."""
        return self.rate_limit.endpoint_limits.get(
            endpoint,
            {
                "requests_per_minute": self.rate_limit.requests_per_minute,
                "requests_per_hour": self.rate_limit.requests_per_hour,
                "requests_per_day": self.rate_limit.requests_per_day,
            },
        )

    def should_log_requests(self) -> bool:
        """Determina se deve logar requests."""
        return self.logging.enabled and self.logging.log_requests

    def get_security_headers(self) -> Dict[str, str]:
        """Retorna headers de segurança baseados no nível."""
        headers = self.security.security_headers.copy()

        if self.security.security_level == SecurityLevel.CRITICAL:
            headers.update(
                {
                    "Content-Security-Policy": "default-src 'self'",
                    "X-Permitted-Cross-Domain-Policies": "none",
                }
            )
        elif self.security.security_level == SecurityLevel.HIGH:
            headers.update(
                {"Content-Security-Policy": "default-src 'self' 'unsafe-inline'"}
            )

        return headers


# Instância global
_gateway_config: Optional[GatewayConfig] = None


def get_gateway_config() -> GatewayConfig:
    """Obtém configuração global do gateway."""
    global _gateway_config

    if _gateway_config is None:
        _gateway_config = GatewayConfig()

    return _gateway_config


def set_gateway_config(config: GatewayConfig):
    """Define configuração global do gateway."""
    global _gateway_config
    _gateway_config = config


def reset_gateway_config():
    """Reseta configuração (para testes)."""
    global _gateway_config
    _gateway_config = None
