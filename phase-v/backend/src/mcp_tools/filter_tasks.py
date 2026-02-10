"""
MCP Tool: Filter Tasks

Filters tasks by various criteria.
Phase V: New MCP tool.
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from src.db.session import get_session
from src.services.task import list_tasks_advanced


async def filter_tasks(
    user_id: str,
    priority: Optional[str] = None,
    tags: Optional[List[str]] = None,
    due_before: Optional[str] = None,
    due_after: Optional[str] = None,
    offset: int = 0,
    limit: int = 50
) -> dict:
    """
    T034: Filter tasks by various criteria.

    Args:
        user_id: User UUID from JWT token
        priority: Optional priority filter (LOW, MEDIUM, HIGH)
        tags: Optional list of tags to filter by (task must have ALL tags)
        due_before: Optional due date upper bound (ISO 8601 string)
        due_after: Optional due date lower bound (ISO 8601 string)
        offset: Pagination offset (default 0)
        limit: Max results to return (default 50, max 100)

    Returns:
        Dict with success status and filtered tasks:
        {
            "success": True,
            "message": "Found 3 tasks matching filters",
            "data": {
                "tasks": [
                    {
                        "id": 1,
                        "title": "High priority task",
                        "priority": "HIGH",
                        "tags": ["work"],
                        "due_date": "2026-02-15T10:00:00Z",
                        "completed": False
                    }
                ],
                "count": 3,
                "total": 3
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
                due_before_dt = datetime.fromisoformat(due_before.replace('Z', '+00:00'))

            if due_after:
                due_after_dt = datetime.fromisoformat(due_after.replace('Z', '+00:00'))

            # Call advanced list service with filters
            tasks, total = list_tasks_advanced(
                user_id=user_id,
                session=session,
                offset=offset,
                limit=limit,
                priority=priority,
                tags=tags,
                due_before=due_before_dt,
                due_after=due_after_dt,
                sort_by="created_at",
                sort_order="desc"
            )

            # Format tasks for response
            formatted_tasks = [
                {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "completed": task.completed,
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
                "message": f"Found {total} task{'s' if total != 1 else ''} matching filters",
                "data": {
                    "tasks": formatted_tasks,
                    "count": len(formatted_tasks),
                    "total": total,
                    "filters": {
                        "priority": priority,
                        "tags": tags,
                        "due_before": due_before,
                        "due_after": due_after
                    },
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
