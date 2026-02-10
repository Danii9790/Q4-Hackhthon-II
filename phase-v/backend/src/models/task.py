"""
Task model for Todo Application.
"""
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship, Column
from typing import Optional, List, Literal
from sqlalchemy import String, JSON
import uuid


# Priority as a string literal type for Pydantic
PriorityType = Literal["LOW", "MEDIUM", "HIGH"]


class Priority(str):
    """Task priority levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not isinstance(v, str) or v not in ("LOW", "MEDIUM", "HIGH"):
            raise ValueError(f"Invalid priority: {v}")
        return v

    def __repr__(self):
        return f"Priority.{self.value}"


class Task(SQLModel, table=True):
    """
    Represents a single to-do item owned by a user.

    Attributes:
        id: Unique task identifier (auto-increment)
        user_id: Foreign key to users table (owner)
        title: Task title (required, 1-200 characters)
        description: Optional task details (max 1000 characters)
        completed: Task completion status (default: False)
        due_date: Optional due date for the task (Phase V)
        priority: Task priority level (Phase V)
        tags: List of tags for categorization (Phase V)
        recurring_task_id: Foreign key to recurring_tasks if this is an occurrence (Phase V)
        created_at: Task creation timestamp
        updated_at: Last modification timestamp
        completed_at: Task completion timestamp (Phase V)
    """
    __tablename__ = "tasks"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id")
    title: str = Field(max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    completed: bool = Field(default=False, index=True)

    # Phase V: Advanced Task Management Fields
    due_date: Optional[datetime] = Field(default=None)
    priority: str = Field(default="MEDIUM", sa_column=Column(String(10)))
    tags: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    recurring_task_id: Optional[str] = Field(default=None, foreign_key="recurring_tasks.id")

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = Field(default=None)

    # Relationships
    user: "User" = Relationship(back_populates="tasks")
