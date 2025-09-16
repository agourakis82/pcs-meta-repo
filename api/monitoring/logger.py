"""
Sistema H1 - Logger Estruturado

Módulo para logging estruturado com correlação de requests e métricas.
"""

import json
import logging
import time
import uuid
from contextvars import ContextVar
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Context vars para rastreamento de requests
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)


class StructuredFormatter(logging.Formatter):
    """Formatter para logs estruturados em JSON."""

    def format(self, record: logging.LogRecord) -> str:
        """Formata log record como JSON estruturado."""
        # Dados básicos do log
        log_data = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Adicionar request context se disponível
        request_id = request_id_var.get()
        if request_id:
            log_data["request_id"] = request_id

        user_id = user_id_var.get()
        if user_id:
            log_data["user_id"] = user_id

        # Adicionar dados extras do record
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        # Adicionar exception info se presente
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info),
            }

        return json.dumps(log_data)


class StructuredLogger:
    """Logger estruturado com contexto de request."""

    def __init__(self, name: str = "mcp_server"):
        self.logger = logging.getLogger(name)
        self.setup_logger()

    def setup_logger(self):
        """Configura o logger com formatters estruturados."""
        if self.logger.handlers:
            return  # Já configurado

        self.logger.setLevel(logging.INFO)

        # Handler para console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(StructuredFormatter())
        self.logger.addHandler(console_handler)

        # Handler para arquivo
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)

        file_handler = logging.FileHandler(logs_dir / "mcp_server.log")
        file_handler.setFormatter(StructuredFormatter())
        self.logger.addHandler(file_handler)

    def set_request_context(self, request_id: str, user_id: Optional[str] = None):
        """Define contexto de request para logs."""
        request_id_var.set(request_id)
        if user_id:
            user_id_var.set(user_id)

    def clear_request_context(self):
        """Limpa contexto de request."""
        request_id_var.set(None)
        user_id_var.set(None)

    def info(self, message: str, **kwargs):
        """Log info com dados extras."""
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning com dados extras."""
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log error com dados extras."""
        self._log(logging.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical com dados extras."""
        self._log(logging.CRITICAL, message, **kwargs)

    def debug(self, message: str, **kwargs):
        """Log debug com dados extras."""
        self._log(logging.DEBUG, message, **kwargs)

    def _log(self, level: int, message: str, **kwargs):
        """Log interno com dados extras."""
        extra = {"extra_fields": kwargs} if kwargs else {}
        self.logger.log(level, message, extra=extra)

    def log_request_start(
        self, method: str, path: str, user_id: Optional[str] = None, **kwargs
    ) -> str:
        """Registra início de request."""
        request_id = str(uuid.uuid4())
        self.set_request_context(request_id, user_id)

        self.info(
            "Request started",
            method=method,
            path=path,
            request_id=request_id,
            user_id=user_id,
            **kwargs,
        )

        return request_id

    def log_request_end(self, status_code: int, duration_ms: float, **kwargs):
        """Registra fim de request."""
        self.info(
            "Request completed",
            status_code=status_code,
            duration_ms=duration_ms,
            **kwargs,
        )

        self.clear_request_context()

    def log_error_with_context(self, error: Exception, operation: str, **kwargs):
        """Registra erro com contexto."""
        self.error(
            f"Error in {operation}",
            error_type=type(error).__name__,
            error_message=str(error),
            operation=operation,
            **kwargs,
            exc_info=True,
        )

    def log_metric(self, metric_name: str, value: float, unit: str = "", **kwargs):
        """Registra métrica como log."""
        self.info(
            "Metric recorded",
            metric_name=metric_name,
            metric_value=value,
            metric_unit=unit,
            **kwargs,
        )

    def log_performance(self, operation: str, duration_ms: float, **kwargs):
        """Registra métrica de performance."""
        self.info(
            "Performance metric", operation=operation, duration_ms=duration_ms, **kwargs
        )

    def log_business_event(self, event_type: str, event_data: Dict[str, Any], **kwargs):
        """Registra evento de negócio."""
        self.info(
            f"Business event: {event_type}",
            event_type=event_type,
            event_data=event_data,
            **kwargs,
        )

    def request_context(self, request_id: str, user_id: Optional[str] = None):
        """
        Context manager para request (compatibilidade).

        Args:
            request_id: ID único do request
            user_id: ID do usuário (opcional)

        Returns:
            Context manager para gerenciar contexto do request
        """
        return RequestLogger(self, "CONTEXT", f"/context/{request_id}", user_id)

    def performance_timer(self, operation: str):
        """
        Context manager para medição de performance (compatibilidade).

        Args:
            operation: Nome da operação sendo medida

        Returns:
            Context manager para medição de tempo
        """
        return PerformanceTimer(self, operation)


class RequestLogger:
    """Context manager para logging de requests."""

    def __init__(
        self,
        logger: StructuredLogger,
        method: str,
        path: str,
        user_id: Optional[str] = None,
    ):
        self.logger = logger
        self.method = method
        self.path = path
        self.user_id = user_id
        self.start_time: Optional[float] = None
        self.request_id: Optional[str] = None

    def __enter__(self):
        self.start_time = time.time()
        self.request_id = self.logger.log_request_start(
            self.method, self.path, self.user_id
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = (time.time() - self.start_time) * 1000

            if exc_type:
                # Request terminou com erro
                self.logger.log_error_with_context(
                    exc_val, f"{self.method} {self.path}", duration_ms=duration
                )
                status_code = 500
            else:
                # Request completou com sucesso
                status_code = 200

            self.logger.log_request_end(status_code, duration)


class PerformanceTimer:
    """Context manager para medição de performance."""

    def __init__(self, logger: StructuredLogger, operation: str):
        self.logger = logger
        self.operation = operation
        self.start_time: Optional[float] = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = (time.time() - self.start_time) * 1000

            if exc_type:
                self.logger.log_error_with_context(
                    exc_val, self.operation, duration_ms=duration
                )
            else:
                self.logger.log_performance(self.operation, duration)


# Instância global
_structured_logger = StructuredLogger()


def get_structured_logger() -> StructuredLogger:
    """Obtém instância global do logger estruturado."""
    return _structured_logger


def get_request_logger(
    method: str, path: str, user_id: Optional[str] = None
) -> RequestLogger:
    """Cria context manager para logging de request."""
    return RequestLogger(_structured_logger, method, path, user_id)


def get_performance_timer(operation: str) -> PerformanceTimer:
    """Cria context manager para medição de performance."""
    return PerformanceTimer(_structured_logger, operation)
