"""
MCP Tool: Set Task Due Date

Sets the due date of a task for the authenticated user.
Phase V: New MCP tool.
"""
from typing import Optional
from sqlalchemy.orm import Session

from src.db.session import get_session
from src.services.task import set_task_due_date as service_set_task_due_date, get_task


async def set_task_due_date(
    user_id: str,
    task_id: int,
    due_date: Optional[str]
) -> dict:
    """
    T031: Set the due date of a task via MCP tool.

    Args:
        user_id: User UUID from JWT token
        task_id: Task's unique identifier
        due_date: New due date (ISO 8601 string, or None to remove due date)

    Returns:
        Dict with success status and updated task:
        {
            "success": True,
            "message": "Task due date updated to 2026-02-15T10:00:00Z",
            "data": {
                "id": 1,
                "title": "Buy groceries",
                "due_date": "2026-02-15T10:00:00Z",
                "updated_at": "2026-02-06T16:00:00"
            }
        }
    """
    try:
        # Get database session
        for session in get_session():
            # Get old task data for audit trail
            old_task = get_task(task_id=task_id, user_id=user_id, session=session)
            old_due_date = old_task.due_date.isoformat() if old_task.due_date else None

            # Call service to update due date
            # Parse ISO string to datetime for service
            due_date_dt = None
            if due_date is not None:
                from datetime import datetime, timezone
                due_date_dt = datetime.fromisoformat(due_date.replace('Z', '+00:00'))

            task = service_set_task_due_date(
                task_id=task_id,
                user_id=user_id,
                due_date=due_date_dt,
                session=session
            )

            # Publish task-updated event to Kafka
            try:
                from src.services.event_publisher import EventPublisher
                old_data = {
                    "title": old_task.title,
                    "due_date": old_due_date,
                }
                new_data = {
                    "title": task.title,
                    "due_date": task.due_date.isoformat() if task.due_date else None,
                }
                EventPublisher.publish_task_updated(
                    task_id=task.id,
                    user_id=user_id,
                    old_data=old_data,
                    new_data=new_data,
                    changes=["due_date"]
                )
            except Exception as kafka_error:
                import logging
                logging.getLogger(__name__).warning(f"Failed to publish to Kafka: {kafka_error}")

            # Return structured response
            return {
                "success": True,
                "message": f"Task due date updated to {due_date or 'removed'}",
                "data": {
                    "id": task.id,
                    "title": task.title,
                    "due_date": task.due_date.isoformat() if task.due_date else None,
                    "updated_at": task.updated_at.isoformat()
                }
            }

    except Exception as e:
        return {
            "success": False,
            "message": str(e),
            "data": None
        }
