"""
Database connection and session management for Todo Application.

Configured with connection pooling optimized for Neon Serverless PostgreSQL.
"""
import os
import logging
from pathlib import Path
from sqlmodel import SQLModel, create_engine, Session
from typing import Generator
from dotenv import load_dotenv

# Load environment variables before accessing them
load_dotenv()

logger = logging.getLogger(__name__)

# Database URL from environment variable (with SQLite default for development)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./todo.db"  # Default to SQLite for development
)

# Create database engine
# Use connection pooling for PostgreSQL, simple settings for SQLite
if DATABASE_URL.startswith("postgresql"):
    # PostgreSQL with connection pooling optimized for Neon Serverless
    engine = create_engine(
        DATABASE_URL,
        echo=os.getenv("DEBUG", "False").lower() == "true",
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=3600,
        pool_pre_ping=True,
    )
else:
    # SQLite (development)
    engine = create_engine(
        DATABASE_URL,
        echo=os.getenv("DEBUG", "False").lower() == "true",
        connect_args={"check_same_thread": False},
    )


def init_db() -> None:
    """
    Initialize database tables.
    This should be called on application startup.
    """
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """
    Dependency function that yields a database session.
    The session is properly closed after use.

    Yields:
        Session: SQLModel/SQLAlchemy database session
    """
    with Session(engine) as session:
        yield session
