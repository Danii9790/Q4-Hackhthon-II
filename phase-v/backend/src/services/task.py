"""
Task service for Todo Application.

This module provides business logic for task CRUD operations,
including validation and database interactions.
Phase V: Advanced task management with due dates, priorities, tags, filtering, sorting, searching.
"""
from datetime import datetime, timezone
from typing import Optional, Tuple, List
from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from src.models.task import Task, Priority


def create_task(
    title: str,
    description: Optional[str],
    user_id: str,
    session: Session,
    due_date: Optional[datetime] = None,
    priority: str = "MEDIUM",
    tags: Optional[List[str]] = None
) -> Task:
    """
    Create a new task for a user.

    Phase V: Supports advanced fields (due_date, priority, tags).

    Args:
        title: Task title (1-200 characters)
        description: Optional task description (max 1000 characters)
        user_id: ID of the user who owns the task
        session: Database session
        due_date: Optional due date (T039: validated to be datetime, stored in UTC)
        priority: Task priority (T037: validated to be LOW/MEDIUM/HIGH, default MEDIUM)
        tags: Optional list of tags (T038: max 10 tags, max 50 chars each)

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

    # T037: Validate priority enum
    valid_priorities = ["LOW", "MEDIUM", "HIGH"]
    if priority not in valid_priorities:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_PRIORITY",
                "message": f"Priority must be one of {valid_priorities}"
            }
        )

    # T038: Validate tags array
    if tags is not None:
        if not isinstance(tags, list):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_TAGS",
                    "message": "Tags must be a list"
                }
            )
        if len(tags) > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_TAGS",
                    "message": "Maximum 10 tags allowed"
                }
            )
        for tag in tags:
            if not isinstance(tag, str) or len(tag) > 50:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "INVALID_TAGS",
                        "message": "Each tag must be a string of max 50 characters"
                    }
                )

    # T039: Validate and normalize due_date to UTC
    if due_date is not None:
        if isinstance(due_date, str):
            # Parse ISO string if needed
            try:
                due_date = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "INVALID_DUE_DATE",
                        "message": "Due date must be a valid ISO 8601 datetime"
                    }
                )
        # Ensure timezone-aware, convert to UTC
        if due_date.tzinfo is None:
            due_date = due_date.replace(tzinfo=timezone.utc)
        else:
            due_date = due_date.astimezone(timezone.utc)

    # Create task with all fields
    now = datetime.now(timezone.utc)
    task = Task(
        title=title.strip(),
        description=description,
        user_id=user_id,
        completed=False,
        due_date=due_date,
        priority=priority,
        tags=tags or [],
        created_at=now,
        updated_at=now
    )

    try:
        session.add(task)
        session.commit()
        session.refresh(task)

        # T103: Log to audit trail
        from src.services.audit_service import AuditService
        try:
            AuditService.log_task_created(
                session=session,
                task_id=task.id,
                user_id=user_id,
                task_data={
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "completed": task.completed,
                    "due_date": task.due_date.isoformat() if task.due_date else None,
                    "priority": task.priority,
                    "tags": task.tags,
                }
            )
        except Exception as audit_error:
            # Log but don't fail the operation
            import logging
            logging.getLogger(__name__).warning(f"Failed to log audit event: {audit_error}")

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
) -> Tuple[List[Task], int]:
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


def list_tasks_advanced(
    user_id: str,
    session: Session,
    offset: int = 0,
    limit: int = 50,
    priority: Optional[str] = None,
    tags: Optional[List[str]] = None,
    due_before: Optional[datetime] = None,
    due_after: Optional[datetime] = None,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc"
) -> Tuple[List[Task], int]:
    """
    T036: List tasks with advanced filtering, sorting, and searching.

    Supports filtering by:
    - priority: Filter by priority level (LOW, MEDIUM, HIGH)
    - tags: Filter by tags (tasks must have ALL specified tags)
    - due_before: Filter tasks due before this date
    - due_after: Filter tasks due after this date
    - search: Full-text search in title and description

    Supports sorting by:
    - created_at, updated_at, due_date, priority, completed_at
    - sort_order: asc or desc

    Args:
        user_id: ID of the user
        session: Database session
        offset: Pagination offset
        limit: Max results to return
        priority: Optional priority filter
        tags: Optional list of tags to filter by
        due_before: Optional due date upper bound
        due_after: Optional due date lower bound
        search: Optional search query for title/description
        sort_by: Field to sort by (default: created_at)
        sort_order: Sort direction (default: desc)

    Returns:
        Tuple of (list of tasks, total count)

    Raises:
        HTTPException 400: If invalid sort parameters
        HTTPException 500: If database operation fails
    """
    try:
        # Build base query filtered by user
        base_query = select(Task).where(Task.user_id == user_id)

        # Apply filters
        if priority:
            # Validate priority
            valid_priorities = ["LOW", "MEDIUM", "HIGH"]
            if priority not in valid_priorities:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "INVALID_PRIORITY",
                        "message": f"Priority must be one of {valid_priorities}"
                    }
                )
            base_query = base_query.where(Task.priority == priority)

        if tags:
            # Filter by tags - task must contain ALL specified tags
            # Using PostgreSQL JSON contains operator
            for tag in tags:
                base_query = base_query.where(Task.tags.contains([tag]))

        if due_before:
            base_query = base_query.where(Task.due_date <= due_before)

        if due_after:
            base_query = base_query.where(Task.due_date >= due_after)

        if search:
            # Full-text search in title and description (case-insensitive)
            search_term = f"%{search}%"
            base_query = base_query.where(
                or_(
                    Task.title.ilike(search_term),
                    Task.description.ilike(search_term)
                )
            )

        # Get total count after filtering
        count_query = select(func.count()).select_from(base_query.subquery())
        total_count = session.execute(count_query).scalar_one()

        # Validate sort_by field
        valid_sort_fields = ["created_at", "updated_at", "due_date", "priority", "completed_at"]
        if sort_by not in valid_sort_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_SORT_FIELD",
                    "message": f"Sort field must be one of {valid_sort_fields}"
                }
            )

        # Validate sort_order
        if sort_order not in ["asc", "desc"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_SORT_ORDER",
                    "message": "Sort order must be 'asc' or 'desc'"
                }
            )

        # Apply sorting
        sort_column = getattr(Task, sort_by)
        if sort_order == "asc":
            query = base_query.order_by(sort_column.asc())
        else:
            query = base_query.order_by(sort_column.desc())

        # Apply pagination
        query = query.offset(offset).limit(limit)
        tasks = session.execute(query).scalars().all()

        return list(tasks), total_count

    except HTTPException:
        raise
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
    session: Session = None,
    due_date: Optional[datetime] = None,
    priority: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> Task:
    """
    Update a task's title, description, and/or advanced fields.

    Phase V: Supports updating due_date, priority, tags.

    Args:
        task_id: ID of the task to update
        user_id: ID of the user who owns the task
        title: New title (optional, 1-200 characters if provided)
        description: New description (optional, max 1000 characters)
        session: Database session
        due_date: New due date (optional, None to remove)
        priority: New priority (optional, LOW/MEDIUM/HIGH)
        tags: New tags list (optional, replaces existing tags)

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

        # Update due_date if provided
        if due_date is not None:
            if isinstance(due_date, str):
                try:
                    due_date = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "code": "INVALID_DUE_DATE",
                            "message": "Due date must be a valid ISO 8601 datetime"
                        }
                    )
            if due_date.tzinfo is None:
                due_date = due_date.replace(tzinfo=timezone.utc)
            else:
                due_date = due_date.astimezone(timezone.utc)
            task.due_date = due_date

        # Update priority if provided
        if priority is not None:
            valid_priorities = ["LOW", "MEDIUM", "HIGH"]
            if priority not in valid_priorities:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "INVALID_PRIORITY",
                        "message": f"Priority must be one of {valid_priorities}"
                    }
                )
            task.priority = priority

        # Update tags if provided
        if tags is not None:
            if not isinstance(tags, list):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "INVALID_TAGS",
                        "message": "Tags must be a list"
                    }
                )
            if len(tags) > 10:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "INVALID_TAGS",
                        "message": "Maximum 10 tags allowed"
                    }
                )
            for tag in tags:
                if not isinstance(tag, str) or len(tag) > 50:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "code": "INVALID_TAGS",
                            "message": "Each tag must be a string of max 50 characters"
                        }
                    )
            task.tags = tags

        # Update timestamp
        task.updated_at = datetime.now(timezone.utc)

        # Commit changes
        session.commit()
        session.refresh(task)

        # T104: Log to audit trail
        from src.services.audit_service import AuditService
        try:
            AuditService.log_task_updated(
                session=session,
                task_id=task.id,
                user_id=user_id,
                old_data={},  # TODO: Track before state
                new_data={
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "completed": task.completed,
                    "due_date": task.due_date.isoformat() if task.due_date else None,
                    "priority": task.priority,
                    "tags": task.tags,
                },
                changes=["updated"]  # TODO: Track specific changes
            )
        except Exception as audit_error:
            import logging
            logging.getLogger(__name__).warning(f"Failed to log audit event: {audit_error}")

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

    Phase V: Also sets completed_at timestamp.

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
        task.completed_at = datetime.now(timezone.utc)
        task.updated_at = datetime.now(timezone.utc)

        # Commit changes
        session.commit()
        session.refresh(task)

        # T105: Log to audit trail
        from src.services.audit_service import AuditService
        try:
            AuditService.log_task_completed(
                session=session,
                task_id=task.id,
                user_id=user_id,
                task_data={
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "completed": task.completed,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                }
            )
        except Exception as audit_error:
            import logging
            logging.getLogger(__name__).warning(f"Failed to log audit event: {audit_error}")

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

    Phase V: Also clears completed_at timestamp.

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
        task.completed_at = None
        task.updated_at = datetime.now(timezone.utc)

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

        # T105: Capture task data for audit before deletion
        task_data_for_audit = {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "completed": task.completed,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "priority": task.priority,
            "tags": task.tags,
        }

        # Delete the task
        session.delete(task)
        session.commit()

        # T105: Log to audit trail (after commit, in separate try/except)
        from src.services.audit_service import AuditService
        try:
            AuditService.log_task_deleted(
                session=session,
                task_id=task_id,
                user_id=user_id,
                task_data=task_data_for_audit
            )
        except Exception as audit_error:
            import logging
            logging.getLogger(__name__).warning(f"Failed to log audit event: {audit_error}")

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


