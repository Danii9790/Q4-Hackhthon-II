# Logging and Monitoring Guide

This document describes the structured logging and monitoring infrastructure implemented for the Todo AI Chatbot backend (T077-T079).

## Overview

The backend implements comprehensive structured logging with:
- **JSON-formatted logs** for easy parsing by log aggregation systems
- **Request ID tracking** for log correlation across components
- **Performance metrics** for database queries, agent execution, and HTTP requests
- **Error tracking** with full context and stack traces
- **Sensitive data sanitization** to prevent credentials leakage

## Architecture

### Logging Components

1. **Core Logging Module** (`src/utils/logging_config.py`)
   - StructuredFormatter: JSON log formatter
   - TextFormatter: Human-readable formatter (development)
   - PerformanceTimer: Context manager for timing operations
   - RequestIDFilter: Adds request ID to log records

2. **HTTP Request Logging** (`src/main.py`)
   - Middleware logs all incoming requests
   - Generates unique request IDs
   - Tracks request duration and status codes
   - Logs slow requests (>3s) at WARNING level

3. **Database Query Logging** (`src/db/session.py`)
   - SQLAlchemy event listeners track all queries
   - Logs query execution time
   - Logs slow queries (>500ms) at WARNING level
   - Tracks connection pool metrics

4. **Agent Execution Logging** (`src/services/agent.py`)
   - Logs all agent runs with timing
   - Tracks tool calls with parameters and results
   - Logs tool execution failures
   - Monitors agent performance

## Configuration

### Environment Variables

Configure logging via environment variables in `.env`:

```bash
# Log Level: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO

# Log Format: JSON (production) or TEXT (development)
LOG_FORMAT=JSON

# Optional: Log to file (if set, logs go to both file and stdout)
LOG_FILE=/var/log/todo-ai-chatbot/app.log

# Log file rotation settings
LOG_FILE_MAX_BYTES=10485760  # 10MB
LOG_FILE_BACKUP_COUNT=5

# Performance thresholds
SLOW_QUERY_THRESHOLD_MS=500.0      # Database queries >500ms
SLOW_REQUEST_THRESHOLD_MS=3000.0   # HTTP requests >3s
```

### Log Levels

- **DEBUG**: Detailed diagnostic information (development)
- **INFO**: General informational messages (default)
- **WARNING**: Warning messages (slow queries/requests)
- **ERROR**: Error events with stack traces
- **CRITICAL**: Critical errors requiring immediate attention

## Log Format

### JSON Structure

All logs follow this structure:

```json
{
  "timestamp": "2026-02-02T12:34:56.789Z",
  "level": "INFO",
  "logger": "src.services.agent",
  "message": "Agent execution started",
  "request_id": "req-a1b2c3d4",
  "extra": {
    "user_id": "user-123",
    "message_length": 45,
    "message_preview": "Add a task to buy groceries"
  }
}
```

### Log Fields

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | string | ISO 8601 timestamp (UTC) |
| `level` | string | Log level (INFO, ERROR, etc.) |
| `logger` | string | Python logger name (module path) |
| `message` | string | Human-readable log message |
| `request_id` | string | Unique request ID (correlation) |
| `extra` | object | Additional context (key-value pairs) |
| `performance` | object | Timing metrics (if operation timed) |
| `error` | object | Error details (if exception occurred) |

### Performance Metrics

Operations with timing include a `performance` object:

```json
{
  "message": "database_query completed in 123.45ms",
  "performance": {
    "duration_ms": 123.45
  }
}
```

### Error Details

Exceptions include an `error` object:

```json
{
  "message": "Task creation failed",
  "error": {
    "type": "ValidationError",
    "message": "Title cannot be empty",
    "traceback": "Traceback (most recent call last)..."
  }
}
```

## Usage Examples

### Basic Logging

```python
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

# Simple log message
logger.info("Processing request")

# Log with extra context
logger.info(
    "Task created",
    extra={
        "task_id": 123,
        "user_id": "user-abc",
        "title": "Buy groceries"
    }
)

# Log error with exception
logger.error(
    "Database connection failed",
    exc_info=True,
    extra={"database": "postgres"}
)
```

### Request ID Tracking

```python
from src.utils.logging_config import get_logger, generate_request_id

logger = get_logger(__name__)
request_id = generate_request_id()

# Add request ID to all logs in this context
logger.info(
    "Processing request",
    extra={"request_id": request_id}
)
```

### Performance Timing

```python
from src.utils.logging_config import get_logger, PerformanceTimer

logger = get_logger(__name__)

# Time an operation
with PerformanceTimer(logger, "database_query"):
    result = await execute_query()

# Logs: "database_query completed in 123.45ms"

# With extra context
with PerformanceTimer(
    logger,
    "agent_execution",
    extra={"user_id": "user-123"}
):
    result = await run_agent()
```

### Tool Call Logging

```python
import time

logger = get_logger(__name__)
tool_start_time = time.time()

try:
    result = await some_tool(param1, param2)
    duration_ms = (time.time() - tool_start_time) * 1000

    logger.info(
        "Tool succeeded: add_task",
        extra={
            "tool_name": "add_task",
            "task_id": result.id,
            "duration_ms": duration_ms
        }
    )
except Exception as e:
    duration_ms = (time.time() - tool_start_time) * 1000

    logger.error(
        "Tool error: add_task",
        exc_info=True,
        extra={
            "tool_name": "add_task",
            "error_type": e.__class__.__name__,
            "duration_ms": duration_ms
        }
    )
```

## Log Correlation

