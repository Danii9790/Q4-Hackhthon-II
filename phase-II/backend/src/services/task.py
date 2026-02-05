"""
Task service for Todo Application.

This module provides business logic for task CRUD operations,
including validation and database interactions.
"""
from datetime import datetime
from typing import Optional, Tuple
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from src.models.task import Task


def create_task(
    title: str,
    description: Optional[str],
    user_id: str,
    session: Session
) -> Task:
    """
    Create a new task for a user.

    Args:
        title: Task title (1-200 characters)
        description: Optional task description (max 1000 characters)
        user_id: ID of the user who owns the task
        session: Database session

    Returns:
        Created Task model instance

    Raises:
        HTTPException 400: If validation fails
        HTTPException 500: If database operation fails
    """
    # Validate title length
    if not title or len(title.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_TITLE",
                "message": "Title is required"
            }
        )

    if len(title) > 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_TITLE",
                "message": "Title must be 200 characters or less"
            }
        )

    # Validate description length
    if description is not None and len(description) > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_DESCRIPTION",
                "message": "Description must be 1000 characters or less"
            }
        )

    # Create task with default values
    now = datetime.utcnow()
    task = Task(
        title=title.strip(),
        description=description,
        user_id=user_id,
        completed=False,
        created_at=now,
        updated_at=now
    )

    try:
        session.add(task)
        session.commit()
        session.refresh(task)
        return task
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "DATABASE_ERROR",
                "message": "Failed to create task"
            }
        )


def list_tasks(
    user_id: str,
    offset: int = 0,
    limit: int = 50,
    session: Session = None
) -> Tuple[list[Task], int]:
    """
    List all tasks for a user with pagination.

    Args:
        user_id: ID of the user
        offset: Number of tasks to skip (default: 0)
        limit: Maximum number of tasks to return (default: 50)
        session: Database session

    Returns:
        Tuple of (list of tasks, total count)

    Raises:
        HTTPException 500: If database operation fails
    """
    try:
        # Build base query filtered by user
        base_query = select(Task).where(Task.user_id == user_id)

        # Get total count
        count_query = select(func.count()).select_from(base_query.subquery())
        total_count = session.execute(count_query).scalar_one()

        # Get paginated tasks ordered by created_at DESC (most recent first)
        query = base_query.order_by(Task.created_at.desc()).offset(offset).limit(limit)
        tasks = session.execute(query).scalars().all()

        return list(tasks), total_count

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "DATABASE_ERROR",
                "message": "Failed to retrieve tasks"
            }
        )


def get_task(task_id: int, user_id: str, session: Session) -> Task:
    """
    Get a specific task by ID with user ownership verification.

    Args:
        task_id: ID of the task to retrieve
        user_id: ID of the user requesting the task
        session: Database session

    Returns:
        Task model instance

    Raises:
        HTTPException 404: If task not found or doesn't belong to user
        HTTPException 500: If database operation fails
    """
    try:
        # Query task by ID and user_id
        task = session.execute(
            select(Task).where(Task.id == task_id, Task.user_id == user_id)
        ).scalar_one_or_none()

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "TASK_NOT_FOUND",
                    "message": f"Task with ID {task_id} not found"
                }
            )

        return task

    except HTTPException:
        # Re-raise HTTP exceptions (404)
        raise
    except Exception as e:
        # Handle other exceptions
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "DATABASE_ERROR",
                "message": "Failed to retrieve task"
            }
        )


def update_task(
    task_id: int,
    user_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    session: Session = None
) -> Task:
    """
    Update a task's title and/or description.

    Args:
        task_id: ID of the task to update
        user_id: ID of the user who owns the task
        title: New title (optional, 1-200 characters if provided)
        description: New description (optional, max 1000 characters)
        session: Database session

    Returns:
        Updated Task model instance

    Raises:
        HTTPException 400: If validation fails
        HTTPException 404: If task not found
        HTTPException 500: If database operation fails
    """
    try:
        # Get task (includes ownership verification)
        task = get_task(task_id=task_id, user_id=user_id, session=session)

        # Validate and update title if provided
        if title is not None:
            if not title or len(title.strip()) == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "INVALID_TITLE",
                        "message": "Title cannot be empty"
                    }
                )
            if len(title) > 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "INVALID_TITLE",
                        "message": "Title must be 200 characters or less"
                    }
                )
            task.title = title.strip()

        # Validate and update description if provided
        if description is not None:
            if len(description) > 1000:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "INVALID_DESCRIPTION",
                        "message": "Description must be 1000 characters or less"
                    }
                )
            task.description = description

        # Update timestamp
        task.updated_at = datetime.utcnow()

        # Commit changes
        session.commit()
        session.refresh(task)

        return task

    except HTTPException:
        # Re-raise HTTP exceptions
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "DATABASE_ERROR",
                "message": "Failed to update task"
            }
        )


def complete_task(task_id: int, user_id: str, session: Session) -> Task:
    """
    Mark a task as completed.

    Args:
        task_id: ID of the task to complete
        user_id: ID of the user who owns the task
        session: Database session

    Returns:
        Updated Task model instance

    Raises:
        HTTPException 404: If task not found
        HTTPException 500: If database operation fails
    """
    try:
        # Get task (includes ownership verification)
        task = get_task(task_id=task_id, user_id=user_id, session=session)

        # Mark as completed
        task.completed = True
        task.updated_at = datetime.utcnow()

        # Commit changes
        session.commit()
        session.refresh(task)

        return task

    except HTTPException:
        # Re-raise HTTP exceptions
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "DATABASE_ERROR",
                "message": "Failed to complete task"
            }
        )


def uncomplete_task(task_id: int, user_id: str, session: Session) -> Task:
    """
    Mark a task as not completed.

    Args:
        task_id: ID of the task to uncomplete
        user_id: ID of the user who owns the task
        session: Database session

    Returns:
        Updated Task model instance

    Raises:
        HTTPException 404: If task not found
        HTTPException 500: If database operation fails
    """
    try:
        # Get task (includes ownership verification)
        task = get_task(task_id=task_id, user_id=user_id, session=session)

        # Mark as not completed
        task.completed = False
        task.updated_at = datetime.utcnow()

        # Commit changes
        session.commit()
        session.refresh(task)

        return task

    except HTTPException:
        # Re-raise HTTP exceptions
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "DATABASE_ERROR",
                "message": "Failed to uncomplete task"
            }
        )


def delete_task(task_id: int, user_id: str, session: Session) -> None:
    """
    Delete a task from the database.

    This function verifies that:
    1. The task exists
    2. The task belongs to the specified user
    3. Deletes the task from the database

    Args:
        task_id: ID of the task to delete
        user_id: ID of the user who owns the task
        session: Database session

    Returns:
        None (success is indicated by lack of exception)

    Raises:
        HTTPException 404: If task not found
        HTTPException 403: If task doesn't belong to user
        HTTPException 500: If database operation fails
    """
    try:
        # Query task by ID (without user filter to provide better error messages)
        task = session.execute(
            select(Task).where(Task.id == task_id)
        ).scalar_one_or_none()

        # Check if task exists
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "TASK_NOT_FOUND",
                    "message": f"Task with ID {task_id} not found"
                }
            )

        # Verify ownership
        if task.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "FORBIDDEN",
                    "message": "You can only delete your own tasks"
                }
            )

        # Delete the task
        session.delete(task)
        session.commit()

    except HTTPException:
        # Re-raise HTTP exceptions (404, 403)
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "DATABASE_ERROR",
                "message": "Failed to delete task"
            }
        )
