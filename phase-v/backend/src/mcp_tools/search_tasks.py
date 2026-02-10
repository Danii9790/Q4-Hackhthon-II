"""
MCP Tool: Search Tasks

Searches tasks by full-text search in title and description.
Phase V: New MCP tool.
"""
from typing import Optional
from sqlalchemy.orm import Session

from src.db.session import get_session
from src.services.task import list_tasks_advanced


async def search_tasks(
    user_id: str,
    query: str,
    offset: int = 0,
    limit: int = 50
) -> dict:
    """
    T033: Search tasks via full-text search in title and description.

    Args:
        user_id: User UUID from JWT token
        query: Search query string (case-insensitive, partial matches)
        offset: Pagination offset (default 0)
        limit: Max results to return (default 50, max 100)

    Returns:
        Dict with success status and matching tasks:
        {
            "success": True,
            "message": "Found 2 tasks matching 'API'",
            "data": {
                "tasks": [
                    {
                        "id": 1,
                        "title": "Complete API implementation",
                        "description": "Build REST API with FastAPI",
                        "completed": False,
                        "created_at": "2026-02-06T12:00:00"
                    }
                ],
                "count": 2,
                "total": 2,
                "query": "API"
            }
        }
    """
    try:
        # Get database session
        for session in get_session():
            # Call advanced list service with search parameter
            tasks, total = list_tasks_advanced(
                user_id=user_id,
                session=session,
                offset=offset,
                limit=limit,
                search=query,
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
                "message": f"Found {total} task{'s' if total != 1 else ''} matching '{query}'",
                "data": {
                    "tasks": formatted_tasks,
                    "count": len(formatted_tasks),
                    "total": total,
                    "query": query,
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
                "total": 0,
                "query": query
            }
        }
