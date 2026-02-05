"""
Demonstration script for structured logging functionality.

Run this script to see examples of:
- JSON-formatted log output
- Request ID tracking
- Performance timing
- Error logging with context
- Sensitive data sanitization

Usage:
    python tests/test_logging_demo.py
"""

import asyncio
import time
from src.utils.logging_config import get_logger, PerformanceTimer, generate_request_id

logger = get_logger(__name__)


def demo_basic_logging():
    """Demonstrate basic structured logging."""
    print("\n=== Demo 1: Basic Logging ===\n")

    logger.info("Application started")
    logger.warning("This is a warning message")
    logger.error("This is an error message")

    # Log with extra context
    logger.info(
        "User action completed",
        extra={
            "user_id": "user-123",
            "action": "create_task",
            "task_id": 456,
            "success": True
        }
    )


def demo_request_tracking():
    """Demonstrate request ID tracking."""
    print("\n=== Demo 2: Request Tracking ===\n")

    # Simulate processing a request
    request_id = generate_request_id()

    logger.info(
        "Request received",
        extra={
            "request_id": request_id,
            "method": "POST",
            "path": "/api/chat",
            "client_ip": "192.168.1.100"
        }
    )

    logger.info(
        "Processing request",
        extra={
            "request_id": request_id,
            "step": "agent_execution"
        }
    )

    logger.info(
        "Request completed",
        extra={
            "request_id": request_id,
            "status_code": 200,
            "duration_ms": 1234.56
        }
    )


def demo_performance_timing():
    """Demonstrate performance timing."""
    print("\n=== Demo 3: Performance Timing ===\n")

    # Time a fast operation
    with PerformanceTimer(logger, "fast_operation"):
        sum(range(1000))

    # Time a slow operation
    with PerformanceTimer(logger, "slow_operation"):
        time.sleep(0.1)

    # Time with extra context
    with PerformanceTimer(
        logger,
        "database_query",
        extra={"query_type": "SELECT", "table": "tasks"}
    ):
        time.sleep(0.05)


def demo_error_logging():
    """Demonstrate error logging."""
    print("\n=== Demo 4: Error Logging ===\n")

    try:
        # Simulate an error
        raise ValueError("Something went wrong")
    except Exception as e:
        logger.error(
            "Operation failed",
            exc_info=True,
            extra={
                "operation": "process_data",
                "error_type": e.__class__.__name__,
                "user_id": "user-456"
            }
        )


def demo_sensitive_data_sanitization():
    """Demonstrate sensitive data sanitization."""
    print("\n=== Demo 5: Sensitive Data Sanitization ===\n")

    # Sensitive fields are automatically redacted
    logger.info(
        "User authentication attempt",
        extra={
            "user_id": "user-789",
            "username": "john_doe",
            "password": "secret123",  # This will be redacted
            "api_key": "sk-abc123",   # This will be redacted
        }
    )


async def demo_async_operation_logging():
    """Demonstrate logging in async operations."""
    print("\n=== Demo 6: Async Operation Logging ===\n")

    logger.info("Async operation started")

    # Simulate async work
    await asyncio.sleep(0.1)

    logger.info(
        "Async operation completed",
        extra={
            "duration_seconds": 0.1,
            "items_processed": 100
        }
    )


def demo_tool_call_logging():
    """Demonstrate tool call logging pattern."""
    print("\n=== Demo 7: Tool Call Logging ===\n")

    tool_name = "add_task"
    tool_start_time = time.time()

    try:
        # Simulate tool execution
        result = {"id": 123, "title": "Buy groceries"}
        duration_ms = (time.time() - tool_start_time) * 1000

        logger.info(
            f"Tool succeeded: {tool_name}",
            extra={
                "tool_name": tool_name,
                "task_id": result["id"],
                "title": result["title"],
                "duration_ms": duration_ms
            }
        )
    except Exception as e:
        duration_ms = (time.time() - tool_start_time) * 1000

        logger.error(
            f"Tool error: {tool_name}",
            exc_info=True,
            extra={
                "tool_name": tool_name,
                "error_type": e.__class__.__name__,
                "error_message": str(e),
                "duration_ms": duration_ms
            }
        )


def main():
    """Run all logging demonstrations."""
    print("\n" + "="*60)
    print("STRUCTURED LOGGING DEMONSTRATION")
    print("="*60)

    demo_basic_logging()
    demo_request_tracking()
    demo_performance_timing()
    demo_error_logging()
    demo_sensitive_data_sanitization()
    asyncio.run(demo_async_operation_logging())
    demo_tool_call_logging()

    print("\n" + "="*60)
    print("DEMONSTRATION COMPLETE")
    print("="*60)
    print("\nNote: All logs above are in JSON format for easy parsing.")
    print("In production, these logs can be sent to Elasticsearch, Loki, or CloudWatch.")
    print("For development, set LOG_FORMAT=TEXT in .env for human-readable logs.\n")


if __name__ == "__main__":
    main()
