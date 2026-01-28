"""
Task routes for Todo Application.

This module provides RESTful endpoints for task management:
- List all tasks for a user (with pagination)
- Create a new task
- Get a specific task by ID

All endpoints require JWT authentication and verify user ownership.
"""
from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user_id
from src.db import get_session
from src.models.task import Task
from src.services.task import create_task, list_tasks, get_task, update_task, complete_task, uncomplete_task, delete_task


# Router configuration
router = APIRouter(prefix="/api/users/{user_id}", tags=["Tasks"])

# Additional router for task-specific endpoints (without user_id in prefix)
task_router = APIRouter(prefix="/api/tasks", tags=["Tasks"])


# ============================================================================
# Request/Response Schemas
# ============================================================================


class TaskCreateRequest(BaseModel):
    """
    Request schema for creating a new task.

    Validation:
    - title: Required, 1-200 characters
    - description: Optional, max 1000 characters
    """
    title: str = Field(..., min_length=1, max_length=200, description="Task title")
    description: Optional[str] = Field(None, max_length=1000, description="Task description")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Validate title is not empty after stripping whitespace."""
        if not v or not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip()


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
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class TaskListResponse(BaseModel):
    """
    Response schema for paginated task list.
    """
    tasks: list[TaskResponse] = Field(..., description="List of tasks")
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
async def get_user_tasks(
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
async def create_user_task(
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
        session=session
    )

    # Convert to response schema
    return TaskResponse(
        id=task.id,
        user_id=task.user_id,
        title=task.title,
        description=task.description,
        completed=task.completed,
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
async def get_user_task(
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
async def update_user_task(
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
async def delete_user_task(
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
async def complete_task_endpoint(
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
async def uncomplete_task_endpoint(
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
        created_at=task.created_at,
        updated_at=task.updated_at
    )
