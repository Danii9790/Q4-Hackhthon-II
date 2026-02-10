"""
Audit routes for Todo Application.

This module provides endpoints for querying the audit trail:
- Get audit trail for a specific task
- Get audit trail for all user activity

All endpoints require JWT authentication and verify user ownership.
"""
from typing import Annotated, Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user_id
from src.db import get_session
from src.models.task_event import TaskEvent
from src.services.audit_service import AuditService


# Router configuration
router = APIRouter(prefix="/api", tags=["Audit"])


# ============================================================================
# Request/Response Schemas
# ============================================================================


class AuditEventResponse(BaseModel):
    """
    Response schema for a single audit event.

    Fields:
        id: Event UUID
        event_type: Type of event (created, updated, completed, deleted)
        task_id: ID of the task
        user_id: ID of the user who performed the action
        event_data: JSON data containing before/after state, changes, etc.
        timestamp: When the event occurred (ISO 8601 format)
    """
    id: str = Field(..., description="Event UUID")
    event_type: str = Field(..., description="Type of event")
    task_id: int = Field(..., description="ID of the task")
    user_id: str = Field(..., description="ID of the user who performed the action")
    event_data: dict = Field(..., description="Event data (before/after state, changes)")
    timestamp: str = Field(..., description="When the event occurred (ISO 8601)")

    class Config:
        from_attributes = True


class AuditListResponse(BaseModel):
    """
    Response schema for audit trail list.

    Fields:
        events: List of audit events
        count: Total number of events returned
    """
    events: List[AuditEventResponse] = Field(..., description="List of audit events")
    count: int = Field(..., description="Total number of events returned")


# ============================================================================
# API Endpoints
# ============================================================================


@router.get(
    "/tasks/{task_id}/audit",
    response_model=AuditListResponse,
    summary="Get audit trail for a task",
    description="T106: Retrieve the complete audit trail for a specific task. Returns all events (created, updated, completed, deleted) in descending chronological order.",
    responses={
        200: {"description": "Audit trail retrieved successfully"},
        401: {"description": "Unauthorized - Invalid or missing JWT"},
        403: {"description": "Forbidden - Task doesn't belong to user"},
        404: {"description": "Task not found"},
        500: {"description": "Internal server error"},
    }
)
def get_task_audit_trail(
    task_id: int,
    user_id: Annotated[str, Depends(get_current_user_id)],
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum number of events to return"),
    session: Session = Depends(get_session),
) -> AuditListResponse:
    """
    T106: Get audit trail for a specific task.

    This endpoint returns the complete audit trail for a task, including:
    - Creation event
    - Update events (with before/after state)
    - Completion event
    - Deletion event (if applicable)

    Authentication:
        - Requires valid JWT token
        - User must own the task

    Args:
        task_id: ID of the task to get audit trail for
        user_id: ID of the authenticated user (from JWT)
        limit: Maximum number of events to return (default: 100, max: 1000)
        session: Database session

    Returns:
        AuditListResponse containing list of audit events

    Raises:
        HTTPException 401: If JWT is invalid or missing
        HTTPException 403: If task doesn't belong to user
        HTTPException 404: If task not found
        HTTPException 500: If database operation fails
    """
    try:
        # Import Task model
        from src.models.task import Task

        # Verify task exists and belongs to user
        task = session.query(Task).filter(
            Task.id == task_id,
            Task.user_id == user_id
        ).first()

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "TASK_NOT_FOUND",
                    "message": f"Task with ID {task_id} not found or doesn't belong to you"
                }
            )

        # Get audit trail using service
        events = AuditService.get_task_history(
            session=session,
            task_id=task_id,
            limit=limit
        )

        # Convert to response format
        event_responses = [
            AuditEventResponse(
                id=event.id,
                event_type=event.event_type,
                task_id=event.task_id,
                user_id=event.user_id,
                event_data=event.event_data,
                timestamp=event.timestamp.isoformat()
            )
            for event in events
        ]

        return AuditListResponse(
            events=event_responses,
            count=len(event_responses)
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "DATABASE_ERROR",
                "message": "Failed to retrieve audit trail"
            }
        )


@router.get(
    "/users/{user_id}/audit",
    response_model=AuditListResponse,
    summary="Get audit trail for user activity",
    description="T107: Retrieve the audit trail for all activity performed by a specific user. Returns events across all tasks in descending chronological order.",
    responses={
        200: {"description": "Audit trail retrieved successfully"},
        401: {"description": "Unauthorized - Invalid or missing JWT"},
        403: {"description": "Forbidden - Can only view your own activity"},
        500: {"description": "Internal server error"},
    }
)
def get_user_audit_trail(
    path_user_id: str,
    user_id: Annotated[str, Depends(get_current_user_id)],
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum number of events to return"),
    session: Session = Depends(get_session),
) -> AuditListResponse:
    """
    T107: Get audit trail for user activity.

    This endpoint returns the complete audit trail for a user's activity,
    including all operations across all tasks they own.

    Authentication:
        - Requires valid JWT token
        - Users can only view their own audit trail

    Args:
        path_user_id: User ID from the URL path
        user_id: ID of the authenticated user (from JWT)
        limit: Maximum number of events to return (default: 100, max: 1000)
        session: Database session

    Returns:
        AuditListResponse containing list of audit events

    Raises:
        HTTPException 401: If JWT is invalid or missing
        HTTPException 403: If trying to view another user's activity
        HTTPException 500: If database operation fails
    """
    try:
        # Verify user is requesting their own activity
        if path_user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "FORBIDDEN",
                    "message": "You can only view your own audit trail"
                }
            )

        # Get audit trail using service
        events = AuditService.get_user_activity(
            session=session,
            user_id=user_id,
            limit=limit
        )

        # Convert to response format
        event_responses = [
            AuditEventResponse(
                id=event.id,
                event_type=event.event_type,
                task_id=event.task_id,
                user_id=event.user_id,
                event_data=event.event_data,
                timestamp=event.timestamp.isoformat()
            )
            for event in events
        ]

        return AuditListResponse(
            events=event_responses,
            count=len(event_responses)
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "DATABASE_ERROR",
                "message": "Failed to retrieve audit trail"
            }
        )
