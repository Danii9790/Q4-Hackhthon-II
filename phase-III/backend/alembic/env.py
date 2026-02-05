"""
Alembic environment configuration for Todo AI Chatbot.

This file is run by Alembic to configure the migration environment.
It sets up the database connection, SQLModel metadata, and migration context.
"""

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Add src directory to Python path for imports
backend_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, backend_dir)

# Import SQLModel and database configuration
from sqlmodel import SQLModel
from src.db.session import DATABASE_URL
from src.models import User, Conversation, Message, Task

# Alembic config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set DATABASE_URL from environment variable
# This overrides sqlalchemy.url in alembic.ini
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Add your model's MetaData object here for 'autogenerate' support
# SQLModel metadata includes all table definitions
target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine,
    though an Engine is acceptable here as well. By skipping the Engine
    creation we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,  # Detect column type changes
        compare_server_default=True,  # Detect server default changes
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    In this scenario we need to create an Engine and associate a connection
    with the context.
    """
    # Use asyncpg driver for PostgreSQL
    # Convert DATABASE_URL to async format if needed
    database_url = config.get_main_option("sqlalchemy.url")

    # For async SQLAlchemy, we need to use the sync driver for migrations
    # Alembic doesn't support async migrations directly
    if database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql+asyncpg://", "postgresql+psycopg://")
        config.set_main_option("sqlalchemy.url", database_url)

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


# Determine if running in offline or online mode
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
