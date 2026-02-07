"""
Alembic environment configuration for Todo Application.

This file is used by Alembic to configure the migration environment.
It provides the database connection and target metadata for migrations.
"""
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from dotenv import load_dotenv

from alembic import context

# Load environment variables from .env file
load_dotenv()

# Import database configuration and models
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))

from models import User, Task
from sqlmodel import SQLModel

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the database URL from environment variable
# Alembic needs a synchronous driver for migrations, so convert asyncpg to psycopg2
_database_url = os.environ.get('DATABASE_URL', 'postgresql://user:pass@localhost/dbname')
if _database_url.startswith('postgresql+asyncpg://'):
    _migration_url = _database_url.replace('postgresql+asyncpg://', 'postgresql+psycopg2://')
else:
    _migration_url = _database_url
config.set_main_option('sqlalchemy.url', _migration_url)

# Add your model's MetaData object here for 'autogenerate' support
target_metadata = SQLModel.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine,
    though an Engine is acceptable here as well. By skipping the Engine
    creation we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    In this scenario we need to create an Engine and associate a
    connection with the context.
    """
    from sqlalchemy import create_engine

    # Create engine directly from migration URL instead of using config section
    # This avoids KeyError: 'url' when the config section doesn't contain the URL
    connectable = create_engine(_migration_url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
