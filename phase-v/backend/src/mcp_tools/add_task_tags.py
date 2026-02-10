"""
MCP Tool: Add Task Tags

Adds tags to a task for the authenticated user.
Phase V: New MCP tool.
"""
from typing import List
from sqlalchemy.orm import Session

from src.db.session import get_session
from src.services.task import add_task_tags as service_add_task_tags, get_task


async def add_task_tags(
    user_id: str,
    task_id: int,
    tags: List[str]
) -> dict:
    """
    T032: Add tags to a task via MCP tool.

    Appends new tags to existing tags (no duplicates).

    Args:
        user_id: User UUID from JWT token
        task_id: Task's unique identifier
        tags: List of tags to add (max 10 total after adding, max 50 chars each)

    Returns:
        Dict with success status and updated task:
        {
            "success": True,
            "message": "Tags ['work', 'urgent'] added to task",
            "data": {
                "id": 1,
                "title": "Buy groceries",
                "tags": ["personal", "work", "urgent"],
                "updated_at": "2026-02-06T16:00:00"
            }
        }
    """
    try:
        # Get database session
        for session in get_session():
            # Get old task data for audit trail
            old_task = get_task(task_id=task_id, user_id=user_id, session=session)
            old_tags = old_task.tags or []

            # Call service to add tags
            task = service_add_task_tags(
                task_id=task_id,
                user_id=user_id,
                tags=tags,
                session=session
            )

            # Publish task-updated event to Kafka
            try:
                from src.services.event_publisher import EventPublisher
                old_data = {
                    "title": old_task.title,
                    "tags": old_tags,
                }
                new_data = {
                    "title": task.title,
                    "tags": task.tags,
                }
                EventPublisher.publish_task_updated(
                    task_id=task.id,
                    user_id=user_id,
                    old_data=old_data,
                    new_data=new_data,
                    changes=["tags"]
                )
            except Exception as kafka_error:
                import logging
                logging.getLogger(__name__).warning(f"Failed to publish to Kafka: {kafka_error}")

            # Return structured response
            return {
                "success": True,
                "message": f"Tags {tags} added to task",
                "data": {
                    "id": task.id,
                    "title": task.title,
                    "tags": task.tags,
                    "updated_at": task.updated_at.isoformat()
                }
            }

    except Exception as e:
        return {
            "success": False,
            "message": str(e),
            "data": None
        }
