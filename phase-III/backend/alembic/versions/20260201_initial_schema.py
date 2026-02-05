"""
Initial database schema for Todo AI Chatbot.

Creates all tables: users, conversations, messages, and tasks.
Includes indexes for performance and foreign key constraints for data integrity.

Revision ID: 001
Revises: None
Create Date: 2026-02-01 13:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial database schema."""
    # Create users table
    op.create_table(
        "users",
        sa.Column(
            "id",
            sa.UUID(),
            nullable=False,
            primary_key=True,
            comment="Unique user identifier"
        ),
        sa.Column(
            "email",
            sa.String(length=255),
            nullable=False,
            comment="User's email address (unique)"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            comment="Account creation timestamp"
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            comment="Last update timestamp"
        ),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_id", "users", ["id"], unique=True)

    # Create conversations table
    op.create_table(
        "conversations",
        sa.Column(
            "id",
            sa.UUID(),
            nullable=False,
            primary_key=True,
            comment="Unique conversation identifier"
        ),
        sa.Column(
            "user_id",
            sa.UUID(),
            nullable=False,
            comment="Foreign key reference to user"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            comment="Conversation creation timestamp"
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            comment="Last message timestamp"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_conversations_user_id",
            ondelete="CASCADE"
        ),
    )
    op.create_index("ix_conversation_user_id", "conversations", ["user_id"])
    op.create_index("ix_conversations_id", "conversations", ["id"], unique=True)

    # Create messages table
    op.create_table(
        "messages",
        sa.Column(
            "id",
            sa.UUID(),
            nullable=False,
            primary_key=True,
            comment="Unique message identifier"
        ),
        sa.Column(
            "conversation_id",
            sa.UUID(),
            nullable=False,
            comment="Foreign key reference to conversation"
        ),
        sa.Column(
            "user_id",
            sa.UUID(),
            nullable=False,
            comment="Foreign key reference to user (for data isolation)"
        ),
        sa.Column(
            "role",
            sa.String(length=20),
            nullable=False,
            comment="Message role ('user' or 'assistant')"
        ),
        sa.Column(
            "content",
            sa.Text(),
            nullable=False,
            comment="Message text content"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            comment="Message creation timestamp"
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"],
            ["conversations.id"],
            name="fk_messages_conversation_id",
            ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_messages_user_id",
            ondelete="CASCADE"
        ),
    )
    op.create_index("ix_message_conversation_id", "messages", ["conversation_id"])
    op.create_index("ix_message_user_id", "messages", ["user_id"])
    op.create_index("ix_message_created_at", "messages", ["created_at"])
    op.create_index("ix_messages_id", "messages", ["id"], unique=True)

    # Create tasks table
    op.create_table(
        "tasks",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
            autoincrement=True,
            primary_key=True,
            comment="Unique task identifier (auto-incrementing)"
        ),
        sa.Column(
            "user_id",
            sa.UUID(),
            nullable=False,
            comment="Foreign key reference to user (for data isolation)"
        ),
        sa.Column(
            "title",
            sa.Text(),
            nullable=False,
            comment="Task title (required)"
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
            comment="Optional detailed task description"
        ),
        sa.Column(
            "completed",
            sa.Boolean(),
            nullable=False,
            default=False,
            comment="Task completion status"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            comment="Task creation timestamp"
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            comment="Last update timestamp"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_tasks_user_id",
            ondelete="CASCADE"
        ),
    )
    op.create_index("ix_task_user_id", "tasks", ["user_id"])
    op.create_index("ix_task_completed", "tasks", ["completed"])
    op.create_index("ix_task_user_completed", "tasks", ["user_id", "completed"])
    op.create_index("ix_tasks_id", "tasks", ["id"], unique=True)


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table("tasks")
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("users")
