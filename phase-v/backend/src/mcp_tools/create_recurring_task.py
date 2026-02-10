"""
MCP Tool: Create Recurring Task

Creates a recurring task template with automatic occurrence generation.
"""
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session

from src.db.session import get_session
from src.services.recurring_service import create_recurring_task


async def create_recurring_task(
    user_id: str,
    title: str,
    frequency: str,
    description: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> dict:
    """
    T065: Create a recurring task template via MCP tool.

    Creates a recurring task template that automatically generates new task
    occurrences when the current one is completed.

    Args:
        user_id: User UUID from JWT token
        title: Task title (1-200 characters)
        frequency: Recurrence frequency (DAILY/WEEKLY/MONTHLY)
        description: Optional task description (max 1000 characters)
        start_date: First occurrence date (ISO 8601 string, defaults to now)
        end_date: Optional end date for recurrence (ISO 8601 string, null for infinite)

    Returns:
        Dict with success status and recurring task data:
        {
            "success": True,
            "message": "Recurring task created successfully",
            "data": {
                "id": "uuid",
                "title": "Weekly team meeting",
                "description": "Weekly sync with the team",
                "frequency": "WEEKLY",
                "start_date": "2026-02-10T10:00:00Z",
                "end_date": null,
                "next_occurrence": "2026-02-10T10:00:00Z",
                "user_id": "uuid"
            }
        }
    """
    try:
        # Parse dates
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        else:
            start_dt = datetime.now()

        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        else:
            end_dt = None

        # Get database session
        for session in get_session():
            # Call recurring task service to create template
            recurring_task = create_recurring_task(
                user_id=user_id,
                title=title,
                description=description,
                frequency=frequency,
                start_date=start_dt,
                end_date=end_dt,
                session=session
            )

            # Publish recurring-task-created event to Kafka
            try:
                from src.services.event_publisher import EventPublisher
                recurring_task_data = {
                    "id": recurring_task.id,
                    "title": recurring_task.title,
                    "description": recurring_task.description,
                    "frequency": recurring_task.frequency,
                    "start_date": recurring_task.start_date.isoformat(),
                    "end_date": recurring_task.end_date.isoformat() if recurring_task.end_date else None,
                    "next_occurrence": recurring_task.next_occurrence.isoformat(),
                    "user_id": recurring_task.user_id,
                }
                EventPublisher.publish_recurring_task_created(
                    recurring_task_id=recurring_task.id,
                    user_id=user_id,
                    recurring_task_data=recurring_task_data
                )
            except Exception as kafka_error:
                # Log but don't fail if Kafka publish fails
                import logging
                logging.getLogger(__name__).warning(f"Failed to publish to Kafka: {kafka_error}")

            # Return structured response
            return {
                "success": True,
                "message": "Recurring task created successfully",
                "data": {
                    "id": recurring_task.id,
                    "title": recurring_task.title,
                    "description": recurring_task.description,
                    "frequency": recurring_task.frequency,
                    "start_date": recurring_task.start_date.isoformat(),
                    "end_date": recurring_task.end_date.isoformat() if recurring_task.end_date else None,
                    "next_occurrence": recurring_task.next_occurrence.isoformat(),
                    "user_id": recurring_task.user_id,
                }
            }

    except Exception as e:
        # Return error response
        return {
            "success": False,
            "message": str(e),
            "data": None
        }
