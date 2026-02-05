# Alembic Database Migrations

This directory contains Alembic database migration configuration and scripts for the Todo AI Chatbot backend.

## Overview

Alembic is a database migration tool for SQLAlchemy/SQLModel. It provides:

- Version control for database schema changes
- Automatic migration generation from model changes
- Upgrade and downgrade paths between schema versions
- Transaction-safe migration execution

## Directory Structure

```
alembic/
├── __init__.py           # Package initialization
├── env.py                # Migration environment configuration
├── script.py.mako        # Template for new migration files
└── versions/             # Migration scripts directory
    └── 20260201_initial_schema.py  # Initial schema migration
```

## Prerequisites

1. **Database URL configured**: Set `DATABASE_URL` in `.env` file
   ```bash
   DATABASE_URL=postgresql+asyncpg://user:password@host/database
   ```

2. **Dependencies installed**: Alembic is included in `pyproject.toml`

## Configuration

### alembic.ini

Main configuration file for Alembic. Key settings:

- `script_location`: Directory containing migration scripts (set to `alembic`)
- `file_template`: Naming pattern for migration files
- `sqlalchemy.url`: Database URL (overridden by `env.py` to use `DATABASE_URL` env var)

### env.py

Environment configuration that:

- Loads `DATABASE_URL` from environment variable
- Imports SQLModel metadata for autogenerate support
- Configures async engine for PostgreSQL
- Handles both online (connected) and offline (SQL script) migration modes

## Usage

### Running Migrations

**Apply all pending migrations:**
```bash
cd backend
alembic upgrade head
```

**Apply specific migration:**
```bash
alembic upgrade <revision_id>
```

**Rollback to previous version:**
```bash
alembic downgrade -1
```

**Rollback to specific version:**
```bash
alembic downgrade <revision_id>
```

**Show current migration version:**
```bash
alembic current
```

**Show migration history:**
```bash
alembic history
```

### Creating New Migrations

**Auto-generate migration from model changes:**
```bash
alembic revision --autogenerate -m "description of changes"
```

This compares current database schema against SQLModel models and generates
migration script for detected differences.

**Create empty migration template:**
```bash
alembic revision -m "description of changes"
```

Use this when you need to write custom migration SQL.

### Migration Scripts

Each migration file in `versions/` contains:

- `upgrade()`: Apply schema changes
- `downgrade()`: Reverse schema changes
- Revision identifiers for version tracking

Example:
```python
def upgrade() -> None:
    """Add new column to tasks table."""
    op.add_column('tasks', sa.Column('priority', sa.Integer(), nullable=True))

def downgrade() -> None:
    """Remove priority column from tasks table."""
    op.drop_column('tasks', 'priority')
```

## Best Practices

1. **Review auto-generated migrations**: Always check generated migrations before committing
2. **Test migrations**: Run migrations on test database before production
3. **Descriptive messages**: Use clear migration descriptions for history readability
4. **Transaction safety**: Migrations run in transactions; they either fully succeed or fail
5. **Backward compatibility**: Ensure downgrades work correctly before deploying upgrades
6. **No data loss**: Never write migrations that destroy data without explicit confirmation

## Current Schema

The initial migration (20260201_initial_schema.py) creates:

- **users**: User accounts with email and timestamps
- **conversations**: Chat sessions linked to users
- **messages**: Individual messages in conversations
- **tasks**: Todo items with title, description, completion status

All tables include:
- UUID primary keys (except tasks uses auto-increment integer)
- Foreign key constraints with CASCADE deletes
- Indexes for query performance
- Timestamp columns (created_at, updated_at)

## Troubleshooting

### Migration Conflicts

If multiple developers create migrations with the same revision ID:

```bash
# Regenerate migration with new ID
alembic revision --autogenerate -m "description" --head=<base_revision>
```

### Database URL Issues

Ensure `DATABASE_URL` is set and uses correct format:
```bash
export DATABASE_URL="postgresql+asyncpg://user:password@host:5432/database"
```

### Async Driver

Alembic uses synchronous psycopg driver for migrations even though
application uses asyncpg. This is handled automatically in `env.py`.

## References

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLModel Documentation](https://sqlmodel.tiangolo.com/)
- [Project Schema](../../specs/001-todo-ai-chatbot/data-model.md)
