"""
MCP Tool: Set Task Priority

Sets the priority of a task for the authenticated user.
Phase V: New MCP tool.
"""
from sqlalchemy.orm import Session

from src.db.session import get_session
from src.services.task import set_task_priority as service_set_task_priority, get_task


async def set_task_priority(
    user_id: str,
    task_id: int,
    priority: str
) -> dict:
    """
    T030: Set the priority of a task via MCP tool.

    Args:
        user_id: User UUID from JWT token
        task_id: Task's unique identifier
        priority: New priority value (LOW, MEDIUM, HIGH)

    Returns:
        Dict with success status and updated task:
        {
            "success": True,
            "message": "Task priority updated to HIGH",
            "data": {
                "id": 1,
                "title": "Buy groceries",
                "priority": "HIGH",
                "updated_at": "2026-02-06T16:00:00"
            }
        }
    """
    try:
        # Get database session
        for session in get_session():
            # Get old task data for audit trail
            old_task = get_task(task_id=task_id, user_id=user_id, session=session)
            old_priority = old_task.priority

            # Call service to update priority
            task = service_set_task_priority(
                task_id=task_id,
                user_id=user_id,
                priority=priority,
                session=session
            )

            # Publish task-updated event to Kafka
            try:
                from src.services.event_publisher import EventPublisher
                old_data = {
                    "title": old_task.title,
                    "priority": old_priority,
                }
                new_data = {
                    "title": task.title,
                    "priority": task.priority,
                }
                EventPublisher.publish_task_updated(
                    task_id=task.id,
                    user_id=user_id,
                    old_data=old_data,
                    new_data=new_data,
                    changes=["priority"]
                )
            except Exception as kafka_error:
                import logging
                logging.getLogger(__name__).warning(f"Failed to publish to Kafka: {kafka_error}")

            # Return structured response
            return {
                "success": True,
                "message": f"Task priority updated to {priority}",
                "data": {
                    "id": task.id,
                    "title": task.title,
                    "priority": task.priority,
                    "updated_at": task.updated_at.isoformat()
                }
            }

    except Exception as e:
        return {
            "success": False,
            "message": str(e),
            "data": None
        }
