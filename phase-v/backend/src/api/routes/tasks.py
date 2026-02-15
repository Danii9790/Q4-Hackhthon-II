"""
Task routes for Todo Application.

This module provides RESTful endpoints for task management:
- List all tasks for a user (with pagination)
- Create a new task
- Get a specific task by ID

All endpoints require JWT authentication and verify user ownership.
"""
from datetime import datetime
from typing import Annotated, Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user_id
from src.db import get_session
from src.models.task import Task
from src.services.task import create_task, list_tasks, get_task, update_task, complete_task, uncomplete_task, delete_task


# Router configuration
router = APIRouter(prefix="/users/{user_id}", tags=["Tasks"])

# Additional router for task-specific endpoints (without user_id in prefix)
task_router = APIRouter(prefix="/tasks", tags=["Tasks"])


# ============================================================================
# Request/Response Schemas
# ============================================================================


class TaskCreateRequest(BaseModel):
    """
    Request schema for creating a new task.

    Validation:
    - title: Required, 1-200 characters
    - description: Optional, max 1000 characters
    - due_date: Optional ISO 8601 datetime string
    - priority: Optional (low, medium, high)
    - tags: Optional list of strings
    """
    title: str = Field(..., min_length=1, max_length=200, description="Task title")
    description: Optional[str] = Field(None, max_length=1000, description="Task description")
    due_date: Optional[str] = Field(None, description="Task due date (ISO 8601 format)")
    priority: Optional[str] = Field(None, description="Task priority (low, medium, high)")
    tags: Optional[List[str]] = Field(None, description="Task tags")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Validate title is not empty after stripping whitespace."""
        if not v or not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip()

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: Optional[str]) -> Optional[str]:
        """Validate priority is one of the allowed values."""
        if v is not None and v.lower() not in ["low", "medium", "high"]:
            raise ValueError("Priority must be one of: low, medium, high")
        return v.upper() if v else None

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate tags and remove duplicates while preserving order."""
        if v is not None:
            # Check maximum 10 tags before deduplication
            if len(v) > 10:
                raise ValueError("Maximum 10 tags allowed")
            # Remove duplicates and empty tags while preserving order
            seen = set()
            result = []
            for tag in v:
                tag = tag.strip()
                if tag and tag not in seen:
                    seen.add(tag)
                    result.append(tag)
            return result
        return v


