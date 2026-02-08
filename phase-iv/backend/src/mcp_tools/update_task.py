"""
MCP Tool: Update Task

Updates a task's title and/or description for the authenticated user.
"""
from typing import Optional
from sqlalchemy.orm import Session

from src.db.session import get_session
from src.services.task import update_task


async def update_task(
    user_id: str,
    task_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None
) -> dict:
    """
    Update a task via MCP tool.

    Args:
        user_id: User UUID from JWT token
        task_id: Task's unique identifier
        title: Optional new title (1-200 characters)
        description: Optional new description (max 1000 characters)

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
                "updated_at": "2026-02-06T16:00:00"
            }
        }
    """
    try:
        # Get database session
        for session in get_session():
            # Call task service to update task
            task = update_task(
                task_id=task_id,
                user_id=user_id,
                title=title,
                description=description,
                session=session
            )

            # Return structured response
            return {
                "success": True,
                "message": "Task updated successfully",
                "data": {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "completed": task.completed,
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
