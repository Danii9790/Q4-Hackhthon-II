"""
Task model for Todo AI Chatbot.

Defines the task entity which represents todo items.
Tasks belong to specific users and can be created, viewed, completed,
updated, and deleted through natural language interactions.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import text
from sqlmodel import (
    Column,
    DateTime,
    Field,
    ForeignKey,
    Index,
    SQLModel,
    Text,
)
from sqlmodel import UUID as SQLUUID


class Task(SQLModel, table=True):
    """
    Task model representing todo items.

    Tasks belong to specific users and can be created, viewed, completed,
    updated, and deleted through natural language interactions.

    Attributes:
        id: Unique task identifier (auto-incrementing integer)
        user_id: Foreign key reference to user (indexed)
        title: Task title (required, max 500 characters)
        description: Optional detailed task description
        completed: Task completion status (default: False)
        created_at: Task creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "tasks"

    id: Optional[int] = Field(
        default=None,
        primary_key=True,
        description="Unique task identifier (auto-incrementing)"
    )
    user_id: UUID = Field(
        sa_column=Column(SQLUUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        description="Foreign key reference to user (for data isolation)"
    )
    title: str = Field(
        max_length=500,
        nullable=False,
        description="Task title (required, max 500 characters)"
    )
    description: Optional[str] = Field(
        default=None,
        sa_column=Column(Text),
        description="Optional detailed task description"
    )
    completed: bool = Field(
        default=False,
        index=True,
        description="Task completion status"
    )
    created_at: datetime = Field(
        default=None,
        sa_column=Column(DateTime, nullable=False, server_default=text("now()")),
        description="Task creation timestamp"
    )
    updated_at: datetime = Field(
        default=None,
        sa_column=Column(DateTime, nullable=False, server_default=text("now()")),
        description="Last update timestamp"
    )

    # Indexes for efficient task queries
    __table_args__ = (
        Index("ix_task_user_id", "user_id"),
        Index("ix_task_completed", "completed"),
        Index("ix_task_user_completed", "user_id", "completed"),
    )

    def __repr__(self) -> str:
        status = "completed" if self.completed else "pending"
        return f"<Task(id={self.id}, title={self.title}, status={status})>"
