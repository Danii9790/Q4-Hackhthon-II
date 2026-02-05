"""
Database session and connection management for Todo AI Chatbot.

Provides database connection pooling, session creation, and initialization.
Uses SQLAlchemy async engine with SQLModel ORM.

Implements T078: Database query logging with performance monitoring.
"""

import os
import time
from typing import Any, AsyncGenerator

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Import SQLModel metadata for Alembic migrations
from sqlmodel import SQLModel

from src.models import User, Conversation, Message, Task
from src.utils.logging_config import get_logger, PerformanceTimer, SLOW_QUERY_THRESHOLD_MS


# ============================================================================
# Logger Setup (T078)
# ============================================================================

logger = get_logger(__name__)


# ============================================================================
# Database URL and Engine Setup (T078: Query Logging)
# ============================================================================

# Database URL from environment variable
# Format: postgresql+asyncpg://user:password@host/database
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://user:password@localhost/todo_ai_chatbot"
)


# ============================================================================
# Query Logging Event Listeners (T078)
# ============================================================================

# Store query start times using context id as key
_query_start_times = {}

def _setup_query_logging(engine: AsyncSession) -> None:
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
    @event.listens_for(engine.sync_engine, "before_cursor_execute", named=True)
    def receive_before_cursor_execute(**kw):
        """Record query start time."""
        context_id = id(kw["context"])
        _query_start_times[context_id] = time.time()

    @event.listens_for(engine.sync_engine, "after_cursor_execute", named=True)
    def receive_after_cursor_execute(**kw):
        """Log query execution with timing (T078)."""
        context_id = id(kw["context"])
        query_start_time = _query_start_times.pop(context_id, None)
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

    @event.listens_for(engine.sync_engine, "connect")
    def receive_connect(dbapi_conn, connection_record):
        """Log new database connections (T078)."""
        logger.debug(
            "New database connection established",
            extra={
                "pool_status": "connection_created",
            }
        )

    @event.listens_for(engine.sync_engine, "close")
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


def _log_pool_metrics(engine: AsyncSession) -> None:
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


# Create async engine with connection pooling optimized for Neon PostgreSQL
# Performance: T080 - Connection pooling for serverless PostgreSQL
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL query logging during development
    # Connection pool settings for Neon PostgreSQL (serverless)
    pool_pre_ping=True,  # Verify connections before using them (detect stale connections)
    pool_size=10,  # Core connection pool size (10-20 recommended for Neon)
    max_overflow=20,  # Additional connections for peak load (max 30 total)
    pool_recycle=3600,  # Recycle connections after 1 hour (prevents stale connections in serverless)
)

# Setup query logging event listeners (T078)
_setup_query_logging(engine)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Prevent object expiration after commit
    autocommit=False,
    autoflush=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides a database session with logging (T078).

    Yields an async session and ensures it's closed after use.
    Logs session lifecycle events and pool metrics.

    Use with FastAPI Depends():

        @app.get("/tasks")
        async def list_tasks(session: AsyncSession = Depends(get_session)):
            ...

    Yields:
        AsyncSession: SQLAlchemy async session
    """
    async with AsyncSessionLocal() as session:
        try:
            logger.debug("Database session acquired")
            yield session
        finally:
            await session.close()
            logger.debug("Database session released")

            # Log pool metrics periodically (every 10 sessions)
            # This helps monitor connection pool health (T078)
            pool = engine.pool
            if pool.checkedout() == 0:  # Log when pool is idle
                _log_pool_metrics(engine)


async def init_db() -> None:
    """
    Initialize database by creating all tables.

    This function creates all tables defined in SQLModel metadata.
    Use this for development/testing. For production, use Alembic migrations.

    Note: This uses async engine which requires SQLModel 0.0.14+.

    Logs initialization progress (T078).
    """
    logger.info("Initializing database schema...")

    async with engine.begin() as conn:
        # Create all tables (use Alembic for production schema changes)
        await conn.run_sync(SQLModel.metadata.create_all)

    # Log pool metrics after initialization (T078)
    _log_pool_metrics(engine)

    logger.info("Database schema initialized successfully")


async def close_db() -> None:
    """
    Close all database connections.

    Call this during application shutdown to gracefully close connections.

    Logs connection closure and final pool metrics (T078).
    """
    logger.info("Closing database connections...")

    # Log final pool metrics before closing (T078)
    _log_pool_metrics(engine)

    await engine.dispose()

    logger.info("Database connections closed")


__all__ = [
    "get_session",
    "init_db",
    "close_db",
    "engine",
    "AsyncSessionLocal",
]
