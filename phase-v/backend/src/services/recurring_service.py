"""
Recurring Task Service

Manages recurring task templates and automatic creation of next occurrences.
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session

from src.models.recurring_task import RecurringTask, Frequency
from src.models.task import Task


logger = logging.getLogger(__name__)


def calculate_next_occurrence(
    current_date: datetime,
    frequency: str
) -> datetime:
    """
    T057-T059: Calculate next occurrence date based on frequency.

    Args:
        current_date: Current occurrence date
        frequency: Frequency type (DAILY, WEEKLY, MONTHLY)

    Returns:
        Next occurrence datetime in UTC

    Raises:
        ValueError: If frequency is invalid
    """
    if frequency == Frequency.DAILY:
        # T058: Add 1 day
        return current_date + timedelta(days=1)
    elif frequency == Frequency.WEEKLY:
        # T059: Add 7 days
        return current_date + timedelta(weeks=1)
    elif frequency == Frequency.MONTHLY:
        # T060: Add 1 month (handle month edge cases)
        # Simple approach: add ~30 days and adjust to same day number
        year = current_date.year
        month = current_date.month + 1

        # Handle year rollover
        if month > 12:
            month = 1
            year += 1

        # Handle months with fewer days (e.g., Feb 31 -> Feb 28/29)
        day = min(current_date.day, [31, 28 if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0) else 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])

        return current_date.replace(year=year, month=month, day=day)
    else:
        raise ValueError(f"Invalid frequency: {frequency}")


def should_create_next_occurrence(end_date: Optional[datetime]) -> bool:
    """
    T061: Check if next occurrence should be created based on end_date.

    Args:
        end_date: Task template end date (None means infinite)

    Returns:
        True if next occurrence should be created, False otherwise
    """
    if end_date is None:
        return True

    now = datetime.now(timezone.utc)
    return end_date > now


def create_recurring_task(
    user_id: str,
    title: str,
    description: Optional[str],
    frequency: str,
    start_date: datetime,
    end_date: Optional[datetime],
    session: Session
) -> RecurringTask:
    """
    Create a recurring task template with first occurrence.

    Args:
        user_id: User ID
        title: Task title
        description: Task description
        frequency: Recurrence frequency (DAILY, WEEKLY, MONTHLY)
        start_date: First occurrence date
        end_date: Optional end date (None for infinite)
        session: Database session

    Returns:
        Created RecurringTask template

    Raises:
        ValueError: If parameters are invalid
    """
    # Validate frequency
    valid_frequencies = [f.value for f in Frequency]
    if frequency not in valid_frequencies:
        raise ValueError(f"Invalid frequency: {frequency}. Must be one of {valid_frequencies}")

    # Ensure dates are timezone-aware
    if start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=timezone.utc)
    else:
        start_date = start_date.astimezone(timezone.utc)

    if end_date and end_date.tzinfo is None:
        end_date = end_date.replace(tzinfo=timezone.utc)
    elif end_date:
        end_date = end_date.astimezone(timezone.utc)

    # Validate end_date is after start_date
    if end_date and end_date <= start_date:
        raise ValueError("end_date must be after start_date")

    # Create recurring task template
    recurring_task = RecurringTask(
        user_id=user_id,
        title=title,
        description=description,
        frequency=frequency,
        start_date=start_date,
        end_date=end_date,
        next_occurrence=start_date,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    session.add(recurring_task)
    session.commit()
    session.refresh(recurring_task)

    # Create first task occurrence
    first_task = Task(
        user_id=user_id,
        title=title,
        description=description,
        recurring_task_id=recurring_task.id,
        completed=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    session.add(first_task)
    session.commit()

    logger.info(f"Created recurring task '{title}' ({frequency}) for user {user_id}")

    return recurring_task


def create_next_occurrence(
    recurring_task_id: str,
    session: Session
) -> Optional[Task]:
    """
    Create next task occurrence for a recurring task.

    Called when a task occurrence is completed.

    Args:
        recurring_task_id: Recurring task template ID
        session: Database session

    Returns:
        Created Task occurrence or None if end_date reached

    Raises:
        ValueError: If recurring task not found
    """
    # Get recurring task template
    recurring_task = session.query(RecurringTask).filter(
        RecurringTask.id == recurring_task_id
    ).first()

    if not recurring_task:
        raise ValueError(f"Recurring task {recurring_task_id} not found")

    # Check if we should create next occurrence
    if not should_create_next_occurrence(recurring_task.end_date):
        logger.info(f"Recurring task {recurring_task_id} reached end_date, stopping")
        return None

    # Calculate next occurrence date
    next_date = calculate_next_occurrence(
        recurring_task.next_occurrence,
        recurring_task.frequency
    )

    # Create new task occurrence
    new_task = Task(
        user_id=recurring_task.user_id,
        title=recurring_task.title,
        description=recurring_task.description,
        recurring_task_id=recurring_task.id,
        due_date=next_date,
        completed=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    session.add(new_task)

    # Update recurring task template
    recurring_task.next_occurrence = next_date
    recurring_task.updated_at = datetime.now(timezone.utc)

    session.commit()
    session.refresh(new_task)

    logger.info(f"Created next occurrence for recurring task {recurring_task_id}: {next_date}")

    return new_task


def get_recurring_tasks(
    user_id: str,
    session: Session,
    include_completed: bool = False
) -> List[RecurringTask]:
    """
    Get all recurring task templates for a user.

    Args:
        user_id: User ID
        session: Database session
        include_completed: Include templates that have reached end_date

    Returns:
        List of RecurringTask templates
    """
    query = session.query(RecurringTask).filter(
        RecurringTask.user_id == user_id
    )

    if not include_completed:
        # Only show active templates (not reached end_date)
        now = datetime.now(timezone.utc)
        query = query.filter(
            (RecurringTask.end_date == None) |
            (RecurringTask.end_date > now)
        )

    return query.order_by(RecurringTask.created_at.desc()).all()


def delete_recurring_task(
    recurring_task_id: str,
    user_id: str,
    session: Session
) -> None:
    """
    Delete a recurring task template.

    This stops future occurrences but does not delete existing tasks.

    Args:
        recurring_task_id: Recurring task template ID
        user_id: User ID (for ownership verification)
        session: Database session

    Raises:
        ValueError: If recurring task not found or doesn't belong to user
    """
    recurring_task = session.query(RecurringTask).filter(
        RecurringTask.id == recurring_task_id,
        RecurringTask.user_id == user_id
    ).first()

    if not recurring_task:
        raise ValueError(f"Recurring task {recurring_task_id} not found")

    session.delete(recurring_task)
    session.commit()

    logger.info(f"Deleted recurring task {recurring_task_id}")
