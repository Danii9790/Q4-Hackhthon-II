"""
MCP Tool: List Tasks

Lists tasks for the authenticated user with advanced filtering.
Phase V: Supports filtering by priority, tags, due date, search, and sorting.
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from src.db.session import get_session
from src.services.task import list_tasks_advanced


async def list_tasks(
    user_id: str,
    status: str = "all",
    priority: Optional[str] = None,
    tags: Optional[List[str]] = None,
    due_before: Optional[str] = None,
    due_after: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    offset: int = 0,
    limit: int = 50
) -> dict:
    """
    T029: List tasks via MCP tool with advanced filtering and sorting.

    Phase V: Supports filtering by priority, tags, due date range, full-text search,
    and sorting by various fields.

    Args:
        user_id: User UUID from JWT token
        status: Filter by completion status ("all", "pending", "completed")
        priority: Optional priority filter (LOW, MEDIUM, HIGH)
        tags: Optional list of tags to filter by (task must have ALL tags)
        due_before: Optional due date upper bound (ISO 8601 string)
        due_after: Optional due date lower bound (ISO 8601 string)
        search: Optional search query for title/description (case-insensitive)
        sort_by: Field to sort by (created_at, updated_at, due_date, priority, completed_at)
        sort_order: Sort direction ("asc" or "desc", default "desc")
        offset: Pagination offset (default 0)
        limit: Max results to return (default 50, max 100)

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
                        "due_date": "2026-02-15T10:00:00Z",
                        "priority": "HIGH",
                        "tags": ["work", "urgent"],
                        "created_at": "2026-02-06T12:00:00"
                    }
                ],
                "count": 3,
                "total": 3,
                "offset": 0,
                "limit": 50
            }
        }
    """
    try:
        # Get database session
        for session in get_session():
            # Parse date filters if provided
            due_before_dt = None
            due_after_dt = None

            if due_before:
                try:
                    due_before_dt = datetime.fromisoformat(due_before.replace('Z', '+00:00'))
                except ValueError:
                    return {
                        "success": False,
                        "message": "Invalid due_before date format. Use ISO 8601 format.",
                        "data": {"tasks": [], "count": 0, "total": 0, "offset": offset, "limit": limit}
                    }

            if due_after:
                try:
                    due_after_dt = datetime.fromisoformat(due_after.replace('Z', '+00:00'))
                except ValueError:
                    return {
                        "success": False,
                        "message": "Invalid due_after date format. Use ISO 8601 format.",
                        "data": {"tasks": [], "count": 0, "total": 0, "offset": offset, "limit": limit}
                    }

            # Call advanced list service
            tasks, total = list_tasks_advanced(
                user_id=user_id,
                session=session,
                offset=offset,
                limit=limit,
                priority=priority,
                tags=tags,
                due_before=due_before_dt,
                due_after=due_after_dt,
                search=search,
                sort_by=sort_by,
                sort_order=sort_order
            )

            # Apply status filter if needed
            if status == "pending":
                tasks = [t for t in tasks if not t.completed]
                total = len(tasks)
            elif status == "completed":
                tasks = [t for t in tasks if t.completed]
                total = len(tasks)

            # Format tasks for response with all Phase V fields
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
                "message": f"Found {total} task{'s' if total != 1 else ''}",
                "data": {
                    "tasks": formatted_tasks,
                    "count": len(formatted_tasks),
                    "total": total,
                    "offset": offset,
                    "limit": limit
                }
            }

    except Exception as e:
        # Return error response
        return {
            "success": False,
            "message": str(e),
            "data": {
                "tasks": [],
                "count": 0,
                "total": 0,
                "offset": offset,
                "limit": limit
            }
        }
