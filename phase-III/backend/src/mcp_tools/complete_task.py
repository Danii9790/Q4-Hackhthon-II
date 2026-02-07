"""
MCP Tool: Complete Task

Marks a task as completed for the authenticated user.
"""
from sqlalchemy.orm import Session

from src.db.session import get_session
from src.services.task import complete_task


async def complete_task(
    user_id: str,
    task_id: int
) -> dict:
    """
    Mark a task as completed via MCP tool.

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
                "updated_at": "2026-02-06T15:30:00"
            }
        }
    """
    try:
        # Get database session
        for session in get_session():
            # Call task service to complete task
            task = complete_task(
                task_id=task_id,
                user_id=user_id,
                session=session
            )

            # Return structured response
            return {
                "success": True,
                "message": f"Task '{task.title}' marked as completed",
                "data": {
                    "id": task.id,
                    "title": task.title,
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
