#!/usr/bin/env python3
"""
Database initialization script for Todo Application.

This script creates all database tables defined in SQLModel models.
Run this script to initialize a fresh database or after adding new models.

Usage:
    python -m scripts.init_db
    OR
    python backend/scripts/init_db.py

Environment:
    Requires DATABASE_URL to be set in .env file or environment
"""
import sys
import logging
from pathlib import Path

# Add backend directory to path so we can import from src
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from src.db import init_db, engine
from src.models import User, Task  # Import models so SQLModel knows about them

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Initialize database tables."""
    try:
        logger.info("Starting database initialization...")

        # Test database connection
        with engine.connect() as conn:
            logger.info("Successfully connected to database")

        # Initialize tables
        init_db()
        logger.info("Database tables created successfully")

        # List created tables
        from sqlmodel import SQLModel
        tables = SQLModel.metadata.tables.keys()
        logger.info(f"Tables created: {', '.join(tables)}")

        return 0

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