class TaskUpdateRequest(BaseModel):
    """
    Request schema for updating an existing task.

    Validation:
    - title: Optional, 1-200 characters if provided
    - description: Optional, max 1000 characters
    - At least one field must be provided
    """
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Task title")
    description: Optional[str] = Field(None, max_length=1000, description="Task description")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        """Validate title is not empty after stripping whitespace."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("Title cannot be empty")
        return v.strip() if v else None


class TaskResponse(BaseModel):
    """
    Response schema for a single task.
    """
    id: int = Field(..., description="Task ID")
    user_id: str = Field(..., description="Owner user ID")
    title: str = Field(..., description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    completed: bool = Field(..., description="Task completion status")
    completed_at: Optional[datetime] = Field(None, description="Task completion timestamp")
    due_date: Optional[datetime] = Field(None, description="Task due date")
    priority: str = Field("MEDIUM", description="Task priority")
    tags: List[str] = Field(default_factory=list, description="Task tags")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class TaskListResponse(BaseModel):
    """
    Response schema for paginated task list.
    """
    tasks: List[TaskResponse] = Field(..., description="List of tasks")
    total: int = Field(..., description="Total number of tasks for user")
    offset: int = Field(..., description="Current pagination offset")
    limit: int = Field(..., description="Current pagination limit")


class ErrorDetail(BaseModel):
    """
    Error detail structure.
    """
    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")


class ErrorResponse(BaseModel):
    """
    Standard error response schema.
    """
    error: ErrorDetail = Field(..., description="Error details")


class DeleteTaskResponse(BaseModel):
    """
    Response schema for successful task deletion.
    """
    message: str = Field(..., description="Success message")


# ============================================================================
# Helper Functions
# ============================================================================


def verify_user_access(authenticated_user_id: str, requested_user_id: str) -> None:
    """
    Verify that the authenticated user matches the requested user ID.

    Args:
        authenticated_user_id: User ID from JWT token
        requested_user_id: User ID from URL parameter

    Raises:
        HTTPException 403: If user IDs don't match
    """
    if authenticated_user_id != requested_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "FORBIDDEN",
                "message": "You can only access your own tasks"
            }
        )


# ============================================================================
# Endpoints
# ============================================================================


@router.get(
    "/tasks",
    response_model=TaskListResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - accessing another user's tasks"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
def get_user_tasks(
    user_id: str,
    authenticated_user_id: Annotated[str, Depends(get_current_user_id)],
    offset: Annotated[int, Query(ge=0, description="Number of tasks to skip")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="Max number of tasks to return")] = 50,
    session: Annotated[Session, Depends(get_session)] = None
) -> TaskListResponse:
    """
    List all tasks for a user with pagination.

    This endpoint:
    1. Verifies JWT authentication
    2. Verifies user_id matches authenticated user
    3. Returns user's tasks ordered by most recent first
    4. Supports pagination with offset/limit

    Args:
        user_id: User ID from URL path
        authenticated_user_id: User ID from JWT token (injected by dependency)
        offset: Number of tasks to skip (default: 0)
        limit: Maximum tasks to return, max 100 (default: 50)
        session: Database session (injected by dependency)

    Returns:
        TaskListResponse with tasks, total count, offset, and limit

    Raises:
        HTTPException 401: If authentication fails
        HTTPException 403: If user_id doesn't match authenticated user
        HTTPException 500: If server error occurs
    """
    # Verify user owns this resource
    verify_user_access(authenticated_user_id, user_id)

    # Get tasks from service layer
    tasks, total = list_tasks(
        user_id=user_id,
        offset=offset,
        limit=limit,
        session=session
    )

    # Convert Task models to response schemas
    task_responses = [
        TaskResponse(
            id=task.id,
            user_id=task.user_id,
            title=task.title,
            description=task.description,
            completed=task.completed,
            created_at=task.created_at,
            updated_at=task.updated_at
        )
        for task in tasks
    ]

    return TaskListResponse(
        tasks=task_responses,
        total=total,
        offset=offset,
        limit=limit
    )


@router.post(
    "/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Validation error"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - creating for another user"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
def create_user_task(
    user_id: str,
    request: TaskCreateRequest,
    authenticated_user_id: Annotated[str, Depends(get_current_user_id)],
    session: Annotated[Session, Depends(get_session)] = None
) -> TaskResponse:
    """
    Create a new task for a user.

    This endpoint:
    1. Verifies JWT authentication
    2. Verifies user_id matches authenticated user
    3. Validates title and description
    4. Creates task with completed=False and current timestamps

    Args:
        user_id: User ID from URL path
        request: Task creation request with title and optional description
        authenticated_user_id: User ID from JWT token (injected by dependency)
        session: Database session (injected by dependency)

    Returns:
        TaskResponse with created task details

    Raises:
        HTTPException 400: If validation fails
        HTTPException 401: If authentication fails
        HTTPException 403: If user_id doesn't match authenticated user
        HTTPException 500: If server error occurs
    """
    # Verify user owns this resource
    verify_user_access(authenticated_user_id, user_id)

    # Create task via service layer
    task = create_task(
        title=request.title,
        description=request.description,
        user_id=user_id,
        due_date=request.due_date,
        priority=request.priority if request.priority else "MEDIUM",
        tags=request.tags,
        session=session
    )

    # Convert to response schema
    return TaskResponse(
        id=task.id,
        user_id=task.user_id,
        title=task.title,
        description=task.description,
        completed=task.completed,
        completed_at=task.completed_at,
        due_date=task.due_date,
        priority=task.priority,
        tags=task.tags or [],
        created_at=task.created_at,
        updated_at=task.updated_at
    )


@router.get(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - accessing another user's task"},
        404: {"model": ErrorResponse, "description": "Task not found"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
def get_user_task(
    user_id: str,
    task_id: int,
    authenticated_user_id: Annotated[str, Depends(get_current_user_id)],
    session: Annotated[Session, Depends(get_session)] = None
) -> TaskResponse:
    """
    Get a specific task by ID.

    This endpoint:
    1. Verifies JWT authentication
    2. Verifies user_id matches authenticated user
    3. Returns task only if it belongs to the user

    Args:
        user_id: User ID from URL path
        task_id: Task ID from URL path
        authenticated_user_id: User ID from JWT token (injected by dependency)
        session: Database session (injected by dependency)

    Returns:
        TaskResponse with task details

    Raises:
        HTTPException 401: If authentication fails
        HTTPException 403: If user_id doesn't match authenticated user
        HTTPException 404: If task not found or doesn't belong to user
        HTTPException 500: If server error occurs
    """
    # Verify user owns this resource
    verify_user_access(authenticated_user_id, user_id)

    # Get task via service layer (includes ownership check)
    task = get_task(
        task_id=task_id,
        user_id=user_id,
        session=session
    )

    # Convert to response schema
    return TaskResponse(
        id=task.id,
        user_id=task.user_id,
        title=task.title,
        description=task.description,
        completed=task.completed,
        completed_at=task.completed_at,
        due_date=task.due_date,
        priority=task.priority,
        tags=task.tags or [],
        created_at=task.created_at,
        updated_at=task.updated_at
    )


@router.patch(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Validation error"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - updating another user's task"},
        404: {"model": ErrorResponse, "description": "Task not found"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
def update_user_task(
    user_id: str,
    task_id: int,
    request: TaskUpdateRequest,
    authenticated_user_id: Annotated[str, Depends(get_current_user_id)],
    session: Annotated[Session, Depends(get_session)] = None
) -> TaskResponse:
    """
    Update a task's title and/or description.

    This endpoint:
    1. Verifies JWT authentication
    2. Verifies user_id matches authenticated user
    3. Updates title and/or description if provided
    4. Updates the updated_at timestamp

    Args:
        user_id: User ID from URL path
        task_id: Task ID from URL path
        request: Task update request with optional title and/or description
        authenticated_user_id: User ID from JWT token (injected by dependency)
        session: Database session (injected by dependency)

    Returns:
        TaskResponse with updated task details

    Raises:
        HTTPException 400: If validation fails
        HTTPException 401: If authentication fails
        HTTPException 403: If user_id doesn't match authenticated user
        HTTPException 404: If task not found or doesn't belong to user
        HTTPException 500: If server error occurs
    """
    # Verify user owns this resource
    verify_user_access(authenticated_user_id, user_id)

    # Validate at least one field is provided
    if request.title is None and request.description is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_REQUEST",
                "message": "At least one field (title or description) must be provided"
            }
        )

    # Update task via service layer
    task = update_task(
        task_id=task_id,
        user_id=user_id,
        title=request.title,
        description=request.description,
        session=session
    )

    # Convert to response schema
    return TaskResponse(
        id=task.id,
        user_id=task.user_id,
        title=task.title,
        description=task.description,
        completed=task.completed,
        completed_at=task.completed_at,
        due_date=task.due_date,
        priority=task.priority,
        tags=task.tags or [],
        created_at=task.created_at,
        updated_at=task.updated_at
    )


# ============================================================================
# Task Completion Endpoints (without user_id in path)
# ============================================================================

@task_router.delete(
    "/{task_id}",
    response_model=DeleteTaskResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - deleting another user's task"},
        404: {"model": ErrorResponse, "description": "Task not found"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
def delete_user_task(
    task_id: int,
    authenticated_user_id: Annotated[str, Depends(get_current_user_id)],
    session: Annotated[Session, Depends(get_session)] = None
) -> DeleteTaskResponse:
    """
    Delete a task.

    This endpoint:
    1. Verifies JWT authentication
    2. Verifies task exists and belongs to the authenticated user
    3. Deletes the task from the database

    Args:
        task_id: Task ID from URL path
        authenticated_user_id: User ID from JWT token (injected by dependency)
        session: Database session (injected by dependency)

    Returns:
        DeleteTaskResponse with success message

    Raises:
        HTTPException 401: If authentication fails
        HTTPException 403: If task doesn't belong to user
        HTTPException 404: If task not found
        HTTPException 500: If server error occurs
    """
    # Delete task via service layer (includes ownership check)
    delete_task(
        task_id=task_id,
        user_id=authenticated_user_id,
        session=session
    )

    # Return success response
    return DeleteTaskResponse(message="Task deleted successfully")


# ============================================================================
# Task Completion Endpoints (without user_id in path)
# ============================================================================


@task_router.patch(
    "/{task_id}/complete",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - accessing another user's task"},
        404: {"model": ErrorResponse, "description": "Task not found"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
def complete_task_endpoint(
    task_id: int,
    authenticated_user_id: Annotated[str, Depends(get_current_user_id)],
    session: Annotated[Session, Depends(get_session)] = None
) -> TaskResponse:
    """
    Mark a task as completed.

    This endpoint:
    1. Verifies JWT authentication and extracts user_id from token
    2. Verifies task exists and belongs to the authenticated user
    3. Marks the task as completed
    4. Updates the updated_at timestamp

    Args:
        task_id: Task ID from URL path
        authenticated_user_id: User ID from JWT token (injected by dependency)
        session: Database session (injected by dependency)

    Returns:
        TaskResponse with updated task details

    Raises:
        HTTPException 401: If authentication fails
        HTTPException 403: If task doesn't belong to authenticated user
        HTTPException 404: If task not found
        HTTPException 500: If server error occurs
    """
    # Complete task via service layer (includes ownership check)
    task = complete_task(
        task_id=task_id,
        user_id=authenticated_user_id,
        session=session
    )

    # Convert to response schema
    return TaskResponse(
        id=task.id,
        user_id=task.user_id,
        title=task.title,
        description=task.description,
        completed=task.completed,
        completed_at=task.completed_at,
        due_date=task.due_date,
        priority=task.priority,
        tags=task.tags or [],
        created_at=task.created_at,
        updated_at=task.updated_at
    )


@task_router.patch(
    "/{task_id}/uncomplete",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - accessing another user's task"},
        404: {"model": ErrorResponse, "description": "Task not found"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
def uncomplete_task_endpoint(
    task_id: int,
    authenticated_user_id: Annotated[str, Depends(get_current_user_id)],
    session: Annotated[Session, Depends(get_session)] = None
) -> TaskResponse:
    """
    Mark a task as not completed.

    This endpoint:
    1. Verifies JWT authentication and extracts user_id from token
    2. Verifies task exists and belongs to the authenticated user
    3. Marks the task as not completed
    4. Updates the updated_at timestamp

    Args:
        task_id: Task ID from URL path
        authenticated_user_id: User ID from JWT token (injected by dependency)
        session: Database session (injected by dependency)

    Returns:
        TaskResponse with updated task details

    Raises:
        HTTPException 401: If authentication fails
        HTTPException 403: If task doesn't belong to authenticated user
        HTTPException 404: If task not found
        HTTPException 500: If server error occurs
    """
    # Uncomplete task via service layer (includes ownership check)
    task = uncomplete_task(
        task_id=task_id,
        user_id=authenticated_user_id,
        session=session
    )

    # Convert to response schema
    return TaskResponse(
        id=task.id,
        user_id=task.user_id,
        title=task.title,
        description=task.description,
        completed=task.completed,
        completed_at=task.completed_at,
        due_date=task.due_date,
        priority=task.priority,
        tags=task.tags or [],
        created_at=task.created_at,
        updated_at=task.updated_at
    )


# ============================================================================
# Phase V: Advanced Task Management Endpoints
# ============================================================================


@task_router.get(
    "",
    response_model=TaskListResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
def get_tasks_with_filters(
    authenticated_user_id: Annotated[str, Depends(get_current_user_id)],
    priority: Annotated[Optional[str], Query(description="Filter by priority (LOW, MEDIUM, HIGH)")] = None,
    tags: Annotated[Optional[str], Query(description="Filter by tags (comma-separated)")] = None,
    due_before: Annotated[Optional[str], Query(description="Filter tasks due before this ISO date")] = None,
    due_after: Annotated[Optional[str], Query(description="Filter tasks due after this ISO date")] = None,
    search: Annotated[Optional[str], Query(description="Full-text search in title and description")] = None,
    sort_by: Annotated[str, Query(description="Sort field (created_at, updated_at, due_date, priority, completed_at)")] = "created_at",
    sort_order: Annotated[str, Query(description="Sort order (asc, desc)")] = "desc",
    offset: Annotated[int, Query(ge=0, description="Number of tasks to skip")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="Max number of tasks to return")] = 50,
    session: Annotated[Session, Depends(get_session)] = None
) -> TaskListResponse:
    """T040: List tasks with advanced filtering, sorting, and searching."""
    from src.services.task import list_tasks_advanced
    from datetime import datetime

    tags_list = None
    if tags:
        tags_list = [t.strip() for t in tags.split(",")]

    due_before_dt = None
    due_after_dt = None
    if due_before:
        due_before_dt = datetime.fromisoformat(due_before.replace('Z', '+00:00'))
    if due_after:
        due_after_dt = datetime.fromisoformat(due_after.replace('Z', '+00:00'))

    tasks, total = list_tasks_advanced(
        user_id=authenticated_user_id,
        session=session,
        offset=offset,
        limit=limit,
        priority=priority,
        tags=tags_list,
        due_before=due_before_dt,
        due_after=due_after_dt,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order
    )

    task_responses = [
        TaskResponse(
            id=task.id, user_id=task.user_id, title=task.title,
            description=task.description, completed=task.completed,
            created_at=task.created_at, updated_at=task.updated_at
        ) for task in tasks
    ]

    return TaskListResponse(tasks=task_responses, total=total, offset=offset, limit=limit)


@task_router.patch("/{task_id}/priority", response_model=TaskResponse)
def set_task_priority_endpoint(
    task_id: int,
    request: dict,
    authenticated_user_id: Annotated[str, Depends(get_current_user_id)],
    session: Annotated[Session, Depends(get_session)] = None
) -> TaskResponse:
    """T041: Set the priority of a task."""
    from src.services.task import set_task_priority as service_set_task_priority

    priority = request.get("priority")
    if not priority:
        raise HTTPException(status_code=400, detail={"code": "INVALID_REQUEST", "message": "priority field is required"})

    task = service_set_task_priority(task_id=task_id, user_id=authenticated_user_id, priority=priority, session=session)

    return TaskResponse(
        id=task.id, user_id=task.user_id, title=task.title,
        description=task.description, completed=task.completed,
        created_at=task.created_at, updated_at=task.updated_at
    )


@task_router.patch("/{task_id}/due-date", response_model=TaskResponse)
def set_task_due_date_endpoint(
    task_id: int,
    request: dict,
    authenticated_user_id: Annotated[str, Depends(get_current_user_id)],
    session: Annotated[Session, Depends(get_session)] = None
) -> TaskResponse:
    """T042: Set the due date of a task."""
    from src.services.task import set_task_due_date as service_set_task_due_date
    from datetime import datetime

    due_date_str = request.get("due_date")
    due_date_dt = None
    if due_date_str is not None:
        due_date_dt = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))

    task = service_set_task_due_date(task_id=task_id, user_id=authenticated_user_id, due_date=due_date_dt, session=session)

    return TaskResponse(
        id=task.id, user_id=task.user_id, title=task.title,
        description=task.description, completed=task.completed,
        created_at=task.created_at, updated_at=task.updated_at
    )


@task_router.post("/{task_id}/tags", response_model=TaskResponse)
def add_task_tags_endpoint(
    task_id: int,
    request: dict,
    authenticated_user_id: Annotated[str, Depends(get_current_user_id)],
    session: Annotated[Session, Depends(get_session)] = None
) -> TaskResponse:
    """T043: Add tags to a task."""
    from src.services.task import add_task_tags as service_add_task_tags

    tags = request.get("tags")
    if not tags or not isinstance(tags, list):
        raise HTTPException(status_code=400, detail={"code": "INVALID_REQUEST", "message": "tags field is required and must be a list"})

    task = service_add_task_tags(task_id=task_id, user_id=authenticated_user_id, tags=tags, session=session)

    return TaskResponse(
        id=task.id, user_id=task.user_id, title=task.title,
        description=task.description, completed=task.completed,
        created_at=task.created_at, updated_at=task.updated_at
    )


# ============================================================================
# Phase V: Reminder Endpoints
# ============================================================================


@task_router.post("/{task_id}/reminders", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_task_reminder_endpoint(
    task_id: int,
    request: dict,
    authenticated_user_id: Annotated[str, Depends(get_current_user_id)],
    session: Annotated[Session, Depends(get_session)] = None
) -> dict:
    """
    T085: Create a reminder for a task.

    Creates a reminder that will trigger a notification at the specified time.

    Args:
        task_id: Task ID from URL path
        request: Request body with remind_at field (ISO 8601 datetime)
        authenticated_user_id: User ID from JWT token
        session: Database session

    Returns:
        Created reminder details

    Raises:
        HTTPException 400: If remind_at is invalid or in the past
        HTTPException 403: If task doesn't belong to user
        HTTPException 404: If task not found
    """
    from src.services.reminder_service import create_reminder
    from src.services.task import get_task
    from datetime import datetime

    # Verify task exists and belongs to user
    task = get_task(task_id=task_id, user_id=authenticated_user_id, session=session)

    # Parse remind_at
    remind_at_str = request.get("remind_at")
    if not remind_at_str:
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_REQUEST", "message": "remind_at field is required"}
        )

    remind_at = datetime.fromisoformat(remind_at_str.replace('Z', '+00:00'))

    # Create reminder
    reminder = create_reminder(
        task_id=task_id,
        remind_at=remind_at,
        session=session
    )

    return {
        "id": reminder.id,
        "task_id": reminder.task_id,
        "remind_at": reminder.remind_at.isoformat(),
        "sent": reminder.sent,
        "sent_at": reminder.sent_at.isoformat() if reminder.sent_at else None,
        "created_at": reminder.created_at.isoformat()
    }


@task_router.get("/{task_id}/reminders", response_model=list)
def list_task_reminders_endpoint(
    task_id: int,
    authenticated_user_id: Annotated[str, Depends(get_current_user_id)],
    session: Annotated[Session, Depends(get_session)] = None
) -> list:
    """
    T086: List all reminders for a specific task.

    Args:
        task_id: Task ID from URL path
        authenticated_user_id: User ID from JWT token
        session: Database session

    Returns:
        List of reminders for the task

    Raises:
        HTTPException 403: If task doesn't belong to user
        HTTPException 404: If task not found
    """
    from src.services.task import get_task
    from src.services.reminder_service import get_reminders_for_task

    # Verify task exists and belongs to user
    task = get_task(task_id=task_id, user_id=authenticated_user_id, session=session)

    # Get reminders for task
    reminders = get_reminders_for_task(task_id=task_id, session=session)

    return [
        {
            "id": r.id,
            "task_id": r.task_id,
            "remind_at": r.remind_at.isoformat(),
            "sent": r.sent,
            "sent_at": r.sent_at.isoformat() if r.sent_at else None,
            "created_at": r.created_at.isoformat()
        }
        for r in reminders
    ]


@task_router.get("/reminders", response_model=dict)
def list_user_reminders_endpoint(
    authenticated_user_id: Annotated[str, Depends(get_current_user_id)],
    session: Annotated[Session, Depends(get_session)] = None,
    include_sent: bool = False
) -> dict:
    """
    T087: List all upcoming reminders for the authenticated user.

    Args:
        authenticated_user_id: User ID from JWT token
        session: Database session
        include_sent: Include sent reminders (default: False)

    Returns:
        Dict with reminders list and count
    """
    from src.services.reminder_service import list_reminders
    from src.models.task import Task

    # Get reminders for user
    reminders = list_reminders(
        user_id=authenticated_user_id,
        session=session,
        include_sent=include_sent
    )

    # Enrich with task titles
    enriched_reminders = []
    for reminder in reminders:
        task = session.query(Task).filter(Task.id == reminder.task_id).first()
        enriched_reminders.append({
            "id": reminder.id,
            "task_id": reminder.task_id,
            "task_title": task.title if task else "Unknown task",
            "remind_at": reminder.remind_at.isoformat(),
            "sent": reminder.sent,
            "sent_at": reminder.sent_at.isoformat() if reminder.sent_at else None,
            "created_at": reminder.created_at.isoformat()
        })

    return {
        "count": len(enriched_reminders),
        "reminders": enriched_reminders
    }


@task_router.post("/reminders/check", response_model=dict)
def check_reminders_endpoint() -> dict:
    """
    T090: Dapr cron binding endpoint for checking due reminders.

    Called by Dapr cron binding every 5 minutes to process due reminders.

    This endpoint:
    1. Queries for unsent reminders where remind_at <= NOW()
    2. Sends notifications for each due reminder
    3. Marks reminders as sent

    Returns:
        Dict with processing results

    Note:
        In production, this should be secured with API token authentication
        to prevent unauthorized calls.
    """
    from src.services.reminder_consumer import process_reminders_cron

    # Process due reminders
    result = process_reminders_cron()

    return {
        "message": "Reminder check completed",
        "processed": result.get("processed", 0),
        "succeeded": result.get("succeeded", 0),
        "failed": result.get("failed", 0),
        "errors": result.get("errors", [])
    }


# ============================================================================
# Phase VI: Audit Trail Endpoints
# ============================================================================


class AuditEventResponse(BaseModel):
    """
    Response schema for a single audit event.
    """
    id: int = Field(..., description="Event ID")
    task_id: int = Field(..., description="Task ID")
    user_id: str = Field(..., description="User who performed the action")
    event_type: str = Field(..., description="Event type (created, updated, completed, deleted)")
    timestamp: datetime = Field(..., description="Event timestamp")
    event_data: dict = Field(..., description="Event data including before/after states")


class AuditTrailResponse(BaseModel):
    """
    Response schema for audit trail query.
    """
    task_id: int = Field(..., description="Task ID")
    events: List[AuditEventResponse] = Field(..., description="List of audit events")
    total: int = Field(..., description="Total number of events")


class UserActivityResponse(BaseModel):
    """
    Response schema for user activity query.
    """
    user_id: str = Field(..., description="User ID")
    events: List[AuditEventResponse] = Field(..., description="List of audit events")
    total: int = Field(..., description="Total number of events")


@task_router.get(
    "/{task_id}/audit",
    response_model=AuditTrailResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - accessing another user's task"},
        404: {"model": ErrorResponse, "description": "Task not found"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
def get_task_audit_trail(
    task_id: int,
    authenticated_user_id: Annotated[str, Depends(get_current_user_id)],
    limit: Annotated[int, Query(ge=1, le=100, description="Max number of events to return")] = 50,
    session: Annotated[Session, Depends(get_session)] = None
) -> AuditTrailResponse:
    """
    T106: Get audit trail for a specific task.

    This endpoint:
    1. Verifies JWT authentication
    2. Verifies task exists and belongs to the authenticated user
    3. Returns all audit events for the task in chronological order

    Args:
        task_id: Task ID from URL path
        authenticated_user_id: User ID from JWT token (injected by dependency)
        limit: Maximum events to return, max 100 (default: 50)
        session: Database session (injected by dependency)

    Returns:
        AuditTrailResponse with task_id, events list, and total count

    Raises:
        HTTPException 401: If authentication fails
        HTTPException 403: If task doesn't belong to user
        HTTPException 404: If task not found
        HTTPException 500: If server error occurs
    """
    from src.services.task import get_task
    from src.services.audit_service import AuditService

    # Verify task exists and belongs to user
    get_task(task_id=task_id, user_id=authenticated_user_id, session=session)

    # Get audit history
    events = AuditService.get_task_history(
        session=session,
        task_id=task_id,
        limit=limit
    )

    # Convert to response schemas
    event_responses = [
        AuditEventResponse(
            id=event.id,
            task_id=event.task_id,
            user_id=event.user_id,
            event_type=event.event_type,
            timestamp=event.timestamp,
            event_data=event.event_data
        )
        for event in events
    ]

    return AuditTrailResponse(
        task_id=task_id,
        events=event_responses,
        total=len(event_responses)
    )


@task_router.get(
    "/audit/activity",
    response_model=UserActivityResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
def get_user_audit_activity(
    authenticated_user_id: Annotated[str, Depends(get_current_user_id)],
    limit: Annotated[int, Query(ge=1, le=100, description="Max number of events to return")] = 50,
    session: Annotated[Session, Depends(get_session)] = None
) -> UserActivityResponse:
    """
    T107: Get audit activity for the authenticated user.

    This endpoint:
    1. Verifies JWT authentication
    2. Returns all audit events performed by the authenticated user
    3. Ordered by most recent first

    Args:
        authenticated_user_id: User ID from JWT token (injected by dependency)
        limit: Maximum events to return, max 100 (default: 50)
        session: Database session (injected by dependency)

    Returns:
        UserActivityResponse with user_id, events list, and total count

    Raises:
        HTTPException 401: If authentication fails
        HTTPException 500: If server error occurs
    """
    from src.services.audit_service import AuditService

    # Get user activity
    events = AuditService.get_user_activity(
        session=session,
        user_id=authenticated_user_id,
        limit=limit
    )

    # Convert to response schemas
    event_responses = [
        AuditEventResponse(
            id=event.id,
            task_id=event.task_id,
            user_id=event.user_id,
            event_type=event.event_type,
            timestamp=event.timestamp,
            event_data=event.event_data
        )
        for event in events
    ]

    return UserActivityResponse(
        user_id=authenticated_user_id,
        events=event_responses,
        total=len(event_responses)
    )
