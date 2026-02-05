"""Add password reset fields to users table

Revision ID: 20250122_add_password_reset
Revises: 20250122000000
Create Date: 2026-01-22
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20250122_add_password_reset'
down_revision: Union[str, None] = '20250122000000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Get the database connection and check if columns exist
    from sqlalchemy import inspect

    conn = op.get_bind()
    inspector = inspect(conn)

    # Get existing columns in users table
    existing_columns = [col['name'] for col in inspector.get_columns('users')]

    # Add reset_token column if it doesn't exist
    if 'reset_token' not in existing_columns:
        op.add_column('users', sa.Column('reset_token', sa.String(), nullable=True))

    # Add reset_token_expires column if it doesn't exist
    if 'reset_token_expires' not in existing_columns:
        op.add_column('users', sa.Column('reset_token_expires', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Remove columns
    op.drop_column('users', 'reset_token_expires')
    op.drop_column('users', 'reset_token')
