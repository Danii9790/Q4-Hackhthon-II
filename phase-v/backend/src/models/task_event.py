"""
TaskEvent model for audit trail.
Records all task operations for compliance, debugging, and analytics.
"""

from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship, Column
from typing import Optional, Any, Dict
from sqlalchemy import JSON
import uuid


class EventType(str):
    """Task event types"""
    CREATED = "created"
    UPDATED = "updated"
    COMPLETED = "completed"
    DELETED = "deleted"


class TaskEvent(SQLModel, table=True):
    """
    Immutable audit trail of all task operations.

    Attributes:
        id: Unique event identifier (UUID)
        event_type: Type of event (created, updated, completed, deleted)
        task_id: Foreign key to tasks table
        user_id: Foreign key to users table (who performed the action)
        event_data: JSON data containing before/after state, changes, etc.
        timestamp: When the event occurred
    """
    __tablename__ = "task_events"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    event_type: str = Field(index=True)
    task_id: int = Field(foreign_key="tasks.id", index=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    event_data: Dict[str, Any] = Field(sa_column=Column(JSON), default_factory=dict)
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        index=True
    )

    # Relationships
    task: "Task" = Relationship()
    user: "User" = Relationship()
