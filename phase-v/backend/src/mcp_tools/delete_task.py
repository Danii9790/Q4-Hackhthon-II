"""
MCP Tool: Delete Task

Deletes a task for the authenticated user.
Phase V: Publishes task-deleted event to Kafka.
"""
from sqlalchemy.orm import Session

from src.db.session import get_session
from src.services.task import delete_task as service_delete_task


async def delete_task(
    user_id: str,
    task_id: int
) -> dict:
    """
    T028: Delete a task via MCP tool.

    Phase V: Publishes task-deleted event to Kafka.

    Args:
        user_id: User UUID from JWT token
        task_id: Task's unique identifier

    Returns:
        Dict with success status and confirmation:
        {
            "success": True,
            "message": "Task 'Buy groceries' deleted successfully",
            "data": {
                "id": 1,
                "title": "Buy groceries",
                "completed": False
            }
        }
    """
    try:
        # Get database session
        for session in get_session():
            # First get the task to return its info and for Kafka event
            from src.models.task import Task
            from sqlalchemy import select

            stmt = select(Task).where(Task.id == task_id, Task.user_id == user_id)
            task = session.execute(stmt).scalar_one_or_none()

            if not task:
                return {
                    "success": False,
                    "message": "Task not found",
                    "data": None
                }

            # Store task data for Kafka event before deleting
            deleted_data = {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "completed": task.completed,
                "due_date": task.due_date.isoformat() if task.due_date else None,
                "priority": task.priority,
                "tags": task.tags,
                "user_id": task.user_id,
            }
            task_title = task.title

            # Delete the task
            service_delete_task(
                task_id=task_id,
                user_id=user_id,
                session=session
            )

            # Publish task-deleted event to Kafka
            try:
                from src.services.event_publisher import EventPublisher
                EventPublisher.publish_task_deleted(
                    task_id=task_id,
                    user_id=user_id,
                    deleted_data=deleted_data
                )
            except Exception as kafka_error:
                # Log but don't fail if Kafka publish fails
                import logging
                logging.getLogger(__name__).warning(f"Failed to publish to Kafka: {kafka_error}")

            # Return structured response
            return {
                "success": True,
                "message": f"Task '{task_title}' deleted successfully",
                "data": {
                    "id": task_id,
                    "title": task_title,
                    "completed": deleted_data["completed"]
                }
            }

    except Exception as e:
        # Return error response
        return {
            "success": False,
            "message": str(e),
            "data": None
        }