def set_task_priority(task_id: int, user_id: str, priority: str, session: Session) -> Task:
    """
    Set the priority of a task.

    Args:
        task_id: ID of the task
        user_id: ID of the user who owns the task
        priority: New priority value (LOW, MEDIUM, HIGH)
        session: Database session

    Returns:
        Updated Task model instance

    Raises:
        HTTPException 400: If invalid priority
        HTTPException 404: If task not found
        HTTPException 500: If database operation fails
    """
    try:
        # Validate priority
        valid_priorities = ["LOW", "MEDIUM", "HIGH"]
        if priority not in valid_priorities:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_PRIORITY",
                    "message": f"Priority must be one of {valid_priorities}"
                }
            )

        # Get task (includes ownership verification)
        task = get_task(task_id=task_id, user_id=user_id, session=session)

        # Update priority
        task.priority = priority
        task.updated_at = datetime.now(timezone.utc)

        session.commit()
        session.refresh(task)
        return task

    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "DATABASE_ERROR",
                "message": "Failed to update task priority"
            }
        )


def set_task_due_date(task_id: int, user_id: str, due_date: Optional[datetime], session: Session) -> Task:
    """
    Set the due date of a task.

    Args:
        task_id: ID of the task
        user_id: ID of the user who owns the task
        due_date: New due date (None to remove due date)
        session: Database session

    Returns:
        Updated Task model instance

    Raises:
        HTTPException 400: If invalid due date format
        HTTPException 404: If task not found
        HTTPException 500: If database operation fails
    """
    try:
        # Validate and normalize due_date to UTC
        if due_date is not None:
            if isinstance(due_date, str):
                # Parse ISO string if needed
                try:
                    due_date = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "code": "INVALID_DUE_DATE",
                            "message": "Due date must be a valid ISO 8601 datetime"
                        }
                    )
            # Ensure timezone-aware, convert to UTC
            if due_date.tzinfo is None:
                due_date = due_date.replace(tzinfo=timezone.utc)
            else:
                due_date = due_date.astimezone(timezone.utc)

        # Get task (includes ownership verification)
        task = get_task(task_id=task_id, user_id=user_id, session=session)

        # Update due date
        task.due_date = due_date
        task.updated_at = datetime.now(timezone.utc)

        session.commit()
        session.refresh(task)
        return task

    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "DATABASE_ERROR",
                "message": "Failed to update task due date"
            }
        )


