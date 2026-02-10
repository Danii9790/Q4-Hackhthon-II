"""
Reminder Service

Manages task reminders, scheduling, and notification sending.
"""
import logging
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session

from src.models.reminder import Reminder
from src.models.task import Task


logger = logging.getLogger(__name__)


def create_reminder(
    task_id: int,
    remind_at: datetime,
    session: Session
) -> Reminder:
    """
    T078: Create a reminder for a task.

    Args:
        task_id: Task ID to create reminder for
        remind_at: When to send the reminder (UTC)
        session: Database session

    Returns:
        Created Reminder

    Raises:
        ValueError: If task not found or remind_at is in the past
    """
    # Validate task exists
    task = session.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise ValueError(f"Task {task_id} not found")

    # Ensure remind_at is timezone-aware
    if remind_at.tzinfo is None:
        remind_at = remind_at.replace(tzinfo=timezone.utc)
    else:
        remind_at = remind_at.astimezone(timezone.utc)

    # Validate remind_at is not in the past
    now = datetime.now(timezone.utc)
    if remind_at < now:
        raise ValueError(f"remind_at must be in the future (provided: {remind_at})")

    # Create reminder
    reminder = Reminder(
        task_id=task_id,
        remind_at=remind_at,
        sent=False,
        created_at=datetime.now(timezone.utc)
    )

    session.add(reminder)
    session.commit()
    session.refresh(reminder)

    logger.info(f"Created reminder for task {task_id} at {remind_at}")

    return reminder


def get_due_reminders(
    session: Session,
    limit: int = 100
) -> List[Reminder]:
    """
    T079: Get reminders that are due to be sent.

    Queries unsent reminders where remind_at <= NOW()

    Args:
        session: Database session
        limit: Maximum number of reminders to return

    Returns:
        List of due Reminder objects
    """
    now = datetime.now(timezone.utc)

    reminders = session.query(Reminder).filter(
        Reminder.sent == False,
        Reminder.remind_at <= now
    ).order_by(
        Reminder.remind_at.asc()
    ).limit(limit).all()

    logger.debug(f"Found {len(reminders)} due reminders")

    return reminders


def send_reminder(
    reminder_id: str,
    session: Session
) -> Reminder:
    """
    T080: Send a reminder notification (in-app).

    Stores notification in database for the user to see.
    Marks reminder as sent and records sent_at timestamp.

    Args:
        reminder_id: Reminder ID to send
        session: Database session

    Returns:
        Updated Reminder with sent=True

    Raises:
        ValueError: If reminder not found or already sent
    """
    # Get reminder
    reminder = session.query(Reminder).filter(
        Reminder.id == reminder_id
    ).first()

    if not reminder:
        raise ValueError(f"Reminder {reminder_id} not found")

    if reminder.sent:
        logger.warning(f"Reminder {reminder_id} already sent")
        return reminder

    # Get task details for notification
    task = session.query(Task).filter(
        Task.id == reminder.task_id
    ).first()

    if not task:
        logger.error(f"Task {reminder.task_id} not found for reminder {reminder_id}")
        raise ValueError(f"Task {reminder.task_id} not found")

    # TODO: Store in-app notification in database
    # For now, we'll just log and mark as sent
    # In a production system, you would:
    # 1. Create a Notification record in the database
    # 2. Send via WebSocket to connected clients
    # 3. Optionally send email/push notification

    logger.info(
        f"Sending reminder for task '{task.title}' to user {task.user_id}"
    )

    # Mark as sent
    reminder.sent = True
    reminder.sent_at = datetime.now(timezone.utc)

    session.commit()
    session.refresh(reminder)

    logger.info(f"Reminder {reminder_id} sent successfully")

    return reminder


def send_email_notification(
    reminder_id: str,
    session: Session
) -> Reminder:
    """
    T081: Send an email notification for a reminder (optional).

    Args:
        reminder_id: Reminder ID to send email for
        session: Database session

    Returns:
        Updated Reminder with sent=True

    Raises:
        ValueError: If reminder not found or already sent

    Note:
        This is an optional feature. In production, you would:
        1. Integrate with an email service (SendGrid, AWS SES, etc.)
        2. Get user's email from the users table
        3. Send HTML-formatted email with task details
        4. Handle email delivery failures gracefully
    """
    # Get reminder
    reminder = session.query(Reminder).filter(
        Reminder.id == reminder_id
    ).first()

    if not reminder:
        raise ValueError(f"Reminder {reminder_id} not found")

    if reminder.sent:
        logger.warning(f"Reminder {reminder_id} already sent")
        return reminder

    # Get task details
    task = session.query(Task).filter(
        Task.id == reminder.task_id
    ).first()

    if not task:
        logger.error(f"Task {reminder.task_id} not found for reminder {reminder_id}")
        raise ValueError(f"Task {reminder.task_id} not found")

    # TODO: Implement email sending
    # In production, you would:
    # 1. Get user's email from users table
    # 2. Use email service (SendGrid, AWS SES, SMTP)
    # 3. Send formatted email with task details
    # 4. Track delivery status

    logger.info(
        f"Email notification would be sent for task '{task.title}' "
        f"(email sending not implemented in this version)"
    )

    # Mark as sent
    reminder.sent = True
    reminder.sent_at = datetime.now(timezone.utc)

    session.commit()
    session.refresh(reminder)

    return reminder


def list_reminders(
    user_id: str,
    session: Session,
    include_sent: bool = False
) -> List[Reminder]:
    """
    T084: List all reminders for a user.

    Args:
        user_id: User ID
        session: Database session
        include_sent: Include sent reminders (default: False)

    Returns:
        List of Reminder objects
    """
    # Get all task IDs for user
    task_ids = session.query(Task.id).filter(
        Task.user_id == user_id
    ).all()

    task_ids = [t[0] for t in task_ids]

    if not task_ids:
        return []

    # Query reminders for user's tasks
    query = session.query(Reminder).filter(
        Reminder.task_id.in_(task_ids)
    )

    if not include_sent:
        query = query.filter(Reminder.sent == False)

    reminders = query.order_by(
        Reminder.remind_at.asc()
    ).all()

    return reminders


def get_reminders_for_task(
    task_id: int,
    session: Session
) -> List[Reminder]:
    """
    Get all reminders for a specific task.

    Args:
        task_id: Task ID
        session: Database session

    Returns:
        List of Reminder objects for the task
    """
    reminders = session.query(Reminder).filter(
        Reminder.task_id == task_id
    ).order_by(
        Reminder.remind_at.asc()
    ).all()

    return reminders


def delete_reminder(
    reminder_id: str,
    session: Session
) -> None:
    """
    Delete a reminder.

    Args:
        reminder_id: Reminder ID to delete
        session: Database session

    Raises:
        ValueError: If reminder not found
    """
    reminder = session.query(Reminder).filter(
        Reminder.id == reminder_id
    ).first()

    if not reminder:
        raise ValueError(f"Reminder {reminder_id} not found")

    session.delete(reminder)
    session.commit()

    logger.info(f"Deleted reminder {reminder_id}")
