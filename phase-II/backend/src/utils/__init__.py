"""
Utility modules for Todo Application backend.

This package contains shared utilities and helper functions.
"""

try:
    from src.utils.logging_config import (
        get_logger,
        setup_logging,
        PerformanceTimer,
        generate_request_id,
        RequestIDFilter,
    )
except ImportError:
    # When running under Alembic, src is added to sys.path
    from utils.logging_config import (
        get_logger,
        setup_logging,
        PerformanceTimer,
        generate_request_id,
        RequestIDFilter,
    )

__all__ = [
    "get_logger",
    "setup_logging",
    "PerformanceTimer",
    "generate_request_id",
    "RequestIDFilter",
]
