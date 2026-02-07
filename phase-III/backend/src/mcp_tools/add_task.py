"""
MCP Tool: Add Task

Creates a new task for the authenticated user.
"""
from typing import Optional
from sqlalchemy.orm import Session

from src.db.session import get_session
from src.services.task import create_task


async def add_task(
    user_id: str,
    title: str,
    description: Optional[str] = None
) -> dict:
    """
    Create a new task for the user.

    MCP tool for adding tasks to the user's task list.
    Enforces user ownership - tasks can only be created for the authenticated user.

    Args:
        user_id: User UUID (for ownership enforcement)
        title: Task title (required, max 200 characters)
        description: Optional task description (max 1000 characters)

    Returns:
        dict: Response with success status and task data:
        {
            "success": bool,
            "message": str,
            "data": {
                "id": str,
                "title": str,
                "description": str,
                "completed": bool,
                "created_at": str
            } | None
        }

    Example:
        >>> result = await add_task(user_id="abc123", title="Buy groceries")
        >>> print(result["success"])
        True
    """
    """
    Create a new task via MCP tool.

    Args:
        user_id: User UUID from JWT token
        title: Task title (1-200 characters)
        description: Optional task description (max 1000 characters)

    Returns:
        Dict with success status and task data:
        {
            "success": True,
            "message": "Task created successfully",
            "data": {
                "id": 1,
                "title": "Buy groceries",
                "description": "Milk, eggs, bread",
                "completed": False,
                "user_id": "uuid",
                "created_at": "2026-02-06T12:00:00"
            }
        }
    """
    try:
        # Get database session
        for session in get_session():
            # Call task service to create task
            task = create_task(
                title=title,
                description=description,
                user_id=user_id,
                session=session
            )

            # Return structured response
            return {
                "success": True,
                "message": "Task created successfully",
                "data": {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "completed": task.completed,
                    "user_id": task.user_id,
                    "created_at": task.created_at.isoformat()
                }
            }

    except Exception as e:
        # Return error response
        return {
            "success": False,
            "message": str(e),
            "data": None
        }
