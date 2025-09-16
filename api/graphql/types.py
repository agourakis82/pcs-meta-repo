"""
Sistema H3 - Tipos GraphQL

Definições de tipos GraphQL para todos os sistemas integrados.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import strawberry

from ..auth.user_manager import Role as AuthRole
from ..auth.user_manager import User as AuthUser
from ..auth.user_manager import UserStatus


@strawberry.enum
class UserStatusEnum(Enum):
    """Enum para status do usuário."""
    ACTIVE = "active"
    INACTIVE = "inactive" 
    SUSPENDED = "suspended"
    PENDING = "pending"


@strawberry.type
class Role:
    """Tipo GraphQL para Role."""
    id: str
    name: str
    description: str
    permissions: List[str]
    is_system: bool


@strawberry.type
class User:
    """Tipo GraphQL para User."""
    id: str
    username: str
    email: str
    first_name: str
    last_name: str
    status: UserStatusEnum
    roles: List[Role]
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]
    full_name: str
    is_active: bool


@strawberry.type
class AuthSession:
    """Tipo GraphQL para sessão de autenticação."""
    session_id: str
    user_id: str
    created_at: datetime
    last_activity: datetime
    expires_at: datetime
    status: str


@strawberry.type
class ConnectionStats:
    """Tipo GraphQL para estatísticas de conexão WebSocket."""
    active_connections: int
    authenticated_connections: int
    anonymous_connections: int
    total_rooms: int
    total_connections_ever: int
    total_messages: int


@strawberry.type
class RoomInfo:
    """Tipo GraphQL para informações de sala WebSocket."""
    room: str
    connection_count: int
    connections: List[str]


@strawberry.type
class CacheStats:
    """Tipo GraphQL para estatísticas de cache."""
    total_keys: int
    memory_usage: int
    hit_rate: float
    miss_rate: float
    operations_count: int


@strawberry.type
class MetricData:
    """Tipo GraphQL para dados de métricas."""
    name: str
    type: str
    value: float
    timestamp: datetime
    labels: Dict[str, str]


@strawberry.type
class SystemHealth:
    """Tipo GraphQL para saúde do sistema."""
    status: str
    uptime: int
    memory_usage: float
    cpu_usage: float
    disk_usage: float
    active_connections: int


@strawberry.type
class GatewayInfo:
    """Tipo GraphQL para informações do gateway."""
    name: str
    version: str
    security_level: str
    active_middlewares: List[str]
    cors_enabled: bool
    rate_limit_enabled: bool
    systems: List[str]
    total_routes: int


@strawberry.type
class RouteInfo:
    """Tipo GraphQL para informações de rota."""
    path: str
    methods: List[str]
    tags: List[str]
    description: str
    requires_auth: bool
    system: str


@strawberry.type
class ApiKey:
    """Tipo GraphQL para API Key."""
    key: str
    name: str
    user_id: str
    created_at: datetime
    expires_at: datetime
    permissions: List[str]
    last_used: Optional[datetime]


@strawberry.input
class CreateUserInput:
    """Input para criação de usuário."""
    username: str
    email: str
    password: str
    first_name: str = ""
    last_name: str = ""
    roles: List[str] = strawberry.field(default_factory=list)


@strawberry.input
class UpdateUserInput:
    """Input para atualização de usuário."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    status: Optional[UserStatusEnum] = None


@strawberry.input
class LoginInput:
    """Input para login."""
    username: str
    password: str


@strawberry.input
class CreateApiKeyInput:
    """Input para criação de API key."""
    name: str
    permissions: List[str] = strawberry.field(default_factory=list)


@strawberry.input
class CacheInput:
    """Input para operações de cache."""
    key: str
    value: str
    ttl: Optional[int] = None


@strawberry.input
class WebSocketMessageInput:
    """Input para mensagem WebSocket."""
    room: str
    message: str
    type: str = "text"


@strawberry.type
class AuthResult:
    """Resultado de autenticação."""
    success: bool
    user: Optional[User]
    access_token: Optional[str]
    refresh_token: Optional[str]
    expires_in: Optional[int]
    error: Optional[str]


@strawberry.type
class OperationResult:
    """Resultado genérico de operação."""
    success: bool
    message: str
    data: Optional[str] = None


@strawberry.type
class PaginationInfo:
    """Informações de paginação."""
    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool


@strawberry.type
class UserConnection:
    """Conexão paginada de usuários."""
    users: List[User]
    pagination: PaginationInfo


@strawberry.type
class MetricsConnection:
    """Conexão paginada de métricas."""
    metrics: List[MetricData]
    pagination: PaginationInfo


@strawberry.type
class RolePermission:
    """Permissão de role."""
    resource: str
    action: str
    description: str


@strawberry.type
class PermissionCheck:
    """Resultado de verificação de permissão."""
    user_id: str
    permission: str
    granted: bool
    reason: Optional[str] = None


# Conversores de tipos
def auth_user_to_graphql(auth_user: AuthUser) -> User:
    """Converte AuthUser para tipo GraphQL User."""
    return User(
        id=auth_user.id,
        username=auth_user.username,
        email=auth_user.email,
        first_name=auth_user.first_name,
        last_name=auth_user.last_name,
        status=UserStatusEnum(auth_user.status.value),
        roles=[auth_role_to_graphql(role) for role in auth_user.roles],
        created_at=auth_user.created_at,
        updated_at=auth_user.updated_at,
        last_login=auth_user.last_login,
        full_name=auth_user.full_name,
        is_active=auth_user.is_active
    )


def auth_role_to_graphql(auth_role: AuthRole) -> Role:
    """Converte AuthRole para tipo GraphQL Role."""
    return Role(
        id=auth_role.id,
        name=auth_role.name,
        description=auth_role.description,
        permissions=auth_role.permissions,
        is_system=auth_role.is_system
    )


def user_status_from_enum(status: UserStatusEnum) -> UserStatus:
    """Converte enum GraphQL para UserStatus."""
    return UserStatus(status.value)    return UserStatus(status.value)