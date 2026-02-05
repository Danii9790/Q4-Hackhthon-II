"""
Structured logging configuration for Todo AI Chatbot.

Provides JSON-formatted structured logging with:
- Request ID tracking for log correlation
- Performance metrics (timing)
- Error context and stack traces
- Configurable log levels via environment
- Sensitive data sanitization

Usage:
    >>> from src.utils.logging_config import get_logger
    >>> logger = get_logger(__name__)
    >>> logger.info("Task created", extra={"task_id": 123, "user_id": "abc"})
"""

import json
import logging
import os
import sys
import time
import traceback
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Any, Dict, Optional
from uuid import uuid4

# ============================================================================
# Configuration
# ============================================================================

# Log level from environment variable (default: INFO)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

# Log format: JSON (default) or TEXT
LOG_FORMAT = os.getenv("LOG_FORMAT", "JSON").upper()

# Log file paths (optional)
LOG_FILE = os.getenv("LOG_FILE", "")
LOG_FILE_MAX_BYTES = int(os.getenv("LOG_FILE_MAX_BYTES", str(10*1024*1024)))  # 10MB
LOG_FILE_BACKUP_COUNT = int(os.getenv("LOG_FILE_BACKUP_COUNT", "5"))

# Performance logging thresholds
SLOW_QUERY_THRESHOLD_MS = float(os.getenv("SLOW_QUERY_THRESHOLD_MS", "500"))
SLOW_REQUEST_THRESHOLD_MS = float(os.getenv("SLOW_REQUEST_THRESHOLD_MS", "3000"))

# Sensitive fields to sanitize
SENSITIVE_FIELDS = {
    "password", "token", "jwt", "secret", "api_key", "authorization",
    "session_token", "refresh_token", "access_token", "Bearer"
}


# ============================================================================
# JSON Formatter
# ============================================================================

class StructuredFormatter(logging.Formatter):
    """
    JSON-formatted log formatter for structured logging.

    Outputs logs as JSON with standardized fields:
    - timestamp: ISO 8601 timestamp
    - level: Log level (INFO, ERROR, etc.)
    - logger: Logger name
    - message: Log message
    - request_id: Correlation ID for request tracking
    - extra: Additional context (user_id, task_id, etc.)
    - error: Error details (if exception occurred)
    - performance: Timing metrics (if duration_ms provided)

    Example:
        {
            "timestamp": "2026-02-02T12:34:56.789Z",
            "level": "INFO",
            "logger": "src.services.agent",
            "message": "Task created successfully",
            "request_id": "req-abc123",
            "extra": {
                "user_id": "user-123",
                "task_id": 456,
                "title": "Buy groceries"
            },
            "performance": {
                "duration_ms": 123.45
            }
        }
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Args:
            record: Python logging LogRecord

        Returns:
            str: JSON-formatted log entry
        """
        # Base log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add request ID if available
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id

        # Add extra context (excluding reserved fields)
        extra = {}
        for key, value in record.__dict__.items():
            if key not in {
                "name", "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "lineno", "funcName", "created", "msecs",
                "relativeCreated", "thread", "threadName", "processName",
                "process", "getMessage", "exc_info", "exc_text", "stack_info",
                "request_id"
            }:
                # Sanitize sensitive data
                if key.lower() in SENSITIVE_FIELDS:
                    extra[key] = "[REDACTED]"
                else:
                    extra[key] = self._sanitize_value(value)

        if extra:
            log_entry["extra"] = extra

        # Add performance metrics if duration_ms provided
        if hasattr(record, "duration_ms"):
            log_entry["performance"] = {
                "duration_ms": round(record.duration_ms, 2)
            }

        # Add exception details if present
        if record.exc_info:
            log_entry["error"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info) if record.exc_info else None
            }

        # Add stack trace if requested
        if record.stack_info:
            log_entry["stack_trace"] = self.formatStack(record.stack_info)

        return json.dumps(log_entry, default=str)

    def _sanitize_value(self, value: Any) -> Any:
        """
        Recursively sanitize sensitive data from values.

        Args:
            value: Value to sanitize

        Returns:
            Sanitized value
        """
        if isinstance(value, dict):
            return {
                k: "[REDACTED]" if k.lower() in SENSITIVE_FIELDS else self._sanitize_value(v)
                for k, v in value.items()
            }
        elif isinstance(value, list):
            return [self._sanitize_value(item) for item in value]
        elif isinstance(value, str):
            # Check for potential sensitive patterns
            for sensitive in SENSITIVE_FIELDS:
                if sensitive.lower() in value.lower():
                    return "[REDACTED]"
            return value
        else:
            return value


