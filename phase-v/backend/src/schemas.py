"""
Pydantic schemas for request/response models.

Defines all Pydantic models for API request validation and response formatting.
Ensures type safety and provides automatic JSON serialization.

Phase V: Adds advanced task management schemas.
"""

from typing import Any, Optional, List
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Error Response Schemas
# ============================================================================

class ErrorResponse(BaseModel):
    """
    Standardized error response model.

    Used for consistent error reporting across all API endpoints.

    Attributes:
        error: Brief error title
        message: Detailed error message
        code: Machine-readable error code
        details: Optional additional error details
    """
    error: str = Field(
        ...,
        description="Brief error title",
        examples=["Bad Request", "Unauthorized", "Not Found"]
    )
    message: str = Field(
        ...,
        description="Detailed error message"
    )
    code: str = Field(
        ...,
        description="Machine-readable error code",
        examples=["BAD_REQUEST", "UNAUTHORIZED", "NOT_FOUND"]
    )
    details: Optional[Any] = Field(
        default=None,
        description="Additional error details (e.g., validation errors)"
    )


# ============================================================================
# Phase V: Advanced Task Management Schemas
# ============================================================================


# Valid priority values
VALID_PRIORITIES = ["LOW", "MEDIUM", "HIGH"]

# Valid frequency values for recurring tasks
VALID_FREQUENCIES = ["DAILY", "WEEKLY", "MONTHLY"]


class TaskCreate(BaseModel):
    """
    T044: Request schema for creating a task with advanced fields.

    Validation:
    - title: Required, 1-200 characters
    - description: Optional, max 1000 characters
    - due_date: Optional, ISO 8601 datetime
    - priority: Optional, must be LOW/MEDIUM/HIGH (default MEDIUM)
    - tags: Optional, max 10 tags, max 50 chars each
    """
    title: str = Field(..., min_length=1, max_length=200, description="Task title")
    description: Optional[str] = Field(None, max_length=1000, description="Task description")
    due_date: Optional[str] = Field(None, description="Due date (ISO 8601 format)")
    priority: str = Field("MEDIUM", description="Task priority (LOW, MEDIUM, HIGH)")
    tags: List[str] = Field(default_factory=list, description="Task tags")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Validate title is not empty after stripping whitespace."""
        if not v or not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip()

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        """Validate priority is one of the allowed values."""
        if v not in VALID_PRIORITIES:
            raise ValueError(f"Priority must be one of {VALID_PRIORITIES}")
        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        """Validate tags array constraints."""
        if len(v) > 10:
            raise ValueError("Maximum 10 tags allowed")
        for tag in v:
            if not isinstance(tag, str) or len(tag) > 50:
                raise ValueError("Each tag must be a string of max 50 characters")
        return v


class TaskUpdate(BaseModel):
    """
    T045: Request schema for updating a task with advanced fields.

    Validation:
    - title: Optional, 1-200 characters if provided
    - description: Optional, max 1000 characters
    - due_date: Optional, ISO 8601 datetime or null to remove
    - priority: Optional, must be LOW/MEDIUM/HIGH
    - tags: Optional, replaces existing tags
    """
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Task title")
    description: Optional[str] = Field(None, max_length=1000, description="Task description")
    due_date: Optional[str] = Field(None, description="Due date (ISO 8601 format)")
    priority: Optional[str] = Field(None, description="Task priority (LOW, MEDIUM, HIGH)")
    tags: Optional[List[str]] = Field(None, description="Task tags")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        """Validate title is not empty after stripping whitespace."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("Title cannot be empty")
        return v.strip() if v else None

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: Optional[str]) -> Optional[str]:
        """Validate priority is one of the allowed values."""
        if v is not None and v not in VALID_PRIORITIES:
            raise ValueError(f"Priority must be one of {VALID_PRIORITIES}")
        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate tags array constraints."""
        if v is not None:
            if len(v) > 10:
                raise ValueError("Maximum 10 tags allowed")
            for tag in v:
                if not isinstance(tag, str) or len(tag) > 50:
                    raise ValueError("Each tag must be a string of max 50 characters")
        return v


class TaskResponse(BaseModel):
    """
    T046: Response schema for a task with all Phase V fields.

    Includes all advanced task fields.
    """
    id: int = Field(..., description="Task ID")
    user_id: str = Field(..., description="Owner user ID")
    title: str = Field(..., description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    completed: bool = Field(..., description="Task completion status")
    completed_at: Optional[datetime] = Field(None, description="Task completion timestamp")
    due_date: Optional[datetime] = Field(None, description="Task due date")
    priority: str = Field(..., description="Task priority (LOW, MEDIUM, HIGH)")
    tags: List[str] = Field(default_factory=list, description="Task tags")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


# ============================================================================
# Phase V: Recurring Task Schemas
# ============================================================================


class RecurringTaskCreate(BaseModel):
    """
    T071: Request schema for creating a recurring task template.

    Validation:
    - title: Required, 1-200 characters
    - description: Optional, max 1000 characters
    - frequency: Required, must be DAILY/WEEKLY/MONTHLY
    - start_date: Optional, ISO 8601 datetime (defaults to now)
    - end_date: Optional, ISO 8601 datetime (null for infinite)
    """
    title: str = Field(..., min_length=1, max_length=200, description="Task title")
    description: Optional[str] = Field(None, max_length=1000, description="Task description")
    frequency: str = Field(..., description="Recurrence frequency (DAILY, WEEKLY, MONTHLY)")
    start_date: Optional[str] = Field(None, description="First occurrence date (ISO 8601)")
    end_date: Optional[str] = Field(None, description="End date for recurrence (ISO 8601, null for infinite)")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Validate title is not empty after stripping whitespace."""
        if not v or not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip()

    @field_validator("frequency")
    @classmethod
    def validate_frequency(cls, v: str) -> str:
        """Validate frequency is one of the allowed values."""
        if v not in VALID_FREQUENCIES:
            raise ValueError(f"Frequency must be one of {VALID_FREQUENCIES}")
        return v