### Tracking a Request End-to-End

All HTTP requests get a unique `X-Request-ID` header:

1. **Request received** (main.py middleware)
   ```json
   {
     "message": "Request started: POST /api/chat",
     "request_id": "req-a1b2c3d4",
     "extra": {
       "method": "POST",
       "path": "/api/chat",
       "client_ip": "192.168.1.100"
     }
   }
   ```

2. **Agent execution** (services/agent.py)
   ```json
   {
     "message": "Agent execution started",
     "request_id": "req-a1b2c3d4",
     "extra": {
       "user_id": "user-123",
       "message_length": 45
     }
   }
   ```

3. **Tool calls** (services/agent.py)
   ```json
   {
     "message": "Tool call executed: add_task",
     "request_id": "req-a1b2c3d4",
     "extra": {
       "tool_name": "add_task",
       "task_id": 456
     }
   }
   ```

4. **Database queries** (db/session.py)
   ```json
   {
     "message": "Query executed (45.23ms)",
     "request_id": "req-a1b2c3d4",
     "extra": {
       "sql": "INSERT INTO tasks (title, user_id) VALUES ($1, $2)",
       "duration_ms": 45.23
     }
   }
   ```

5. **Request completed** (main.py middleware)
   ```json
   {
     "message": "Request completed: POST /api/chat - 200",
     "request_id": "req-a1b2c3d4",
     "extra": {
       "status_code": 200,
       "duration_ms": 1234.56
     }
   }
   ```

## Monitoring and Alerting

### Key Metrics to Monitor

1. **Request Performance**
   - Average request duration
   - P95, P99 request duration
   - Slow request rate (>3s)

2. **Database Performance**
   - Average query duration
   - Slow query rate (>500ms)
   - Connection pool utilization

3. **Agent Performance**
   - Average agent execution time
   - Tool call success rate
   - Agent error rate

4. **Error Rates**
   - HTTP 4xx errors (client errors)
   - HTTP 5xx errors (server errors)
   - Unhandled exceptions

### Alerting Recommendations

Set up alerts for:

- **Critical**: Error rate > 5% (5min window)
- **Warning**: P95 request latency > 5s (5min window)
- **Warning**: Slow query rate > 10% (5min window)
- **Info**: Connection pool > 80% full (5min window)

## Log Aggregation

### Recommended Tools

1. **Development**
   - stdout/stderr with human-readable TEXT format
   - Tail logs: `tail -f logs/app.log`

2. **Production**
   - JSON format for log aggregation
   - **ELK Stack** (Elasticsearch, Logstash, Kibana)
   - **Grafana Loki** + Grafana
   - **CloudWatch Logs** (AWS)
   - **Datadog Logs**

### Example: Loki Query

```logql
{app="todo-ai-chatbot", level="error"}
| json
| line_format "{{.request_id}}: {{.message}}"

# Find slow requests
{app="todo-ai-chatbot"}
| json
| duration_ms > 3000

# Track user activity
{app="todo-ai-chatbot"}
| json
| sum(count_over_time({user_id="user-123"}[5m]))
```

## Sensitive Data Handling

The logging system automatically sanitizes:

- **Passwords**
- **JWT tokens**
- **API keys**
- **Session tokens**
- **Bearer tokens**

Fields matching these patterns are redacted as `[REDACTED]`.

### Example Sanitization

```python
# This will be sanitized automatically
logger.info(
    "User authenticated",
    extra={
        "user_id": "user-123",
        "token": "eyJhbGciOiJIUzI1NiIs..."  # Automatically redacted
    }
)

# Output:
# {
#   "message": "User authenticated",
#   "extra": {
#     "user_id": "user-123",
#     "token": "[REDACTED]"
#   }
# }
```

## Troubleshooting

### No Logs Appearing

1. Check `LOG_LEVEL` - set to `DEBUG` for maximum verbosity
2. Verify logging configuration is loaded
3. Check file permissions (if using `LOG_FILE`)

### Missing Request IDs

1. Ensure middleware is registered in `main.py`
2. Check that `generate_request_id()` is being called
3. Verify request is passing through middleware

### Logs Too Verbose

1. Increase `LOG_LEVEL` to `WARNING` or `ERROR`
2. Suppress specific loggers:
   ```python
   logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
   ```

### Performance Impact

Logging overhead is minimal:
- JSON formatting: <1ms per log
- File I/O: asynchronous
- No impact when `LOG_LEVEL=ERROR`

## Best Practices

1. **Use appropriate log levels**
   - DEBUG: Detailed diagnostics
   - INFO: Normal operations
   - WARNING: Performance issues
   - ERROR: Failures needing attention

2. **Include context**
   - Always add relevant `extra` fields
   - Include IDs for database entities
   - Add request IDs for correlation

3. **Log at boundaries**
   - HTTP requests/responses
   - Function entry/exit (for critical paths)
   - External API calls
   - Database queries

4. **Avoid excessive logging**
   - Don't log every loop iteration
   - Use sampling for high-frequency events
   - Aggregate metrics instead

5. **Protect sensitive data**
   - Never log passwords, tokens, or keys
   - Sanitize user input before logging
   - Use the built-in sanitization

## References

- [Python Logging Documentation](https://docs.python.org/3/library/logging.html)
- [SQLAlchemy Event System](https://docs.sqlalchemy.org/en/14/core/event.html)
- [FastAPI Middleware](https://fastapi.tiangolo.com/tutorial/middleware/)
- [OpenAI Agents SDK](https://github.com/openai/openai-agents)
