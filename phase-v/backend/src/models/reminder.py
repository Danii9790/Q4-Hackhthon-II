"""
Reminder model for task reminders.
"""

from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
import uuid


class Reminder(SQLModel, table=True):
    """
    Scheduled reminder for a task with a due date.

    Attributes:
        id: Unique reminder identifier (UUID)
        task_id: Foreign key to tasks table
        remind_at: When to send the reminder (UTC)
        sent: Whether the reminder has been sent
        sent_at: When the reminder was actually sent
        created_at: When the reminder was created
    """
    __tablename__ = "reminders"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    task_id: int = Field(foreign_key="tasks.id", index=True)
    remind_at: datetime = Field(index=True)
    sent: bool = Field(default=False, index=True)
    sent_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationships
    task: "Task" = Relationship()
