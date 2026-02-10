# Audit Service
# Logs all task operations to TaskEvent table for complete audit trail

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from sqlmodel import Session
from src.models.task_event import TaskEvent

logger = logging.getLogger(__name__)


class AuditService:
    """Service for managing audit trail of task operations"""

    @staticmethod
    def log_task_created(
        session: Session,
        task_id: int,
        user_id: str,
        task_data: Dict[str, Any],
    ):
        """Log task creation to audit trail"""
        event = TaskEvent(
            event_type="created",
            task_id=task_id,
            user_id=user_id,
            event_data={
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "before": None,
                "after": task_data,
                "changes": ["created"],
            },
        )
        session.add(event)
        session.commit()
        logger.info(f"Audit: Task {task_id} created by user {user_id}")

    @staticmethod
    def log_task_updated(
        session: Session,
        task_id: int,
        user_id: str,
        old_data: Dict[str, Any],
        new_data: Dict[str, Any],
        changes: list,
    ):
        """Log task update to audit trail"""
        event = TaskEvent(
            event_type="updated",
            task_id=task_id,
            user_id=user_id,
            event_data={
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "before": old_data,
                "after": new_data,
                "changes": changes,
            },
        )
        session.add(event)
        session.commit()
        logger.info(f"Audit: Task {task_id} updated by user {user_id}, changes: {changes}")

    @staticmethod
    def log_task_completed(
        session: Session,
        task_id: int,
        user_id: str,
        task_data: Dict[str, Any],
    ):
        """Log task completion to audit trail"""
        event = TaskEvent(
            event_type="completed",
            task_id=task_id,
            user_id=user_id,
            event_data={
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "before": {"completed": False},
                "after": {"completed": True, "completed_at": task_data.get("completed_at")},
                "changes": ["completed", "completed_at"],
            },
        )
        session.add(event)
        session.commit()
        logger.info(f"Audit: Task {task_id} completed by user {user_id}")

    @staticmethod
    def log_task_deleted(
        session: Session,
        task_id: int,
        user_id: str,
        deleted_data: Dict[str, Any],
    ):
        """Log task deletion to audit trail"""
        event = TaskEvent(
            event_type="deleted",
            task_id=task_id,
            user_id=user_id,
            event_data={
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "before": deleted_data,
                "after": None,
                "changes": ["deleted"],
            },
        )
        session.add(event)
        session.commit()
        logger.info(f"Audit: Task {task_id} deleted by user {user_id}")

    @staticmethod
    def get_task_history(
        session: Session,
        task_id: int,
        limit: int = 100,
    ) -> List[TaskEvent]:
        """Get audit trail for a specific task"""
        events = session.query(TaskEvent)\
            .filter(TaskEvent.task_id == task_id)\
            .order_by(TaskEvent.timestamp.desc())\
            .limit(limit)\
            .all()
        return events

    @staticmethod
    def get_user_activity(
        session: Session,
        user_id: str,
        limit: int = 100,
    ) -> List[TaskEvent]:
        """Get all events performed by a specific user"""
        events = session.query(TaskEvent)\
            .filter(TaskEvent.user_id == user_id)\
            .order_by(TaskEvent.timestamp.desc())\
            .limit(limit)\
            .all()
        return events
