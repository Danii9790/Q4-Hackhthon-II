"""
Database initialization utilities for Todo AI Chatbot.

Provides functions to verify database connectivity and initialize schema.
"""

import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import SQLModel

from src.models import Conversation, Message, Task, User

# Configure logging
logger = logging.getLogger(__name__)


async def verify_database_connection(engine: AsyncEngine) -> bool:
    """
    Verify that the database connection is working.

    Attempts to connect to the database and execute a simple query.
    Logs the result and returns a boolean indicating success.

    Args:
        engine: SQLAlchemy async engine

    Returns:
        bool: True if connection successful, False otherwise

    Example:
        >>> from src.db.session import engine
        >>> is_connected = await verify_database_connection(engine)
        >>> if is_connected:
        ...     print("Database is reachable")
    """
    try:
        async with engine.connect() as conn:
            # Execute a simple query to verify connection
            await conn.execute("SELECT 1")

        logger.info("Database connection verified successfully")
        return True

    except SQLAlchemyError as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False

    except Exception as e:
        logger.error(f"Unexpected error during database verification: {str(e)}")
        return False


async def initialize_database_schema(engine: AsyncEngine) -> bool:
    """
    Initialize database schema by creating all tables.

    This function creates all tables defined in SQLModel metadata.
    Use this for development/testing. For production, use Alembic migrations.

    The function will:
    1. Create all tables if they don't exist
    2. Log the creation process
    3. Handle any database errors gracefully

    Args:
        engine: SQLAlchemy async engine

    Returns:
        bool: True if initialization successful, False otherwise

    Example:
        >>> from src.db.session import engine
        >>> success = await initialize_database_schema(engine)
        >>> if success:
        ...     print("Database schema initialized")
    """
    try:
        async with engine.begin() as conn:
            # Create all tables from SQLModel metadata
            # This will not overwrite existing tables
            await conn.run_sync(SQLModel.metadata.create_all)

        logger.info("Database schema initialized successfully")
        logger.info(f"Created tables: {', '.join(SQLModel.metadata.tables.keys())}")
        return True

    except SQLAlchemyError as e:
        logger.error(f"Database schema initialization failed: {str(e)}")
        return False

    except Exception as e:
        logger.error(f"Unexpected error during schema initialization: {str(e)}")
        return False


async def init_db(engine: AsyncEngine) -> bool:
    """
    Complete database initialization workflow.

    This function combines connection verification and schema initialization
    into a single workflow. It will:
    1. Verify database connectivity
    2. Initialize schema if connection is successful
    3. Return False if either step fails

    Args:
        engine: SQLAlchemy async engine

    Returns:
        bool: True if both steps successful, False otherwise

    Example:
        >>> from src.db.session import engine
        >>> success = await init_db(engine)
        >>> if not success:
        ...     print("Failed to initialize database")
    """
    logger.info("Starting database initialization...")

    # Step 1: Verify connection
    if not await verify_database_connection(engine):
        logger.error("Cannot proceed with schema initialization: connection failed")
        return False

    # Step 2: Initialize schema
    if not await initialize_database_schema(engine):
        logger.error("Database schema initialization failed")
        return False

    logger.info("Database initialization completed successfully")
    return True


__all__ = [
    "verify_database_connection",
    "initialize_database_schema",
    "init_db",
]
