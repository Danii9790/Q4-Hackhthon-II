"""
Database session and connection management for Todo Application.

Provides database connection pooling, session creation, and initialization.
Uses SQLAlchemy sync engine with SQLModel ORM.

Implements T078: Database query logging with performance monitoring.
"""

import os
import sys
import time
from typing import Generator, Any

from sqlalchemy import event, create_engine
from sqlalchemy.orm import sessionmaker, Session

# Import SQLModel metadata for Alembic migrations
from sqlmodel import SQLModel

# Handle imports for both normal execution and Alembic migrations
try:
    from src.models import User, Task
    from src.utils.logging_config import get_logger, PerformanceTimer, SLOW_QUERY_THRESHOLD_MS
except ImportError:
    # When running under Alembic, src is added to sys.path
    from models import User, Task
    from utils.logging_config import get_logger, PerformanceTimer, SLOW_QUERY_THRESHOLD_MS


# ============================================================================
# Logger Setup (T078)
# ============================================================================

logger = get_logger(__name__)


# ============================================================================
# Database URL and Engine Setup (T078: Query Logging)
# ============================================================================

# Database URL from environment variable
# Format: postgresql://user:password@host/database
_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@localhost/todo_ai_chatbot"
)

# For sync sessions, we use psycopg2 driver
# Replace asyncpg with psycopg2 if present
if _DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = _DATABASE_URL.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
elif _DATABASE_URL.startswith("postgresql://"):
    # Add psycopg2 driver if not specified
    DATABASE_URL = _DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://")
else:
    DATABASE_URL = _DATABASE_URL


# ============================================================================
# Query Logging Event Listeners (T078)
# ============================================================================

def _setup_query_logging(engine) -> None:
    """
    Setup SQLAlchemy event listeners for query logging (T078).

    Logs:
    - All SQL queries with execution time
    - Slow queries (>500ms) at WARNING level
    - Query parameters (sanitized)
    - Connection pool metrics

    Args:
        engine: SQLAlchemy engine instance
    """
    @event.listens_for(engine, "before_cursor_execute", named=True)
    def receive_before_cursor_execute(**kw):
        """Record query start time."""
        kw["context"]['query_start_time'] = time.time()

    @event.listens_for(engine, "after_cursor_execute", named=True)
    def receive_after_cursor_execute(**kw):
        """Log query execution with timing (T078)."""
        query_start_time = kw["context"].pop('query_start_time', None)
        if query_start_time is None:
            return

        duration_ms = (time.time() - query_start_time) * 1000

        # Extract SQL statement and parameters
        statement = kw["statement"]
        parameters = kw["parameters"]

        # Sanitize parameters (avoid logging sensitive data)
        sanitized_params = _sanitize_query_params(parameters)

        # Determine log level based on duration (T078)
        if duration_ms > SLOW_QUERY_THRESHOLD_MS:
            log_func = logger.warning
            log_message = f"Slow query detected ({duration_ms:.2f}ms)"
        else:
            log_func = logger.debug
            log_message = f"Query executed ({duration_ms:.2f}ms)"

        # Log query with context (T078)
        log_func(
            log_message,
            extra={
                "sql": str(statement)[:500],  # Truncate long queries
                "parameters": sanitized_params,
                "duration_ms": duration_ms,
                "slow_query": duration_ms > SLOW_QUERY_THRESHOLD_MS,
            }
        )

    @event.listens_for(engine, "connect")
    def receive_connect(dbapi_conn, connection_record):
        """Log new database connections (T078)."""
        logger.debug(
            "New database connection established",
            extra={
                "pool_status": "connection_created",
            }
        )

    @event.listens_for(engine, "close")
    def receive_close(dbapi_conn, connection_record):
        """Log database connection closures (T078)."""
        logger.debug(
            "Database connection closed",
            extra={
                "pool_status": "connection_closed",
            }
        )


def _sanitize_query_params(parameters: Any) -> Any:
    """
    Sanitize query parameters to avoid logging sensitive data (T078).

    Removes or redacts:
    - Passwords
    - JWT tokens
    - API keys
    - Session tokens

    Args:
        parameters: Raw query parameters

    Returns:
        Sanitized parameters safe for logging
    """
    if parameters is None:
        return None

    if isinstance(parameters, dict):
        return {
            k: "[REDACTED]" if any(
                sensitive in k.lower()
                for sensitive in ["password", "token", "secret", "api_key"]
            ) else v
            for k, v in parameters.items()
        }
    elif isinstance(parameters, (list, tuple)):
        # For positional parameters, redact if any look like sensitive data
        return [
            "[REDACTED]" if isinstance(p, str) and len(p) > 50 and any(
                sensitive in p.lower()
                for sensitive in ["bearer", "jwt", "token"]
            ) else p
            for p in parameters
        ]
    else:
        return parameters


def _log_pool_metrics(engine) -> None:
    """
    Log connection pool metrics (T078).

    Logs:
    - Pool size
    - Checked out connections
    - Overflow connections
    - Checked in connections

    Args:
        engine: SQLAlchemy engine instance
    """
    pool = engine.pool
    logger.info(
        "Database connection pool metrics",
        extra={
            "pool_size": pool.size(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "checked_in": pool.checkedin(),
        }
    )


# Create sync engine with connection pooling optimized for PostgreSQL
# Performance: T080 - Connection pooling for PostgreSQL
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL query logging during development
    # Connection pool settings for PostgreSQL
    pool_pre_ping=True,  # Verify connections before using them (detect stale connections)
    pool_size=10,  # Core connection pool size (10-20 recommended)
    max_overflow=20,  # Additional connections for peak load (max 30 total)
    pool_recycle=3600,  # Recycle connections after 1 hour (prevents stale connections)
)

# Setup query logging event listeners (T078)
_setup_query_logging(engine)

# Create sync session factory
SessionLocal = sessionmaker(
    engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,  # Prevent object expiration after commit
)


def get_session() -> Generator[Session, None, None]:
    """
    Dependency that provides a database session with logging (T078).

    Yields a sync session and ensures it's closed after use.
    Logs session lifecycle events and pool metrics.

    Use with FastAPI Depends():

        @app.get("/tasks")
        def list_tasks(session: Session = Depends(get_session)):
            ...

    Yields:
        Session: SQLAlchemy sync session
    """
    session = SessionLocal()
    try:
        logger.debug("Database session acquired")
        yield session
    finally:
        session.close()
        logger.debug("Database session released")

        # Log pool metrics periodically (every 10 sessions)
        # This helps monitor connection pool health (T078)
        pool = engine.pool
        if pool.checkedout() == 0:  # Log when pool is idle
            _log_pool_metrics(engine)


def init_db() -> None:
    """
    Initialize database by creating all tables.

    This function creates all tables defined in SQLModel metadata.
    Use this for development/testing. For production, use Alembic migrations.

    Logs initialization progress (T078).
    """
    logger.info("Initializing database schema...")

    # Create all tables (use Alembic for production schema changes)
    SQLModel.metadata.create_all(engine)

    # Log pool metrics after initialization (T078)
    _log_pool_metrics(engine)

    logger.info("Database schema initialized successfully")


def close_db() -> None:
    """
    Close all database connections.

    Call this during application shutdown to gracefully close connections.

    Logs connection closure and final pool metrics (T078).
    """
    logger.info("Closing database connections...")

    # Log final pool metrics before closing (T078)
    _log_pool_metrics(engine)

    engine.dispose()

    logger.info("Database connections closed")


__all__ = [
    "get_session",
    "init_db",
    "close_db",
    "engine",
    "SessionLocal",
]
