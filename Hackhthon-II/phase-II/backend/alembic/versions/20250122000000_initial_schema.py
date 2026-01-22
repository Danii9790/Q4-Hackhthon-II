"""Initial schema: Create users and tasks tables

Revision ID: 20250122000000
Revises:
Create Date: 2025-01-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20250122000000'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create initial database schema with users and tasks tables.

    Users table:
    - id: Primary key (string, Better Auth user ID)
    - email: Unique email address
    - name: Optional display name
    - created_at: Timestamp of account creation

    Tasks table:
    - id: Primary key (auto-increment)
    - user_id: Foreign key to users table
    - title: Task title (max 200 chars)
    - description: Optional task description (max 1000 chars)
    - completed: Boolean completion status
    - created_at: Timestamp of task creation
    - updated_at: Timestamp of last update

    Indexes:
    - Users: email (unique), id
    - Tasks: user_id, completed (for filtering), user_id+completed (composite)
    """

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('email', sa.String(), unique=True, nullable=False),
        sa.Column('password_hash', sa.String(), nullable=True),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_id', 'users', ['id'])

    # Create tasks table
    op.create_table(
        'tasks',
        sa.Column('id', sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.String(length=1000), nullable=True),
        sa.Column('completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_tasks_user_id', 'tasks', ['user_id'])
    op.create_index('ix_tasks_completed', 'tasks', ['completed'])
    op.create_index('ix_tasks_user_id_completed', 'tasks', ['user_id', 'completed'])


def downgrade() -> None:
    """
    Drop the tables in reverse order of creation.

    Tasks must be dropped first due to foreign key constraint.
    """

    # Drop tasks table
    op.drop_index('ix_tasks_user_id_completed', table_name='tasks')
    op.drop_index('ix_tasks_completed', table_name='tasks')
    op.drop_index('ix_tasks_user_id', table_name='tasks')
    op.drop_table('tasks')

    # Drop users table
    op.drop_index('ix_users_id', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
