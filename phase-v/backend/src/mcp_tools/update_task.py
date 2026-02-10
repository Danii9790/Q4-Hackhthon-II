"""
MCP Tool: Update Task

Updates a task's fields for the authenticated user.
Phase V: Supports due_date, priority, tags.
"""
from typing import Optional, List
from sqlalchemy.orm import Session

from src.db.session import get_session
from src.services.task import update_task as service_update_task, get_task


async def update_task(
    user_id: str,
    task_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    due_date: Optional[str] = None,
    priority: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> dict:
    """
    T026: Update a task via MCP tool with advanced fields.

    Phase V: Adds support for updating due_date, priority, and tags.
    Publishes task-updated event to Kafka after update.

    Args:
        user_id: User UUID from JWT token
        task_id: Task's unique identifier
        title: Optional new title (1-200 characters)
        description: Optional new description (max 1000 characters)
        due_date: Optional new due date (ISO 8601 string, or None to remove)
        priority: Optional new priority (LOW/MEDIUM/HIGH)
        tags: Optional new tags list (replaces existing tags)

    Returns:
        Dict with success status and updated task:
        {
            "success": True,
            "message": "Task updated successfully",
            "data": {
                "id": 1,
                "title": "New title",
                "description": "New description",
                "completed": False,
                "due_date": "2026-02-20T10:00:00Z",
                "priority": "HIGH",
                "tags": ["work"],
                "updated_at": "2026-02-06T16:00:00"
            }
        }
    """
    try:
        # Get database session
        for session in get_session():
            # Get old task data for audit trail
            old_task = get_task(task_id=task_id, user_id=user_id, session=session)
            old_data = {
                "title": old_task.title,
                "description": old_task.description,
                "due_date": old_task.due_date.isoformat() if old_task.due_date else None,
                "priority": old_task.priority,
                "tags": old_task.tags,
            }

            # Call task service to update task
            task = service_update_task(
                task_id=task_id,
                user_id=user_id,
                title=title,
                description=description,
                due_date=due_date,
                priority=priority,
                tags=tags,
                session=session
            )

            # Publish task-updated event to Kafka
            try:
                from src.services.event_publisher import EventPublisher
                new_data = {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "completed": task.completed,
                    "due_date": task.due_date.isoformat() if task.due_date else None,
                    "priority": task.priority,
                    "tags": task.tags,
                    "user_id": task.user_id,
                }

                # Determine what changed
                changes = []
                if old_data["title"] != new_data["title"]:
                    changes.append("title")
                if old_data["description"] != new_data["description"]:
                    changes.append("description")
                if old_data["due_date"] != new_data["due_date"]:
                    changes.append("due_date")
                if old_data["priority"] != new_data["priority"]:
                    changes.append("priority")
                if old_data["tags"] != new_data["tags"]:
                    changes.append("tags")

                EventPublisher.publish_task_updated(
                    task_id=task.id,
                    user_id=user_id,
                    old_data=old_data,
                    new_data=new_data,
                    changes=changes
                )
            except Exception as kafka_error:
                # Log but don't fail if Kafka publish fails
                import logging
                logging.getLogger(__name__).warning(f"Failed to publish to Kafka: {kafka_error}")

            # Return structured response
            return {
                "success": True,
                "message": "Task updated successfully",
                "data": {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "completed": task.completed,
                    "due_date": task.due_date.isoformat() if task.due_date else None,
                    "priority": task.priority,
                    "tags": task.tags,
                    "updated_at": task.updated_at.isoformat()
                }
            }

    except Exception as e:
        # Return error response
        return {
            "success": False,
            "message": str(e),
            "data": None
        }
