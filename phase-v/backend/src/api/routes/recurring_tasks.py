"""
Recurring Task routes for Todo Application.

This module provides RESTful endpoints for recurring task management:
- Create a recurring task template
- List all recurring task templates for a user
- Get a specific recurring task template by ID
- Delete a recurring task template

All endpoints require JWT authentication and verify user ownership.
"""
from datetime import datetime
from typing import Annotated, Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user_id
from src.db import get_session
from src.models.recurring_task import RecurringTask, Frequency
from src.services.recurring_service import (
    create_recurring_task as service_create_recurring_task,
    get_recurring_tasks as service_get_recurring_tasks,
    delete_recurring_task as service_delete_recurring_task,
)


# Router configuration
router = APIRouter(prefix="/api/recurring-tasks", tags=["Recurring Tasks"])


# ============================================================================
# Request/Response Schemas
# ============================================================================


class RecurringTaskCreateRequest(BaseModel):
    """
    T071: Request schema for creating a recurring task template.

    Validation:
    - title: Required, 1-200 characters
    - description: Optional, max 1000 characters
    - frequency: Required, must be DAILY, WEEKLY, or MONTHLY
    - start_date: Optional, ISO 8601 datetime string (defaults to now)
    - end_date: Optional, ISO 8601 datetime string (null for infinite)
    """
    title: str = Field(..., min_length=1, max_length=200, description="Task title")
    description: Optional[str] = Field(None, max_length=1000, description="Task description")
    frequency: str = Field(..., description="Recurrence frequency (DAILY/WEEKLY/MONTHLY)")
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
        """Validate frequency is a valid option."""
        valid_frequencies = [f.value for f in Frequency]
        if v not in valid_frequencies:
            raise ValueError(f"Frequency must be one of {valid_frequencies}")
        return v


