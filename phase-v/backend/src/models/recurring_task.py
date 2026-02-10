"""
RecurringTask model for recurring task templates.
"""

from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship, Column
from typing import Optional, Literal
from sqlalchemy import String
import uuid


# Frequency as a string literal type for Pydantic
FrequencyType = Literal["DAILY", "WEEKLY", "MONTHLY"]


class Frequency(str):
    """Recurring task frequency"""
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not isinstance(v, str) or v not in ("DAILY", "WEEKLY", "MONTHLY"):
            raise ValueError(f"Invalid frequency: {v}")
        return v

    def __repr__(self):
        return f"Frequency.{self.value}"


class RecurringTask(SQLModel, table=True):
    """
    Template for recurring tasks that generates task occurrences automatically.

    Attributes:
        id: Unique recurring task identifier (UUID)
        user_id: Foreign key to users table (creator)
        title: Task title template
        description: Task description template
        frequency: How often the task repeats (DAILY, WEEKLY, MONTHLY)
        start_date: First occurrence date
        end_date: Optional last occurrence date
        next_occurrence: Calculated date of next task occurrence
        created_at: Template creation timestamp
        updated_at: Last update timestamp
    """
    __tablename__ = "recurring_tasks"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    title: str = Field(max_length=255)
    description: Optional[str] = Field(default=None)
    frequency: str = Field(sa_column=Column(String(20)))
    start_date: datetime = Field(nullable=False)
    end_date: Optional[datetime] = Field(default=None)
    next_occurrence: datetime = Field(nullable=False, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationships
    user: "User" = Relationship()
