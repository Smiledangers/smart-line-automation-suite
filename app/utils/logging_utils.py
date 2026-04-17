"""Logging utilities for structured logging with request ID tracking."""
import logging
import json
import uuid
from typing import Any, Dict, Optional
from datetime import datetime
from contextvars import ContextVar

# Context variable for request ID
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)


def get_request_id() -> Optional[str]:
    """Get current request ID from context."""
    return request_id_var.get()


def set_request_id(request_id: str) -> None:
    """Set request ID in context."""
    request_id_var.set(request_id)


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add request ID if available
        request_id = get_request_id()
        if request_id:
            log_data["request_id"] = request_id

        # Add extra fields
        if hasattr(record, 'extra_data'):
            log_data.update(record.extra_data)

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def setup_logging(level: str = "INFO") -> None:
    """Setup structured logging."""
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Console handler with structured formatter
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(console_handler)


def log_with_context(logger: logging.Logger, level: str, message: str, **kwargs) -> None:
    """Log with additional context."""
    extra = {"extra_data": kwargs}
    getattr(logger, level.lower())(message, extra=extra)


# Convenience functions
def log_info(logger: logging.Logger, message: str, **kwargs) -> None:
    """Log info with context."""
    log_with_context(logger, "INFO", message, **kwargs)


def log_error(logger: logging.Logger, message: str, **kwargs) -> None:
    """Log error with context."""
    log_with_context(logger, "ERROR", message, **kwargs)


def log_warning(logger: logging.Logger, message: str, **kwargs) -> None:
    """Log warning with context."""
    log_with_context(logger, "WARNING", message, **kwargs)


def log_debug(logger: logging.Logger, message: str, **kwargs) -> None:
    """Log debug with context."""
    log_with_context(logger, "DEBUG", message, **kwargs)