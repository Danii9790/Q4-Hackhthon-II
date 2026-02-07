"""
MCP Tool: Delete Task

Deletes a task for the authenticated user.
"""
from sqlalchemy.orm import Session

from src.db.session import get_session
from src.services.task import delete_task


async def delete_task(
    user_id: str,
    task_id: int
) -> dict:
    """
    Delete a task via MCP tool.

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
            # Call task service to delete task
            # First get the task to return its info
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

            task_title = task.title
            task_completed = task.completed

            # Delete the task
            delete_task(
                task_id=task_id,
                user_id=user_id,
                session=session
            )

            # Return structured response
            return {
                "success": True,
                "message": f"Task '{task_title}' deleted successfully",
                "data": {
                    "id": task_id,
                    "title": task_title,
                    "completed": task_completed
                }
            }

    except Exception as e:
        # Return error response
        return {
            "success": False,
            "message": str(e),
            "data": None
        }
