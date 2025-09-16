"""
Error handling and validation system for PCS-HELIO MCP API.

This module provides comprehensive error handling with:
- Custom exception classes for different error types
- Standardized error response formats
- Request validation with Pydantic models
- Exception handlers for FastAPI
- Error logging and monitoring integration
"""

import traceback
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from fastapi import HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .config import settings
from .logging import get_logger, log_security_event

logger = get_logger("errors")


class ErrorDetail(BaseModel):
    """Individual error detail model."""

    type: str = Field(description="Error type")
    message: str = Field(description="Error message")
    field: Optional[str] = Field(
        default=None, description="Field that caused the error"
    )
    code: Optional[str] = Field(default=None, description="Error code")


class ErrorResponse(BaseModel):
    """Standardized error response model."""

    error: bool = Field(default=True, description="Indicates this is an error response")
    status_code: int = Field(description="HTTP status code")
    error_type: str = Field(description="Type of error")
    message: str = Field(description="Human-readable error message")
    details: List[ErrorDetail] = Field(
        default_factory=list, description="Detailed error information"
    )
    timestamp: str = Field(description="Error timestamp")
    request_id: Optional[str] = Field(
        default=None, description="Request correlation ID"
    )
    help: Optional[str] = Field(
        default=None, description="Help text or documentation link"
    )


class APIError(HTTPException):
    """Base API error with enhanced logging and context."""

    def __init__(
        self,
        status_code: int,
        message: str,
        error_type: str = "api_error",
        details: Optional[List[ErrorDetail]] = None,
        help_text: Optional[str] = None,
        log_level: str = "warning",
    ):
        super().__init__(status_code=status_code, detail=message)
        self.error_type = error_type
        self.details = details or []
        self.help_text = help_text
        self.log_level = log_level


class ValidationError(APIError):
    """Request validation error."""

    def __init__(
        self,
        message: str = "Request validation failed",
        details: Optional[List[ErrorDetail]] = None,
        field: Optional[str] = None,
    ):
        if field and not details:
            details = [
                ErrorDetail(type="validation_error", message=message, field=field)
            ]

        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message=message,
            error_type="validation_error",
            details=details,
            help_text="Check the request format and required fields",
        )


class AuthenticationError(APIError):
    """Authentication required or failed."""

    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message=message,
            error_type="authentication_error",
            help_text=(
                "Provide a valid API key in Authorization header " "or query parameter"
            ),
            log_level="warning",
        )


class AuthorizationError(APIError):
    """Authorization/permission denied."""

    def __init__(self, message: str = "Access denied"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            message=message,
            error_type="authorization_error",
            help_text="You don't have permission to access this resource",
            log_level="warning",
        )


class RateLimitError(APIError):
    """Rate limit exceeded."""

    def __init__(
        self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None
    ):
        details = []
        if retry_after:
            details.append(
                ErrorDetail(
                    type="rate_limit",
                    message=f"Retry after {retry_after} seconds",
                    code="retry_after",
                )
            )

        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            message=message,
            error_type="rate_limit_error",
            details=details,
            help_text="Reduce request frequency or upgrade API key limits",
            log_level="info",
        )


class NotFoundError(APIError):
    """Resource not found."""

    def __init__(self, resource: str = "Resource", resource_id: Optional[str] = None):
        message = f"{resource} not found"
        if resource_id:
            message += f": {resource_id}"

        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=message,
            error_type="not_found_error",
            help_text="Check the resource identifier and try again",
        )


class ServiceError(APIError):
    """Internal service or external dependency error."""

    def __init__(
        self,
        message: str = "Service temporarily unavailable",
        service_name: Optional[str] = None,
    ):
        if service_name:
            message = f"{service_name}: {message}"

        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            message=message,
            error_type="service_error",
            help_text="Try again later or contact support if the problem persists",
            log_level="error",
        )


class ConfigurationError(APIError):
    """Server configuration error."""

    def __init__(self, message: str = "Server configuration error"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=message,
            error_type="configuration_error",
            help_text="Contact the API administrator",
            log_level="error",
        )


