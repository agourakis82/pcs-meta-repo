"""
Request validation models for PCS-HELIO MCP API.

This module provides comprehensive request validation with:
- Pydantic models for all API endpoints
- Field validation and constraints
- Custom validators for complex data types
- Response models for API consistency
- Query parameter validation
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field
from pydantic.types import PositiveInt, StrictStr


class APIKeyScope(str, Enum):
    """API key permission scopes."""

    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    ALL = "all"


class SortOrder(str, Enum):
    """Sort order options."""

    ASC = "asc"
    DESC = "desc"


class LogLevel(str, Enum):
    """Log level options."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class BaseRequest(BaseModel):
    """Base request model with common fields."""

    model_config = {
        "extra": "forbid",  # Forbid extra fields
        "str_strip_whitespace": True,  # Strip whitespace from strings
        "validate_assignment": True,  # Validate on assignment
    }


class BaseResponse(BaseModel):
    """Base response model with common fields."""

    success: bool = Field(description="Request success status")
    timestamp: str = Field(description="Response timestamp")
    request_id: Optional[str] = Field(
        default=None, description="Request correlation ID"
    )

    model_config = {"str_strip_whitespace": True}


class PaginationParams(BaseRequest):
    """Pagination parameters for list endpoints."""

    limit: Optional[PositiveInt] = Field(
        default=50, le=1000, description="Maximum number of items to return"
    )
    offset: Optional[int] = Field(
        default=0, ge=0, description="Number of items to skip"
    )


class SortingParams(BaseRequest):
    """Sorting parameters for list endpoints."""

    sort_by: Optional[StrictStr] = Field(default=None, description="Field to sort by")
    sort_order: SortOrder = Field(default=SortOrder.ASC, description="Sort order")


class HealthCheckResponse(BaseResponse):
    """Health check endpoint response."""

    status: Literal["healthy", "unhealthy"] = Field(description="Health status")
    version: str = Field(description="API version")
    uptime_seconds: float = Field(description="Server uptime in seconds")
    checks: Dict[str, bool] = Field(description="Individual health checks")


class SystemStatus(BaseModel):
    """System status information."""

    cpu_percent: float = Field(description="CPU usage percentage")
    memory_percent: float = Field(description="Memory usage percentage")
    disk_percent: float = Field(description="Disk usage percentage")
    load_average: Optional[List[float]] = Field(description="System load average")


class StatusResponse(BaseResponse):
    """Status endpoint response."""

    status: Literal["running", "maintenance", "error"] = Field(
        description="Service status"
    )
    system: SystemStatus = Field(description="System metrics")
    active_connections: int = Field(description="Number of active connections")
    rate_limits: Dict[str, Any] = Field(description="Rate limiting status")


class APIInfo(BaseModel):
    """API information."""

    name: str = Field(description="API name")
    version: str = Field(description="API version")
    description: str = Field(description="API description")
    contact: Optional[Dict[str, str]] = Field(description="Contact information")
    license: Optional[Dict[str, str]] = Field(description="License information")


class InfoResponse(BaseResponse):
    """Info endpoint response."""

    api: APIInfo = Field(description="API information")
    endpoints: List[str] = Field(description="Available endpoints")
    authentication: Dict[str, Any] = Field(description="Authentication info")
    rate_limiting: Dict[str, Any] = Field(description="Rate limiting info")


class AuthStatusResponse(BaseResponse):
    """Authentication status response."""

    authenticated: bool = Field(description="Authentication status")
    api_key_id: Optional[str] = Field(description="API key identifier")
    scopes: List[APIKeyScope] = Field(description="Available scopes")
    rate_limit_remaining: Optional[int] = Field(description="Remaining requests")
    rate_limit_reset: Optional[datetime] = Field(description="Rate limit reset time")


class PingResponse(BaseResponse):
    """Ping endpoint response."""

    message: str = Field(default="pong", description="Ping response message")
    latency_ms: Optional[float] = Field(description="Response latency in milliseconds")


class ErrorValidationRequest(BaseRequest):
    """Request model for testing error validation."""

    required_field: StrictStr = Field(description="Required string field")
    positive_number: PositiveInt = Field(description="Must be positive integer")
    email: Optional[str] = Field(description="Optional email field")
    choice: Literal["option1", "option2", "option3"] = Field(
        description="Must be one of the choices"
    )


class BulkRequest(BaseRequest):
    """Bulk operation request."""

    items: List[Dict[str, Any]] = Field(description="List of items to process")
    operation: Literal["create", "update", "delete"] = Field(
        description="Operation type"
    )


class BulkResponse(BaseResponse):
    """Bulk operation response."""

    total: int = Field(description="Total items processed")
    successful: int = Field(description="Successfully processed items")
    failed: int = Field(description="Failed items")
    errors: List[Dict[str, Any]] = Field(description="Error details for failed items")


