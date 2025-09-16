"""
Authentication system for PCS-HELIO MCP API.

This module provides API key-based authentication with support for:
- Header-based authentication (Authorization: Bearer <key>)
- Query parameter authentication (?api_key=<key>)
- Middleware integration with FastAPI
- Custom exceptions for authentication errors
- Decorators for endpoint protection
"""

import logging
from functools import wraps
from typing import Any, Callable, Dict, Optional

from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer
from fastapi.security.utils import get_authorization_scheme_param
from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp

from .config import settings

# Configure module logger
logger = logging.getLogger(__name__)

# Security scheme for API key authentication
security = HTTPBearer(auto_error=False)


class AuthenticationError(HTTPException):
    """Base authentication error."""

    def __init__(self, detail: str = "Authentication required"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class InvalidAPIKeyError(AuthenticationError):
    """Invalid API key error."""

    def __init__(self, detail: str = "Invalid API key"):
        super().__init__(detail=detail)


class MissingAPIKeyError(AuthenticationError):
    """Missing API key error."""

    def __init__(self, detail: str = "API key required"):
        super().__init__(detail=detail)


def extract_api_key(request: Request) -> Optional[str]:
    """
    Extract API key from request headers or query parameters.

    Priority:
    1. Authorization header (Bearer token)
    2. Query parameter 'api_key'
    3. Query parameter 'key'

    Args:
        request: FastAPI request object

    Returns:
        API key string if found, None otherwise
    """
    # Check Authorization header
    authorization = request.headers.get("Authorization")
    if authorization:
        scheme, credentials = get_authorization_scheme_param(authorization)
        if scheme.lower() == "bearer" and credentials:
            return credentials

    # Check query parameters
    api_key = request.query_params.get("api_key")
    if api_key:
        return api_key

    key = request.query_params.get("key")
    if key:
        return key

    return None


def validate_api_key(api_key: str) -> bool:
    """
    Validate API key against configured keys.

    Args:
        api_key: API key to validate

    Returns:
        True if key is valid, False otherwise
    """
    if not api_key:
        return False

    valid_keys = settings.api_keys_list
    if not valid_keys:
        # If no keys configured, allow all requests
        return True

    return api_key in valid_keys


def require_authentication(request: Request) -> str:
    """
    Require valid API key authentication.

    Args:
        request: FastAPI request object

    Returns:
        Valid API key

    Raises:
        MissingAPIKeyError: If no API key provided
        InvalidAPIKeyError: If API key is invalid
    """
    logger.info(f"🔍 REQUIRE_AUTH called for {request.url.path}")
    print(f"🔍 REQUIRE_AUTH: API_KEY_REQUIRED={settings.API_KEY_REQUIRED}, path={request.url.path}")
    if not settings.API_KEY_REQUIRED:
        print("🔓 REQUIRE_AUTH: API_KEY_REQUIRED is False - bypassing")
        logger.info("🔓 API_KEY_REQUIRED is False - bypassing auth")
        return "bypass"

    api_key = extract_api_key(request)
    logger.info(f"🔑 Extracted API key: {'***' + api_key[-4:] if api_key else 'None'}")
    if not api_key:
        logger.warning(
            "Missing API key in request",
            extra={
                "path": request.url.path,
                "method": request.method,
                "client": request.client.host if request.client else "unknown",
            },
        )
        raise MissingAPIKeyError()

    if not validate_api_key(api_key):
        logger.warning(
            "Invalid API key attempted",
            extra={
                "path": request.url.path,
                "method": request.method,
                "client": request.client.host if request.client else "unknown",
                "api_key_prefix": api_key[:8] + "..." if len(api_key) > 8 else api_key,
            },
        )
        raise InvalidAPIKeyError()

    logger.info(f"✅ API key validated successfully for {request.url.path}")
    return api_key


def optional_authentication(request: Request) -> Optional[str]:
    """
    Optional API key authentication.

    Args:
        request: FastAPI request object

    Returns:
        Valid API key if provided and valid, None otherwise
    """
    if not settings.API_KEY_REQUIRED:
        return None

    api_key = extract_api_key(request)
    if not api_key:
        return None

    if not validate_api_key(api_key):
        logger.warning(
            "Invalid API key attempted (optional auth)",
            extra={
                "path": request.url.path,
                "method": request.method,
                "client": request.client.host if request.client else "unknown",
            },
        )
        return None

    logger.info(
        "Successful optional API key authentication",
        extra={
            "path": request.url.path,
            "method": request.method,
            "client": request.client.host if request.client else "unknown",
        },
    )

    return api_key


class APIKeyMiddleware(BaseHTTPMiddleware):
    """
    Middleware for API key authentication.

    This middleware can be configured to:
    - Require authentication for all endpoints
    - Allow bypass for specific paths
    - Log authentication attempts
    """

    def __init__(
        self, app, exempt_paths: Optional[list[str]] = None, require_auth: bool = True
    ):
        super().__init__(app)
        self.exempt_paths = exempt_paths or [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
        ]
        self.require_auth = require_auth

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and validate authentication if required.

        Args:
            request: Incoming request
            call_next: Next middleware/endpoint

        Returns:
            Response from next middleware/endpoint
        """
        print(f"🔍 MIDDLEWARE: Processing {request.method} {request.url.path}")
        
        # Skip authentication for exempt paths
        if request.url.path in self.exempt_paths:
            print(f"🔓 MIDDLEWARE: Exempt path {request.url.path}")
            return await call_next(request)

        # Skip if authentication not required globally
        print(f"🔑 MIDDLEWARE: API_KEY_REQUIRED={settings.API_KEY_REQUIRED}, require_auth={self.require_auth}")
        if not self.require_auth or not settings.API_KEY_REQUIRED:
            print("🔓 MIDDLEWARE: Auth not required - bypassing")
            return await call_next(request)

        print(f"🔐 MIDDLEWARE: AUTH REQUIRED for {request.url.path}")
        logger.info(f"🔐 AUTH REQUIRED for {request.url.path} - validating API key")
        try:
            # Validate API key
            api_key = require_authentication(request)

            # Add API key to request state for downstream use
            request.state.api_key = api_key
            request.state.authenticated = True
            logger.debug("API key validation successful")

        except AuthenticationError as e:
            # Return authentication error
            logger.warning(f"Authentication failed for {request.url.path}: {e.detail}")
            return Response(
                content=f'{{"detail": "{e.detail}"}}',
                status_code=e.status_code,
                headers=e.headers,
                media_type="application/json",
            )

        # Continue to next middleware/endpoint
        response = await call_next(request)
        return response


def require_api_key(func: Callable) -> Callable:
    """
    Decorator to require API key authentication for endpoint.

    Args:
        func: Endpoint function to protect

    Returns:
        Protected endpoint function
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        print(f"🔐 DECORATOR: Checking auth for {func.__name__}")
        # Find request object in args/kwargs
        request = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break

        if "request" in kwargs:
            request = kwargs["request"]

        if not request:
            raise ValueError("Request object not found in endpoint arguments")

        # Require authentication
        api_key = require_authentication(request)

        # Add to request state
        request.state.api_key = api_key
        request.state.authenticated = True

        # Call original function
        return await func(*args, **kwargs)

    return wrapper


def optional_api_key(func: Callable) -> Callable:
    """
    Decorator for optional API key authentication.

    Args:
        func: Endpoint function

    Returns:
        Endpoint function with optional authentication
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Find request object in args/kwargs
        request = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break

        if "request" in kwargs:
            request = kwargs["request"]

        if not request:
            raise ValueError("Request object not found in endpoint arguments")

        # Optional authentication
        api_key = optional_authentication(request)

        # Add to request state
        request.state.api_key = api_key
        request.state.authenticated = api_key is not None

        # Call original function
        return await func(*args, **kwargs)

    return wrapper


def get_current_api_key(request: Request) -> Optional[str]:
    """
    Get current API key from request state.

    Args:
        request: FastAPI request object

    Returns:
        Current API key if authenticated, None otherwise
    """
    return getattr(request.state, "api_key", None)


def is_authenticated(request: Request) -> bool:
    """
    Check if request is authenticated.

    Args:
        request: FastAPI request object

    Returns:
        True if authenticated, False otherwise
    """
    return getattr(request.state, "authenticated", False)


# Convenience functions for FastAPI dependencies
async def get_api_key_required(request: Request) -> str:
    """FastAPI dependency for required API key authentication."""
    return require_authentication(request)


async def get_api_key_optional(request: Request) -> Optional[str]:
    """FastAPI dependency for optional API key authentication."""
    return optional_authentication(request)


async def verify_token(request: Request) -> Dict[str, Any]:
    """
    FastAPI dependency for token verification.

    Returns user information if token is valid.
    For API key authentication, returns basic user info.
    """
    api_key = await get_api_key_required(request)

    # Para autenticação por API key, retorna info básica do usuário
    return {
        "sub": "api_key_user",
        "api_key": api_key,
        "authenticated": True,
        "auth_type": "api_key",
    }