def create_error_response(
    error: Union[APIError, Exception], request: Optional[Request] = None
) -> ErrorResponse:
    """
    Create standardized error response from exception.

    Args:
        error: Exception that occurred
        request: Optional request object for context

    Returns:
        Standardized error response
    """
    # Get request ID for correlation
    request_id = None
    if request and hasattr(request.state, "request_id"):
        request_id = request.state.request_id

    # Handle APIError instances
    if isinstance(error, APIError):
        return ErrorResponse(
            status_code=error.status_code,
            error_type=error.error_type,
            message=error.detail,
            details=error.details,
            timestamp=datetime.now(timezone.utc).isoformat(),
            request_id=request_id,
            help=error.help_text,
        )

    # Handle standard HTTPException
    elif isinstance(error, HTTPException):
        return ErrorResponse(
            status_code=error.status_code,
            error_type="http_error",
            message=str(error.detail),
            timestamp=datetime.now(timezone.utc).isoformat(),
            request_id=request_id,
        )

    # Handle validation errors
    elif isinstance(error, (ValidationError, RequestValidationError)):
        details = []
        if hasattr(error, "errors"):
            for err in error.errors():
                details.append(
                    ErrorDetail(
                        type="validation_error",
                        message=err.get("msg", "Validation error"),
                        field=".".join(str(x) for x in err.get("loc", [])),
                        code=err.get("type", "validation_error"),
                    )
                )

        return ErrorResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_type="validation_error",
            message="Request validation failed",
            details=details,
            timestamp=datetime.now(timezone.utc).isoformat(),
            request_id=request_id,
            help="Check the request format and required fields",
        )

    # Handle unexpected errors
    else:
        # Log unexpected errors with full traceback
        logger.error(
            "Unexpected error occurred",
            extra={
                "error_type": type(error).__name__,
                "error_message": str(error),
                "request_id": request_id,
                "traceback": traceback.format_exc(),
            },
        )

        # Return generic error in production, detailed in development
        if settings.ENV.lower() == "production":
            message = "An unexpected error occurred"
        else:
            message = f"{type(error).__name__}: {str(error)}"

        return ErrorResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_type="internal_error",
            message=message,
            timestamp=datetime.now(timezone.utc).isoformat(),
            request_id=request_id,
            help="Contact support if this problem persists",
        )


async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """
    Handle APIError exceptions with logging and standardized response.

    Args:
        request: FastAPI request object
        exc: APIError exception

    Returns:
        JSON error response
    """
    error_response = create_error_response(exc, request)

    # Log error with appropriate level
    log_data = {
        "error_type": exc.error_type,
        "status_code": exc.status_code,
        "message": exc.detail,
        "request_path": request.url.path,
        "request_method": request.method,
        "client_ip": request.client.host if request.client else "unknown",
    }

    if hasattr(request.state, "request_id"):
        log_data["request_id"] = request.state.request_id

    # Log at specified level
    log_method = getattr(logger, exc.log_level.lower(), logger.warning)
    log_method(f"API Error: {exc.error_type}", extra=log_data)

    # Log security events for auth errors
    if exc.error_type in ["authentication_error", "authorization_error"]:
        log_security_event(
            exc.error_type,
            request,
            {"status_code": exc.status_code, "message": exc.detail},
        )

    return JSONResponse(
        status_code=exc.status_code, content=error_response.model_dump()
    )


async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Handle request validation errors with detailed field information.

    Args:
        request: FastAPI request object
        exc: Validation error exception

    Returns:
        JSON error response
    """
    error_response = create_error_response(exc, request)

    logger.warning(
        "Request validation failed",
        extra={
            "request_path": request.url.path,
            "request_method": request.method,
            "validation_errors": [str(err) for err in exc.errors()],
            "client_ip": request.client.host if request.client else "unknown",
        },
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.model_dump(),
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle unexpected exceptions with logging and safe error response.

    Args:
        request: FastAPI request object
        exc: Any exception

    Returns:
        JSON error response
    """
    error_response = create_error_response(exc, request)

    # Log the full error details
    logger.error(
        "Unhandled exception occurred",
        extra={
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "request_path": request.url.path,
            "request_method": request.method,
            "client_ip": request.client.host if request.client else "unknown",
            "traceback": traceback.format_exc(),
        },
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(),
    )


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> None:
    """
    Validate that required fields are present in data.

    Args:
        data: Data dictionary to validate
        required_fields: List of required field names

    Raises:
        ValidationError: If any required fields are missing
    """
    missing_fields = [field for field in required_fields if field not in data]

    if missing_fields:
        details = [
            ErrorDetail(
                type="missing_field",
                message=f"Required field '{field}' is missing",
                field=field,
                code="required",
            )
            for field in missing_fields
        ]

        raise ValidationError(
            message=f"Missing required fields: {', '.join(missing_fields)}",
            details=details,
        )


def validate_field_types(data: Dict[str, Any], field_types: Dict[str, type]) -> None:
    """
    Validate field types in data dictionary.

    Args:
        data: Data dictionary to validate
        field_types: Dictionary mapping field names to expected types

    Raises:
        ValidationError: If any fields have incorrect types
    """
    type_errors = []

    for field, expected_type in field_types.items():
        if field in data and not isinstance(data[field], expected_type):
            type_errors.append(
                ErrorDetail(
                    type="type_error",
                    message=f"Field '{field}' must be of type {expected_type.__name__}",
                    field=field,
                    code="type_error",
                )
            )

    if type_errors:
        raise ValidationError(
            message="Field type validation failed", details=type_errors
        )


# Common validation patterns
def validate_api_key_format(api_key: str) -> None:
    """Validate API key format."""
    if not api_key or len(api_key) < 8:
        raise ValidationError(
            message="API key must be at least 8 characters long", field="api_key"
        )


def validate_pagination_params(
    limit: Optional[int] = None, offset: Optional[int] = None
) -> None:
    """Validate pagination parameters."""
    if limit is not None and (limit < 1 or limit > 1000):
        raise ValidationError(message="Limit must be between 1 and 1000", field="limit")

    if offset is not None and offset < 0:
        raise ValidationError(message="Offset must be non-negative", field="offset")