class SearchRequest(BaseRequest):
    """Search request with pagination and sorting."""

    # Pagination fields
    limit: Optional[PositiveInt] = Field(
        default=50, le=1000, description="Maximum number of items to return"
    )
    offset: Optional[int] = Field(
        default=0, ge=0, description="Number of items to skip"
    )

    # Sorting fields
    sort_by: Optional[StrictStr] = Field(default=None, description="Field to sort by")
    sort_order: SortOrder = Field(default=SortOrder.ASC, description="Sort order")

    # Search fields
    query: StrictStr = Field(min_length=1, max_length=1000, description="Search query")
    filters: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional filters"
    )
    fields: Optional[List[str]] = Field(
        default=None, description="Fields to include in response"
    )


class SearchResponse(BaseResponse):
    """Search response with pagination."""

    results: List[Dict[str, Any]] = Field(description="Search results")
    total: int = Field(description="Total number of results")
    page: int = Field(description="Current page number")
    pages: int = Field(description="Total number of pages")
    has_next: bool = Field(description="Whether there are more results")


class FileUploadRequest(BaseRequest):
    """File upload request validation."""

    filename: StrictStr = Field(description="Original filename")
    content_type: str = Field(description="File content type")
    size: PositiveInt = Field(
        le=10_000_000,  # 10MB limit
        description="File size in bytes",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional file metadata"
    )


class FileUploadResponse(BaseResponse):
    """File upload response."""

    file_id: str = Field(description="Unique file identifier")
    url: str = Field(description="File access URL")
    size: int = Field(description="File size in bytes")
    checksum: str = Field(description="File checksum")


class ConfigUpdateRequest(BaseRequest):
    """Configuration update request."""

    settings: Dict[str, Any] = Field(description="Configuration settings to update")


class ConfigResponse(BaseResponse):
    """Configuration response."""

    settings: Dict[str, Any] = Field(description="Current configuration settings")
    updated_at: datetime = Field(description="Last update timestamp")


class MetricsRequest(BaseRequest):
    """Metrics request parameters."""

    start_time: Optional[datetime] = Field(description="Start time for metrics")
    end_time: Optional[datetime] = Field(description="End time for metrics")
    metrics: Optional[List[str]] = Field(description="Specific metrics to retrieve")


class MetricsResponse(BaseResponse):
    """Metrics response."""

    metrics: Dict[str, Any] = Field(description="Metrics data")
    period: Dict[str, datetime] = Field(description="Time period covered")
    summary: Dict[str, float] = Field(description="Summary statistics")


# Validation helper functions
def validate_json_structure(data: Any, required_fields: List[str]) -> bool:
    """
    Validate JSON structure has required fields.

    Args:
        data: JSON data to validate
        required_fields: List of required field names

    Returns:
        True if valid, raises ValueError if not
    """
    if not isinstance(data, dict):
        raise ValueError("Data must be a JSON object")

    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise ValueError(f"Missing required fields: {missing_fields}")

    return True


def validate_string_length(
    value: str, min_length: int = 0, max_length: Optional[int] = None
) -> str:
    """
    Validate string length.

    Args:
        value: String to validate
        min_length: Minimum length
        max_length: Maximum length

    Returns:
        Validated string
    """
    if len(value) < min_length:
        raise ValueError(f"String must be at least {min_length} characters long")

    if max_length and len(value) > max_length:
        raise ValueError(f"String cannot exceed {max_length} characters")

    return value


def validate_numeric_range(
    value: Union[int, float],
    min_val: Optional[Union[int, float]] = None,
    max_val: Optional[Union[int, float]] = None,
) -> Union[int, float]:
    """
    Validate numeric value is within range.

    Args:
        value: Numeric value to validate
        min_val: Minimum value
        max_val: Maximum value

    Returns:
        Validated value
    """
    if min_val is not None and value < min_val:
        raise ValueError(f"Value must be at least {min_val}")

    if max_val is not None and value > max_val:
        raise ValueError(f"Value cannot exceed {max_val}")

    return value


def validate_email_format(email: str) -> bool:
    """
    Validate email format using regex.

    Args:
        email: Email string to validate

    Returns:
        True if valid, False otherwise
    """
    import re

    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(email_pattern, email))


def validate_pagination_params(
    limit: Optional[int] = None, offset: Optional[int] = None
) -> None:
    """Validate pagination parameters."""
    if limit is not None and (limit < 1 or limit > 1000):
        raise ValueError("Limit must be between 1 and 1000")

    if offset is not None and offset < 0:
        raise ValueError("Offset must be non-negative")
