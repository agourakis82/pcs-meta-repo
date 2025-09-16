"""
Structured logging system for PCS-HELIO MCP API.

This module provides structured logging with support for:
- JSON and console output formats
- Configurable log levels from settings
- Request/response logging middleware
- Performance timing and metrics
- Security event logging
- Error tracking and correlation
"""

import json
import logging
import sys
import time
import uuid
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Callable, Dict, Optional, Union

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .config import settings


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter for structured JSON logging.

    Formats log records as JSON with consistent structure and
    additional context fields.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        # Create base log structure
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add process/thread info
        log_entry["process_id"] = record.process
        log_entry["thread_id"] = record.thread

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add extra fields from record
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "funcName",
                "lineno",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "getMessage",
                "exc_info",
                "exc_text",
                "stack_info",
                "message",
            }:
                extra_fields[key] = value

        if extra_fields:
            log_entry["extra"] = extra_fields

        return json.dumps(log_entry)


class ConsoleFormatter(logging.Formatter):
    """
    Human-readable console formatter.

    Provides colored output and structured formatting for development.
    """

    # Color codes for different log levels
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """Format log record for console output."""
        # Add color if available
        color = self.COLORS.get(record.levelname, "")
        reset = self.RESET if color else ""

        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime(
            "%Y-%m-%d %H:%M:%S.%f"
        )[:-3]

        # Build basic message
        message = f"{color}[{timestamp}] {record.levelname:8} {record.name}: {record.getMessage()}{reset}"

        # Add extra context if present
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "funcName",
                "lineno",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "getMessage",
                "exc_info",
                "exc_text",
                "stack_info",
                "message",
            }:
                extra_fields[key] = value

        if extra_fields:
            extra_str = " ".join(f"{k}={v}" for k, v in extra_fields.items())
            message += f" | {extra_str}"

        # Add exception info
        if record.exc_info:
            message += f"\n{self.formatException(record.exc_info)}"

        return message


def configure_logging() -> None:
    """
    Configure structured logging for the application.

    Sets up formatters, handlers, and log levels based on settings.
    """
    # Determine log level
    log_level = getattr(
        logging,
        settings.ENV.upper() if hasattr(settings, "LOG_LEVEL") else "INFO",
        logging.INFO,
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    # Set formatter based on environment
    if settings.ENV.lower() == "production":
        # JSON formatter for production
        formatter = StructuredFormatter()
    else:
        # Console formatter for development
        formatter = ConsoleFormatter()

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Configure specific loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(log_level)

    # Log configuration
    logger = get_logger("logging")
    logger.info(
        "Logging configured",
        extra={
            "log_level": logging.getLevelName(log_level),
            "format": "json" if settings.ENV.lower() == "production" else "console",
            "environment": settings.ENV,
        },
    )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for comprehensive request/response logging.

    Logs HTTP requests with timing, authentication info, and performance metrics.
    """

    def __init__(
        self,
        app,
        logger_name: str = "http.access",
        log_body: bool = False,
        exempt_paths: Optional[list[str]] = None,
    ):
        super().__init__(app)
        self.logger = get_logger(logger_name)
        self.log_body = log_body
        self.exempt_paths = exempt_paths or ["/health", "/metrics"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and log comprehensive information.

        Args:
            request: Incoming request
            call_next: Next middleware/endpoint

        Returns:
            Response from next middleware/endpoint
        """
        # Generate request ID for correlation
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Skip logging for exempt paths
        if request.url.path in self.exempt_paths:
            return await call_next(request)

        # Extract request information
        start_time = time.time()
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("User-Agent", "")

        # Log request start
        request_data = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client_ip": client_ip,
            "user_agent": user_agent,
            "content_type": request.headers.get("Content-Type"),
            "content_length": request.headers.get("Content-Length"),
        }

        # Add authentication info if available
        if hasattr(request.state, "api_key"):
            request_data["authenticated"] = getattr(
                request.state, "authenticated", False
            )
            if request_data["authenticated"]:
                request_data["auth_method"] = "api_key"

        self.logger.info("Request started", extra=request_data)

        # Process request
        try:
            response = await call_next(request)

            # Calculate timing
            duration_ms = (time.time() - start_time) * 1000

            # Log successful response
            response_data = {
                "request_id": request_id,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "response_size": response.headers.get("Content-Length"),
            }

            # Add rate limiting info if available
            if "X-RateLimit-Remaining" in response.headers:
                response_data["rate_limit_remaining"] = response.headers[
                    "X-RateLimit-Remaining"
                ]

            self.logger.info("Request completed", extra=response_data)

            # Add correlation headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(round(duration_ms, 2))

            return response

        except Exception as e:
            # Log error
            duration_ms = (time.time() - start_time) * 1000

            error_data = {
                "request_id": request_id,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "duration_ms": round(duration_ms, 2),
            }

            self.logger.error("Request failed", extra=error_data)
            raise

    def _get_client_ip(self, request: Request) -> str:
        """Extract real client IP address."""
        # Check forwarded headers (proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

        # Fall back to direct client
        if request.client:
            return request.client.host

        return "unknown"


def get_logger(name: str = "api") -> logging.Logger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def log_security_event(
    event_type: str,
    request: Request,
    details: Optional[Dict[str, Any]] = None,
    level: str = "WARNING",
) -> None:
    """
    Log security-related events.

    Args:
        event_type: Type of security event
        request: Request object
        details: Additional event details
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    logger = get_logger("security")

    security_data = {
        "event_type": event_type,
        "client_ip": request.client.host if request.client else "unknown",
        "path": request.url.path,
        "method": request.method,
        "user_agent": request.headers.get("User-Agent", ""),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    if details:
        security_data.update(details)

    # Add request ID if available
    if hasattr(request.state, "request_id"):
        security_data["request_id"] = request.state.request_id

    # Log at specified level
    log_method = getattr(logger, level.lower(), logger.warning)
    log_method(f"Security event: {event_type}", extra=security_data)


def log_performance_metric(
    metric_name: str,
    value: Union[int, float],
    unit: str = "ms",
    context: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log performance metrics.

    Args:
        metric_name: Name of the metric
        value: Metric value
        unit: Unit of measurement
        context: Additional context
    """
    logger = get_logger("performance")

    metric_data = {
        "metric_name": metric_name,
        "value": value,
        "unit": unit,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

    if context:
        metric_data.update(context)

    logger.info(f"Performance metric: {metric_name}", extra=metric_data)


@contextmanager
def log_operation_time(operation_name: str, logger_name: str = "performance"):
    """
    Context manager for logging operation execution time.

    Args:
        operation_name: Name of the operation
        logger_name: Logger name to use
    """
    logger = get_logger(logger_name)
    start_time = time.time()

    try:
        yield
    finally:
        duration_ms = (time.time() - start_time) * 1000
        logger.info(
            f"Operation completed: {operation_name}",
            extra={"operation": operation_name, "duration_ms": round(duration_ms, 2)},
        )


# Configure logging on module import
configure_logging()

# Export commonly used logger
logger = get_logger("api")