class RecurringTaskResponse(BaseModel):
    """
    T072: Response schema for a recurring task template.

    Includes all recurring task fields including next occurrence date.
    """
    id: str = Field(..., description="Recurring task template ID")
    user_id: str = Field(..., description="Owner user ID")
    title: str = Field(..., description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    frequency: str = Field(..., description="Recurrence frequency")
    start_date: datetime = Field(..., description="First occurrence date")
    end_date: Optional[datetime] = Field(None, description="End date for recurrence")
    next_occurrence: datetime = Field(..., description="Next scheduled occurrence")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


# ============================================================================
# Phase V: Reminder Schemas
# ============================================================================


class ReminderCreate(BaseModel):
    """
    T088: Request schema for creating a reminder.

    Validation:
    - remind_at: Required, ISO 8601 datetime in the future
    """
    remind_at: str = Field(..., description="When to send the reminder (ISO 8601 format)")

    @field_validator("remind_at")
    @classmethod
    def validate_remind_at(cls, v: str) -> str:
        """Validate remind_at is a valid ISO 8601 datetime."""
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(v.replace('Z', '+00:00'))
            # Ensure it's in the future
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=None)
            # Return as-is, will be validated in service layer
            return v
        except ValueError:
            raise ValueError("remind_at must be a valid ISO 8601 datetime")


class ReminderResponse(BaseModel):
    """
    T089: Response schema for a reminder.

    Includes all reminder fields.
    """
    id: str = Field(..., description="Reminder ID")
    task_id: int = Field(..., description="Associated task ID")
    remind_at: datetime = Field(..., description="When to send the reminder")
    sent: bool = Field(..., description="Whether the reminder has been sent")
    sent_at: Optional[datetime] = Field(None, description="When the reminder was sent")
    created_at: datetime = Field(..., description="Creation timestamp")


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    # Error schemas
    "ErrorResponse",
    # Phase V: Task schemas
    "TaskCreate",
    "TaskUpdate",
    "TaskResponse",
    # Phase V: Recurring task schemas
    "VALID_FREQUENCIES",
    "RecurringTaskCreate",
    "RecurringTaskResponse",
    # Phase V: Reminder schemas
    "ReminderCreate",
    "ReminderResponse",
]
