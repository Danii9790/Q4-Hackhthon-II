"""
MCP Tool: List Tasks

Lists tasks for the authenticated user with optional status filtering.
"""
from sqlalchemy.orm import Session

from src.db.session import get_session
from src.services.task import list_tasks


async def list_tasks(
    user_id: str,
    status: str = "all"
) -> dict:
    """
    List tasks via MCP tool with optional status filtering.

    Args:
        user_id: User UUID from JWT token
        status: Filter by status ("all", "pending", "completed")

    Returns:
        Dict with success status and task list:
        {
            "success": True,
            "message": "Found 3 tasks",
            "data": {
                "tasks": [
                    {
                        "id": 1,
                        "title": "Buy groceries",
                        "description": "Milk, eggs, bread",
                        "completed": False,
                        "created_at": "2026-02-06T12:00:00"
                    }
                ],
                "count": 3
            }
        }
    """
    try:
        # Get database session
        for session in get_session():
            # Determine filter based on status
            if status == "pending":
                # We need to filter by completed=False
                tasks, total = list_tasks(user_id=user_id, session=session)
                tasks = [t for t in tasks if not t.completed]
                total = len(tasks)
            elif status == "completed":
                # We need to filter by completed=True
                tasks, total = list_tasks(user_id=user_id, session=session)
                tasks = [t for t in tasks if t.completed]
                total = len(tasks)
            else:  # "all"
                # Get all tasks
                tasks, total = list_tasks(user_id=user_id, session=session)

            # Format tasks for response
            formatted_tasks = [
                {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "completed": task.completed,
                    "created_at": task.created_at.isoformat()
                }
                for task in tasks
            ]

            # Return structured response
            return {
                "success": True,
                "message": f"Found {total} task{'s' if total != 1 else ''}",
                "data": {
                    "tasks": formatted_tasks,
                    "count": total
                }
            }

    except Exception as e:
        # Return error response
        return {
            "success": False,
            "message": str(e),
            "data": {
                "tasks": [],
                "count": 0
            }
        }
