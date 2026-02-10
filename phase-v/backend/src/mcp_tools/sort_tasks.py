"""
MCP Tool: Sort Tasks

Returns sorted tasks by specified field and order.
Phase V: New MCP tool.
"""
from sqlalchemy.orm import Session

from src.db.session import get_session
from src.services.task import list_tasks_advanced


async def sort_tasks(
    user_id: str,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    offset: int = 0,
    limit: int = 50
) -> dict:
    """
    T035: Sort and return tasks by specified field and order.

    Args:
        user_id: User UUID from JWT token
        sort_by: Field to sort by (created_at, updated_at, due_date, priority, completed_at)
        sort_order: Sort direction ("asc" or "desc", default "desc")
        offset: Pagination offset (default 0)
        limit: Max results to return (default 50, max 100)

    Returns:
        Dict with success status and sorted tasks:
        {
            "success": True,
            "message": "Found 5 tasks sorted by due_date",
            "data": {
                "tasks": [
                    {
                        "id": 1,
                        "title": "Task due soon",
                        "due_date": "2026-02-10T10:00:00Z",
                        "priority": "HIGH",
                        "completed": False
                    }
                ],
                "count": 5,
                "total": 5,
                "sort_by": "due_date",
                "sort_order": "desc"
            }
        }
    """
    try:
        # Get database session
        for session in get_session():
            # Call advanced list service with sorting
            tasks, total = list_tasks_advanced(
                user_id=user_id,
                session=session,
                offset=offset,
                limit=limit,
                sort_by=sort_by,
                sort_order=sort_order
            )

            # Format tasks for response
            formatted_tasks = [
                {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "completed": task.completed,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                    "due_date": task.due_date.isoformat() if task.due_date else None,
                    "priority": task.priority,
                    "tags": task.tags or [],
                    "created_at": task.created_at.isoformat(),
                    "updated_at": task.updated_at.isoformat(),
                }
                for task in tasks
            ]

            # Return structured response
            return {
                "success": True,
                "message": f"Found {total} task{'s' if total != 1 else ''} sorted by {sort_by}",
                "data": {
                    "tasks": formatted_tasks,
                    "count": len(formatted_tasks),
                    "total": total,
                    "sort_by": sort_by,
                    "sort_order": sort_order,
                    "offset": offset,
                    "limit": limit
                }
            }

    except Exception as e:
        return {
            "success": False,
            "message": str(e),
            "data": {
                "tasks": [],
                "count": 0,
                "total": 0
            }
        }