def add_task_tags(task_id: int, user_id: str, tags: List[str], session: Session) -> Task:
    """
    Add tags to a task (appends to existing tags).

    Args:
        task_id: ID of the task
        user_id: ID of the user who owns the task
        tags: List of tags to add
        session: Database session

    Returns:
        Updated Task model instance

    Raises:
        HTTPException 400: If invalid tags
        HTTPException 404: If task not found
        HTTPException 500: If database operation fails
    """
    try:
        # Validate tags array
        if not isinstance(tags, list):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_TAGS",
                    "message": "Tags must be a list"
                }
            )

        for tag in tags:
            if not isinstance(tag, str) or len(tag) > 50:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "code": "INVALID_TAGS",
                        "message": "Each tag must be a string of max 50 characters"
                    }
                )

        # Get task (includes ownership verification)
        task = get_task(task_id=task_id, user_id=user_id, session=session)

        # Merge tags: add new tags without duplicates
        existing_tags = set(task.tags or [])
        new_tags = set(tags)
        merged_tags = list(existing_tags.union(new_tags))

        # Validate max 10 tags
        if len(merged_tags) > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "INVALID_TAGS",
                    "message": "Maximum 10 tags allowed"
                }
            )

        # Update tags
        task.tags = merged_tags
        task.updated_at = datetime.now(timezone.utc)

        session.commit()
        session.refresh(task)
        return task

    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "DATABASE_ERROR",
                "message": "Failed to update task tags"
            }
        )
