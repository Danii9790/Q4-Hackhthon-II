# Logging Quick Start Guide

## Setup

1. **Configure environment variables** (`.env`):
```bash
LOG_LEVEL=INFO          # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT=JSON         # JSON (prod) or TEXT (dev)
LOG_FILE=               # Empty for stdout only
```

2. **Import the logger**:
```python
from src.utils.logging_config import get_logger
logger = get_logger(__name__)
```

## Basic Usage

### Simple Logging
```python
logger.info("Processing request")
logger.warning("High memory usage")
logger.error("Database connection failed", exc_info=True)
```

### Logging with Context
```python
logger.info(
    "Task created",
    extra={
        "user_id": "user-123",
        "task_id": 456,
        "title": "Buy groceries"
    }
)
```

### Performance Timing
```python
from src.utils.logging_config import PerformanceTimer

with PerformanceTimer(logger, "database_query"):
    result = await execute_query()
# Logs: "database_query completed in 123.45ms"
```

### Request Tracking
```python
from src.utils.logging_config import generate_request_id

request_id = generate_request_id()  # e.g., "req-a1b2c3d4"

logger.info(
    "Request started",
    extra={
        "request_id": request_id,
        "path": "/api/chat"
    }
)
```

## Tool Call Pattern

```python
import time

tool_name = "add_task"
tool_start_time = time.time()

try:
    result = await tool_function(param1, param2)
    duration_ms = (time.time() - tool_start_time) * 1000

    logger.info(
        f"Tool succeeded: {tool_name}",
        extra={
            "tool_name": tool_name,
            "result_id": result.id,
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
            "duration_ms": duration_ms
        }
    )
```

## Log Levels

| Level | Usage | Example |
|-------|-------|---------|
| DEBUG | Detailed diagnostics | "Query execution plan: ..." |
| INFO | Normal operations | "Request completed successfully" |
| WARNING | Potential issues | "Slow query detected (>500ms)" |
| ERROR | Failures | "Database connection failed" |
| CRITICAL | Severe failures | "Cannot connect to database" |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | INFO | Minimum log level to output |
| `LOG_FORMAT` | JSON | Log format (JSON or TEXT) |
| `LOG_FILE` | "" | Optional file path for logs |
| `SLOW_QUERY_THRESHOLD_MS` | 500.0 | Slow query threshold in ms |
| `SLOW_REQUEST_THRESHOLD_MS` | 3000.0 | Slow request threshold in ms |

## Development vs Production

### Development (Human-Readable)
```bash
LOG_LEVEL=DEBUG
LOG_FORMAT=TEXT
LOG_FILE=
```

Output:
```
[2026-02-02 12:34:56] INFO     [req-abc123] src.main: Request started (extra={'method': 'POST', 'path': '/api/chat'})
```

### Production (Structured)
```bash
LOG_LEVEL=INFO
LOG_FORMAT=JSON
LOG_FILE=/var/log/app.log
```

Output:
```json
{"timestamp":"2026-02-02T12:34:56.789Z","level":"INFO","logger":"src.main","message":"Request started","request_id":"req-abc123","extra":{"method":"POST","path":"/api/chat"}}
```

## Viewing Logs

### Real-Time (Development)
```bash
tail -f logs/app.log
```

### Filter by Request ID
```bash
jq 'select(.request_id == "req-abc123")' logs/app.log
```

### Filter by User
```bash
jq 'select(.extra.user_id == "user-123")' logs/app.log
```

### Find Errors
```bash
jq 'select(.level == "ERROR")' logs/app.log
```

### Slow Requests
```bash
jq 'select(.performance.duration_ms > 3000)' logs/app.log
```

## Sensitive Data

**Automatically Redacted:**
- `password`
- `token`
- `jwt`
- `secret`
- `api_key`
- `authorization`

Example:
```python
logger.info("User login", extra={
    "user_id": "user-123",
    "password": "secret123"  # Logged as [REDACTED]
})
```

## Common Patterns

### HTTP Request Logging
```python
logger.info("Request started", extra={
    "request_id": request_id,
    "method": request.method,
    "path": request.url.path,
    "client_ip": request.client.host
})

# ... process request ...

logger.info("Request completed", extra={
    "request_id": request_id,
    "status_code": 200,
    "duration_ms": 1234.56
})
```

### Database Query Logging
```python
logger.debug("Executing query", extra={
    "sql": str(query),
    "parameters": sanitized_params
})

# ... execute query ...

logger.info("Query completed", extra={
    "sql": str(query)[:100],  # Truncate long queries
    "rows_affected": result.rowcount,
    "duration_ms": 45.23
})
```

### Agent Execution Logging
```python
logger.info("Agent execution started", extra={
    "user_id": str(user_id),
    "message_length": len(message),
    "history_length": len(history)
})

# ... run agent ...

logger.info("Agent execution completed", extra={
    "user_id": str(user_id),
    "tool_calls_count": len(tools_called),
    "duration_ms": 1234.56
})
```

## Troubleshooting

### No Logs Appearing
```bash
# Check log level
echo $LOG_LEVEL  # Should be DEBUG or INFO

# Verify logging module loaded
python -c "from src.utils.logging_config import get_logger; logger = get_logger('test'); logger.info('Test')"
```

### Logs Too Verbose
```bash
# Increase log level
export LOG_LEVEL=WARNING
```

### Missing Request IDs
```bash
# Ensure middleware is registered in main.py
# Check that generate_request_id() is being called
```

## Further Reading

- Full Documentation: `docs/LOGGING.md`
- Implementation Summary: `docs/LOGGING_IMPLEMENTATION.md`
- Demo Script: `tests/test_logging_demo.py`
