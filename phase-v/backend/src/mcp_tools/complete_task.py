"""
MCP Tool: Complete Task

Marks a task as completed for the authenticated user.
Phase V: Publishes task-completed event to Kafka.
"""
from sqlalchemy.orm import Session

from src.db.session import get_session
from src.services.task import complete_task as service_complete_task


async def complete_task(
    user_id: str,
    task_id: int
) -> dict:
    """
    T027, T066: Mark a task as completed via MCP tool.

    Phase V: Publishes task-completed event to Kafka.
    T066: Returns next_occurrence info for recurring tasks.

    Args:
        user_id: User UUID from JWT token
        task_id: Task's unique identifier

    Returns:
        Dict with success status and updated task:
        {
            "success": True,
            "message": "Task marked as completed",
            "data": {
                "id": 1,
                "title": "Buy groceries",
                "completed": True,
                "completed_at": "2026-02-06T15:30:00Z",
                "updated_at": "2026-02-06T15:30:00",
                "next_occurrence": {
                    "recurring_task_id": "uuid",
                    "next_date": "2026-02-13T10:00:00Z",
                    "frequency": "WEEKLY"
                }
            }
        }
    """
    try:
        # Get database session
        for session in get_session():
            # Call task service to complete task
            task = service_complete_task(
                task_id=task_id,
                user_id=user_id,
                session=session
            )

            # T066: Check if this is a recurring task and get next occurrence info
            next_occurrence_info = None
            if task.recurring_task_id:
                from src.models.recurring_task import RecurringTask
                recurring_template = session.query(RecurringTask).filter(
                    RecurringTask.id == task.recurring_task_id
                ).first()

                if recurring_template:
                    next_occurrence_info = {
                        "recurring_task_id": recurring_template.id,
                        "next_date": recurring_template.next_occurrence.isoformat(),
                        "frequency": recurring_template.frequency,
                        "title": recurring_template.title,
                    }

            # Publish task-completed event to Kafka
            try:
                from src.services.event_publisher import EventPublisher
                task_data = {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "completed": task.completed,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                    "due_date": task.due_date.isoformat() if task.due_date else None,
                    "priority": task.priority,
                    "tags": task.tags,
                    "user_id": task.user_id,
                    "recurring_task_id": task.recurring_task_id,
                }
                EventPublisher.publish_task_completed(
                    task_id=task.id,
                    user_id=user_id,
                    task_data=task_data
                )
            except Exception as kafka_error:
                # Log but don't fail if Kafka publish fails
                import logging
                logging.getLogger(__name__).warning(f"Failed to publish to Kafka: {kafka_error}")

            # Build response data
            response_data = {
                "id": task.id,
                "title": task.title,
                "completed": task.completed,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                "updated_at": task.updated_at.isoformat()
            }

            # T066: Add next occurrence info for recurring tasks
            if next_occurrence_info:
                response_data["next_occurrence"] = next_occurrence_info

            # Return structured response
            message = f"Task '{task.title}' marked as completed"
            if next_occurrence_info:
                message += f". Next occurrence scheduled for {next_occurrence_info['next_date']}"

            return {
                "success": True,
                "message": message,
                "data": response_data
            }

    except Exception as e:
        # Return error response
        return {
            "success": False,
            "message": str(e),
            "data": None
        }
