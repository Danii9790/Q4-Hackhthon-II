"""
MCP Tool: List Reminders

Lists upcoming reminders for the authenticated user.
"""
from typing import Optional
from sqlalchemy.orm import Session

from src.db.session import get_session
from src.services.reminder_service import list_reminders


async def list_reminders_tool(
    user_id: str,
    include_sent: bool = False
) -> dict:
    """
    T084: List upcoming reminders via MCP tool.

    Returns all reminders for the user's tasks that haven't been sent yet.

    Args:
        user_id: User UUID from JWT token
        include_sent: Include sent reminders (default False)

    Returns:
        Dict with success status and reminders list:
        {
            "success": True,
            "message": "Found 2 reminders",
            "data": {
                "count": 2,
                "reminders": [
                    {
                        "id": "uuid",
                        "task_id": 1,
                        "task_title": "Complete project proposal",
                        "remind_at": "2026-02-10T16:00:00Z",
                        "sent": false,
                        "sent_at": null
                    }
                ]
            }
        }
    """
    try:
        # Get database session
        for session in get_session():
            # Call reminder service to list reminders
            reminders = list_reminders(
                user_id=user_id,
                session=session,
                include_sent=include_sent
            )

            # Format reminders for response
            from src.models.task import Task

            formatted_reminders = []
            for reminder in reminders:
                # Get task details
                task = session.query(Task).filter(
                    Task.id == reminder.task_id
                ).first()

                formatted_reminders.append({
                    "id": reminder.id,
                    "task_id": reminder.task_id,
                    "task_title": task.title if task else "Unknown task",
                    "remind_at": reminder.remind_at.isoformat(),
                    "sent": reminder.sent,
                    "sent_at": reminder.sent_at.isoformat() if reminder.sent_at else None
                })

            # Return structured response
            return {
                "success": True,
                "message": f"Found {len(formatted_reminders)} reminder{'s' if len(formatted_reminders) != 1 else ''}",
                "data": {
                    "count": len(formatted_reminders),
                    "reminders": formatted_reminders
                }
            }

    except Exception as e:
        # Return error response
        return {
            "success": False,
            "message": str(e),
            "data": {
                "count": 0,
                "reminders": []
            }
        }