class TextFormatter(logging.Formatter):
    """
    Human-readable text formatter for development.

    Format: [TIMESTAMP] LEVEL [REQUEST_ID] LOGGER: MESSAGE (extra={...})
    """

    def __init__(self):
        fmt = "[%(asctime)s] %(levelname)-8s [%(request_id)s] %(name)s: %(message)s"
        super().__init__(fmt=fmt, datefmt="%Y-%m-%d %H:%M:%S")

    def format(self, record: logging.LogRecord) -> str:
        # Add request_id default if not present
        if not hasattr(record, "request_id"):
            record.request_id = "N/A"

        # Format base message
        message = super().format(record)

        # Add extra context
        extra = {}
        for key, value in record.__dict__.items():
            if key not in {
                "name", "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "lineno", "funcName", "created", "msecs",
                "relativeCreated", "thread", "threadName", "processName",
                "process", "getMessage", "exc_info", "exc_text", "stack_info",
                "request_id", "asctime", "message"
            }:
                extra[key] = value

        if extra:
            message += f" (extra={extra})"

        # Add duration if present
        if hasattr(record, "duration_ms"):
            message += f" (duration_ms={record.duration_ms:.2f})"

        return message


# ============================================================================
# Request ID Filter
# ============================================================================

class RequestIDFilter(logging.Filter):
    """
    Filter that adds request_id to all log records from a specific context.

    Usage:
        >>> logger = get_logger(__name__)
        >>> logger.addFilter(RequestIDFilter("req-abc123"))
    """

    def __init__(self, request_id: Optional[str] = None):
        super().__init__()
        self.request_id = request_id or str(uuid4())

    def filter(self, record: logging.LogRecord) -> bool:
        """Add request_id to log record."""
        record.request_id = self.request_id
        return True


# ============================================================================
# Logger Setup
# ============================================================================

def setup_logging() -> None:
    """
    Configure global logging settings for the application.

    Sets up:
    - Root logger with appropriate handlers
    - Console handler (stdout)
    - File handler (if LOG_FILE configured)
    - Log level from environment
    - Structured or text formatter based on LOG_FORMAT
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Choose formatter based on LOG_FORMAT
    if LOG_FORMAT == "JSON":
        formatter = StructuredFormatter()
    else:
        formatter = TextFormatter()

    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (if configured)
    if LOG_FILE:
        try:
            file_handler = RotatingFileHandler(
                LOG_FILE,
                maxBytes=LOG_FILE_MAX_BYTES,
                backupCount=LOG_FILE_BACKUP_COUNT,
                encoding="utf-8"
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except (IOError, OSError) as e:
            # Fallback to console if file logging fails
            root_logger.warning(f"Failed to setup file logging: {e}")

    # Suppress noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    # Log startup message
    root_logger.info(
        "Logging initialized",
        extra={
            "log_level": LOG_LEVEL,
            "log_format": LOG_FORMAT,
            "log_file": LOG_FILE or "stdout"
        }
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.

    Args:
        name: Logger name (typically __name__ of the module)

    Returns:
        logging.Logger: Configured logger instance

    Example:
        >>> from src.utils.logging_config import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing request", extra={"request_id": "abc123"})
    """
    return logging.getLogger(name)


# ============================================================================
# Performance Logging Utilities
# ============================================================================

class PerformanceTimer:
    """
    Context manager for timing operations and logging performance.

    Usage:
        >>> with PerformanceTimer(logger, "database_query"):
        ...     await execute_query()
        # Logs: "database_query completed in 123.45ms"

        >>> with PerformanceTimer(logger, "agent_execution", extra={"user_id": "123"}):
        ...     await run_agent()
        # Logs with user_id context
    """

    def __init__(
        self,
        logger: logging.Logger,
        operation_name: str,
        level: int = logging.INFO,
        extra: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize performance timer.

        Args:
            logger: Logger instance
            operation_name: Name of the operation being timed
            level: Log level (default: INFO)
            extra: Additional context to include in log
        """
        self.logger = logger
        self.operation_name = operation_name
        self.level = level
        self.extra = extra or {}
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        duration_ms = (self.end_time - self.start_time) * 1000

        # Add duration to extra context
        log_extra = {
            **self.extra,
            "operation": self.operation_name,
            "duration_ms": duration_ms
        }

        if exc_type is not None:
            # Log error if exception occurred
            log_extra["error_type"] = exc_type.__name__
            self.logger.error(
                f"{self.operation_name} failed after {duration_ms:.2f}ms",
                exc_info=True,
                extra=log_extra
            )
        else:
            # Log success
            self.logger.log(
                self.level,
                f"{self.operation_name} completed in {duration_ms:.2f}ms",
                extra=log_extra
            )

    def get_duration_ms(self) -> float:
        """Get duration in milliseconds (must be called after context exit)."""
        if self.start_time is None or self.end_time is None:
            return 0.0
        return (self.end_time - self.start_time) * 1000


# ============================================================================
# Request ID Generator
# ============================================================================

def generate_request_id() -> str:
    """
    Generate a unique request ID for log correlation.

    Returns:
        str: Unique request ID (e.g., "req-a1b2c3d4")

    Example:
        >>> request_id = generate_request_id()
        >>> logger.info("Processing request", extra={"request_id": request_id})
    """
    return f"req-{uuid4().hex[:8]}"


# ============================================================================
# Initialization
# ============================================================================

# Setup logging on module import
setup_logging()


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "get_logger",
    "setup_logging",
    "StructuredFormatter",
    "TextFormatter",
    "RequestIDFilter",
    "PerformanceTimer",
    "generate_request_id",
    "SLOW_QUERY_THRESHOLD_MS",
    "SLOW_REQUEST_THRESHOLD_MS",
]