class RecurringTaskResponse(BaseModel):
    """
    T072: Response schema for a recurring task template.
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


class RecurringTaskListResponse(BaseModel):
    """
    Response schema for recurring task list.
    """
    recurring_tasks: List[RecurringTaskResponse] = Field(..., description="List of recurring task templates")
    total: int = Field(..., description="Total number of recurring tasks")


class ErrorDetail(BaseModel):
    """Error detail schema."""
    message: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")


# ============================================================================
# API Endpoints
# ============================================================================


@router.post(
    "",
    response_model=RecurringTaskResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorDetail, "description": "Invalid request data"},
        401: {"model": ErrorDetail, "description": "Unauthorized"},
    },
    summary="Create a recurring task template",
    description="T067: Creates a new recurring task template that automatically generates task occurrences. "
                "The first occurrence is created immediately."
)
async def create_recurring_task(
    request: RecurringTaskCreateRequest,
    session: Session = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
) -> RecurringTaskResponse:
    """
    T067: Create a new recurring task template.

    Args:
        request: Recurring task creation request
        session: Database session
        user_id: Authenticated user ID from JWT

    Returns:
        Created recurring task template

    Raises:
        HTTPException: If validation fails or creation error occurs
    """
    try:
        # Parse dates
        start_date = None
        end_date = None

        if request.start_date:
            start_date = datetime.fromisoformat(request.start_date.replace('Z', '+00:00'))
        else:
            start_date = datetime.now()

        if request.end_date:
            end_date = datetime.fromisoformat(request.end_date.replace('Z', '+00:00'))

        # Create recurring task
        recurring_task = service_create_recurring_task(
            user_id=user_id,
            title=request.title,
            description=request.description,
            frequency=request.frequency,
            start_date=start_date,
            end_date=end_date,
            session=session
        )

        return RecurringTaskResponse(
            id=recurring_task.id,
            user_id=recurring_task.user_id,
            title=recurring_task.title,
            description=recurring_task.description,
            frequency=recurring_task.frequency,
            start_date=recurring_task.start_date,
            end_date=recurring_task.end_date,
            next_occurrence=recurring_task.next_occurrence,
            created_at=recurring_task.created_at,
            updated_at=recurring_task.updated_at,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Validation error", "detail": str(e)}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to create recurring task", "detail": str(e)}
        )


@router.get(
    "",
    response_model=RecurringTaskListResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorDetail, "description": "Unauthorized"},
    },
    summary="List recurring task templates",
    description="T068: Lists all recurring task templates for the authenticated user. "
                "Supports filtering by completion status."
)
async def list_recurring_tasks(
    session: Session = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
    include_completed: bool = Query(
        False,
        description="Include templates that have reached end_date"
    ),
) -> RecurringTaskListResponse:
    """
    T068: List all recurring task templates for the authenticated user.

    Args:
        session: Database session
        user_id: Authenticated user ID from JWT
        include_completed: Include templates that have reached end_date

    Returns:
        List of recurring task templates
    """
    try:
        recurring_tasks = service_get_recurring_tasks(
            user_id=user_id,
            session=session,
            include_completed=include_completed
        )

        return RecurringTaskListResponse(
            recurring_tasks=[
                RecurringTaskResponse(
                    id=rt.id,
                    user_id=rt.user_id,
                    title=rt.title,
                    description=rt.description,
                    frequency=rt.frequency,
                    start_date=rt.start_date,
                    end_date=rt.end_date,
                    next_occurrence=rt.next_occurrence,
                    created_at=rt.created_at,
                    updated_at=rt.updated_at,
                )
                for rt in recurring_tasks
            ],
            total=len(recurring_tasks),
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to list recurring tasks", "detail": str(e)}
        )


@router.get(
    "/{recurring_task_id}",
    response_model=RecurringTaskResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorDetail, "description": "Unauthorized"},
        403: {"model": ErrorDetail, "description": "Forbidden - not the owner"},
        404: {"model": ErrorDetail, "description": "Recurring task not found"},
    },
    summary="Get a recurring task template",
    description="T069: Gets a specific recurring task template by ID. "
                "Verifies user ownership before returning."
)
async def get_recurring_task(
    recurring_task_id: str,
    session: Session = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
) -> RecurringTaskResponse:
    """
    T069: Get a specific recurring task template by ID.

    Args:
        recurring_task_id: Recurring task template ID
        session: Database session
        user_id: Authenticated user ID from JWT

    Returns:
        Recurring task template details

    Raises:
        HTTPException: If not found or user doesn't own it
    """
    try:
        # Get recurring task and verify ownership
        recurring_task = session.query(RecurringTask).filter(
            RecurringTask.id == recurring_task_id,
            RecurringTask.user_id == user_id
        ).first()

        if not recurring_task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"message": "Recurring task not found"}
            )

        return RecurringTaskResponse(
            id=recurring_task.id,
            user_id=recurring_task.user_id,
            title=recurring_task.title,
            description=recurring_task.description,
            frequency=recurring_task.frequency,
            start_date=recurring_task.start_date,
            end_date=recurring_task.end_date,
            next_occurrence=recurring_task.next_occurrence,
            created_at=recurring_task.created_at,
            updated_at=recurring_task.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to get recurring task", "detail": str(e)}
        )


@router.delete(
    "/{recurring_task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        401: {"model": ErrorDetail, "description": "Unauthorized"},
        403: {"model": ErrorDetail, "description": "Forbidden - not the owner"},
        404: {"model": ErrorDetail, "description": "Recurring task not found"},
    },
    summary="Delete a recurring task template",
    description="T070: Deletes a recurring task template. "
                "Stops future occurrences but does not delete existing tasks. "
                "Verifies user ownership before deletion."
)
async def delete_recurring_task(
    recurring_task_id: str,
    session: Session = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
) -> None:
    """
    T070: Delete a recurring task template.

    This stops future occurrences but does not delete existing tasks.

    Args:
        recurring_task_id: Recurring task template ID
        session: Database session
        user_id: Authenticated user ID from JWT

    Raises:
        HTTPException: If not found or user doesn't own it
    """
    try:
        # Delete recurring task (service verifies ownership)
        service_delete_recurring_task(
            recurring_task_id=recurring_task_id,
            user_id=user_id,
            session=session
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": str(e)}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": "Failed to delete recurring task", "detail": str(e)}
        )
