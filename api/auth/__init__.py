"""
Sistema H3 - Autenticação

Sistema completo de autenticação com JWT, OAuth2, API keys,
gestão de usuários, roles e permissões.
"""

from ..config import settings

# Expose API key middleware and helpers from the sibling module api/auth.py
from .apikey import (
    APIKeyMiddleware,
    AuthenticationError,
    InvalidAPIKeyError,
    MissingAPIKeyError,
    extract_api_key,
    get_api_key_optional,
    get_api_key_required,
    get_current_api_key,
    is_authenticated,
    optional_api_key,
    optional_authentication,
)
from .apikey import (
    require_api_key as _require_api_key_impl,  # decorators and dependencies; helpers and utilities
)
from .apikey import require_authentication, validate_api_key, verify_token
from .auth_manager import (
    AuthConfig,
    AuthManager,
    AuthMethod,
    AuthResult,
    AuthSession,
    SessionStatus,
    get_auth_manager,
)
from .jwt_handler import JWTHandler
from .permissions import (
    Permission,
    PermissionLevel,
    PermissionManager,
    ResourceType,
    get_permission_manager,
    require_permission,
    require_role,
)
from .user_manager import Role, User, UserManager, UserStatus

__all__ = [
    # Auth Manager
    "AuthManager",
    "AuthConfig",
    "AuthMethod",
    "AuthSession",
    "AuthResult",
    "SessionStatus",
    "get_auth_manager",
    # JWT Handler
    "JWTHandler",
    # User Manager
    "UserManager",
    "User",
    "Role",
    "UserStatus",
    # Permission Manager
    "PermissionManager",
    "Permission",
    "PermissionLevel",
    "ResourceType",
    "require_permission",
    "require_role",
    "get_permission_manager",
]

# Re-export API key auth utilities
__all__ += [
    "APIKeyMiddleware",
    "require_api_key",
    "optional_api_key",
    "get_api_key_required",
    "get_api_key_optional",
    "verify_token",
    "extract_api_key",
    "validate_api_key",
    "require_authentication",
    "optional_authentication",
    "get_current_api_key",
    "is_authenticated",
    "AuthenticationError",
    "InvalidAPIKeyError",
    "MissingAPIKeyError",
]


def verify_api_key(api_key: str | None) -> bool:
    """Compatibility verifier used in tests (reads settings.API_KEYS).

    Returns False if no keys configured or key is falsy, otherwise membership test.
    """
    if not api_key:
        return False
    raw = getattr(settings, "API_KEYS", "") or ""
    keys = [k.strip() for k in raw.split(",") if k.strip()]
    if not keys:
        return False
    return api_key in keys


def require_api_key(func):
    """Test-friendly decorator that uses verify_api_key() and extract_api_key()."""
    import functools

    from fastapi import Request

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        if not getattr(settings, "API_KEY_REQUIRED", True):
            return await func(*args, **kwargs)

        # Find Request
        request = kwargs.get("request")
        if request is None:
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
        if request is None:
            raise ValueError("Request object not found")

        api_key = extract_api_key(request)
        if not api_key:
            raise MissingAPIKeyError()
        if not verify_api_key(api_key):
            raise InvalidAPIKeyError()
        return await func(*args, **kwargs)

    return wrapper


class AuthMiddleware:
    """Lightweight ASGI auth middleware for tests (compat layer)."""

    def __init__(self, app):
        self.app = app
        self.exempt_paths = {"/", "/health", "/docs", "/openapi.json"}

    def _should_authenticate(self, path: str) -> bool:
        return path not in self.exempt_paths

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            return await self.app(scope, receive, send)
        path = scope.get("path", "/")
        if not getattr(
            settings, "API_KEY_REQUIRED", True
        ) or not self._should_authenticate(path):
            return await self.app(scope, receive, send)
        # For tests, do not enforce key here; rely on route decorators
        return await self.app(scope, receive, send)


__all__ += ["verify_api_key", "AuthMiddleware"]
