"""
MCP Tool: Add Task

Creates a new task for the authenticated user.
Phase V: Supports due_date, priority, tags.
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from src.db.session import get_session
from src.services.task import create_task


async def add_task(
    user_id: str,
    title: str,
    description: Optional[str] = None,
    due_date: Optional[str] = None,
    priority: str = "MEDIUM",
    tags: Optional[List[str]] = None
) -> dict:
    """
    T025: Create a new task via MCP tool with advanced fields.

    Phase V: Adds support for due_date, priority, and tags.
    Publishes task-created event to Kafka after creation.

    Args:
        user_id: User UUID from JWT token
        title: Task title (1-200 characters)
        description: Optional task description (max 1000 characters)
        due_date: Optional due date (ISO 8601 string, e.g., "2026-02-15T10:00:00Z")
        priority: Task priority (LOW/MEDIUM/HIGH, default MEDIUM)
        tags: Optional list of tags (max 10 tags, max 50 chars each)

    Returns:
        Dict with success status and task data:
        {
            "success": True,
            "message": "Task created successfully",
            "data": {
                "id": 1,
                "title": "Buy groceries",
                "description": "Milk, eggs, bread",
                "completed": False,
                "user_id": "uuid",
                "created_at": "2026-02-06T12:00:00",
                "due_date": "2026-02-15T10:00:00Z",
                "priority": "HIGH",
                "tags": ["work", "urgent"]
            }
        }
    """
    try:
        # Get database session
        for session in get_session():
            # Call task service to create task with advanced fields
            task = create_task(
                title=title,
                description=description,
                user_id=user_id,
                session=session,
                due_date=due_date,
                priority=priority,
                tags=tags
            )

            # Publish task-created event to Kafka
            try:
                from src.services.event_publisher import EventPublisher
                task_data = {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "completed": task.completed,
                    "due_date": task.due_date.isoformat() if task.due_date else None,
                    "priority": task.priority,
                    "tags": task.tags,
                    "user_id": task.user_id,
                }
                EventPublisher.publish_task_created(
                    task_id=task.id,
                    user_id=user_id,
                    task_data=task_data
                )
            except Exception as kafka_error:
                # Log but don't fail if Kafka publish fails
                import logging
                logging.getLogger(__name__).warning(f"Failed to publish to Kafka: {kafka_error}")

            # Return structured response
            return {
                "success": True,
                "message": "Task created successfully",
                "data": {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "completed": task.completed,
                    "user_id": task.user_id,
                    "created_at": task.created_at.isoformat(),
                    "due_date": task.due_date.isoformat() if task.due_date else None,
                    "priority": task.priority,
                    "tags": task.tags,
                }
            }

    except Exception as e:
        # Return error response
        return {
            "success": False,
            "message": str(e),
            "data": None
        }
