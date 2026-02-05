"""
Task model for Todo Application.
"""
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional


class Task(SQLModel, table=True):
    """
    Represents a single to-do item owned by a user.

    Attributes:
        id: Unique task identifier (auto-increment)
        user_id: Foreign key to users table (owner)
        title: Task title (required, 1-200 characters)
        description: Optional task details (max 1000 characters)
        completed: Task completion status (default: False)
        created_at: Task creation timestamp
        updated_at: Last modification timestamp
    """
    __tablename__ = "tasks"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="users.id")
    title: str = Field(max_length=200)
    description: Optional[str] = Field(default=None, max_length=1000)
    completed: bool = Field(default=False, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: "User" = Relationship(back_populates="tasks")
