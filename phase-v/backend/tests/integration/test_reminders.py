"""
Integration tests for reminders.

Tests for creating, scheduling, and sending task reminders.
"""
import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from src.main import app
from src.db.session import get_session
from src.models.task import Task


# Test database setup
TEST_DATABASE_URL = "sqlite:///./test.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_session():
    """Override database session for testing."""
    try:
        db = TestSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_session] = override_get_session
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Setup test database before each test."""
    from src.models.task import Task, RecurringTask
    from src.models.user import User
    from src.models.reminder import Reminder
    Task.metadata.create_all(bind=test_engine)
    RecurringTask.metadata.create_all(bind=test_engine)
    User.metadata.create_all(bind=test_engine)
    Reminder.metadata.create_all(bind=test_engine)
    yield
    Task.metadata.drop_all(bind=test_engine)
    RecurringTask.metadata.drop_all(bind=test_engine)
    User.metadata.drop_all(bind=test_engine)
    Reminder.metadata.drop_all(bind=test_engine)


@pytest.fixture
def test_user():
    """Create a test user and return user_id."""
    from src.models.user import User
    import uuid

    db = TestSessionLocal()
    user = User(
        id=str(uuid.uuid4()),
        email="test@example.com",
        name="Test User",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    user_id = user.id
    db.close()
    return user_id


@pytest.fixture
def auth_headers(test_user):
    """Get authentication headers for test user."""
    return {"X-User-ID": test_user}


@pytest.fixture
def test_task(test_user):
    """Create a test task with due date and return task_id."""
    from src.models.task import Task

    db = TestSessionLocal()
    task = Task(
        user_id=test_user,
        title="Task with reminder",
        description="This task needs a reminder",
        due_date=datetime.now(timezone.utc) + timedelta(hours=5),
        completed=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    task_id = task.id
    db.close()
    return task_id


def test_create_reminder_for_task(test_task, auth_headers):
    """
    T075: Test creating a reminder for a task.

    Given a valid task with a due date
    When creating a reminder 1 hour before due date
    Then the reminder should be created with correct remind_at time
    """
    from src.services.reminder_service import create_reminder

    db = TestSessionLocal()

    # Calculate reminder time (1 hour before task due date)
    task = db.query(Task).filter(Task.id == test_task).first()
    remind_at = task.due_date - timedelta(hours=1)

    # Create reminder
    reminder = create_reminder(
        task_id=test_task,
        remind_at=remind_at,
        session=db
    )

    assert reminder.id is not None
    assert reminder.task_id == test_task
    assert reminder.remind_at == remind_at
    assert reminder.sent is False
    assert reminder.sent_at is None
    db.close()


def test_schedule_reminders():
    """
    T076: Test scheduling reminders query.

    Given multiple reminders with different remind_at times
    When querying for due reminders (remind_at <= NOW())
    Then only unsent reminders that are due should be returned
    """
    from src.services.reminder_service import create_reminder, get_due_reminders
    from src.models.task import Task
    from src.models.user import User
    import uuid

    db = TestSessionLocal()

    # Create test user and task
    user = User(
        id=str(uuid.uuid4()),
        email="schedule-test@example.com",
        name="Schedule Test User",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(user)
    db.commit()

    task = Task(
        user_id=user.id,
        title="Task with multiple reminders",
        due_date=datetime.now(timezone.utc) + timedelta(hours=5),
        completed=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(task)
    db.commit()

    # Create reminders:
    # 1. Past reminder (should be due)
    reminder1 = create_reminder(
        task_id=task.id,
        remind_at=datetime.now(timezone.utc) - timedelta(minutes=10),
        session=db
    )

    # 2. Current reminder (should be due)
    reminder2 = create_reminder(
        task_id=task.id,
        remind_at=datetime.now(timezone.utc),
        session=db
    )

    # 3. Future reminder (should NOT be due)
    reminder3 = create_reminder(
        task_id=task.id,
        remind_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        session=db
    )

    # Get due reminders
    due_reminders = get_due_reminders(session=db)

    # Should have 2 due reminders (reminder1 and reminder2)
    assert len(due_reminders) >= 2

    # Check that reminder1 and reminder2 are in the list
    due_ids = [r.id for r in due_reminders]
    assert reminder1.id in due_ids
    assert reminder2.id in due_ids

    db.close()


def test_send_reminder():
    """
    T077: Test sending a reminder notification.

    Given a due reminder
    When sending the reminder
    Then reminder should be marked as sent with sent_at timestamp
    """
    from src.services.reminder_service import create_reminder, send_reminder
    from src.models.task import Task
    from src.models.user import User
    import uuid

    db = TestSessionLocal()

    # Create test user and task
    user = User(
        id=str(uuid.uuid4()),
        email="send-test@example.com",
        name="Send Test User",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(user)
    db.commit()

    task = Task(
        user_id=user.id,
        title="Task with sendable reminder",
        description="Don't forget this task!",
        due_date=datetime.now(timezone.utc) + timedelta(hours=1),
        completed=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(task)
    db.commit()

    # Create reminder that's due
    reminder = create_reminder(
        task_id=task.id,
        remind_at=datetime.now(timezone.utc) - timedelta(minutes=5),
        session=db
    )

    # Refresh from database to get latest state
    db.refresh(reminder)

    # Send reminder
    send_reminder(
        reminder_id=reminder.id,
        session=db
    )

    # Refresh to check updated state
    db.refresh(reminder)

    assert reminder.sent is True
    assert reminder.sent_at is not None
    assert reminder.sent_at <= datetime.now(timezone.utc)

    db.close()


def test_list_reminders_for_user(test_user, test_task, auth_headers):
    """
    T084: Test listing reminders for a user.

    Given a user with multiple reminders for different tasks
    When listing all upcoming reminders
    Then all unsent reminders should be returned
    """
    from src.services.reminder_service import create_reminder, list_reminders
    from src.models.task import Task

    db = TestSessionLocal()

    # Create another task
    task2 = Task(
        user_id=test_user,
        title="Another task",
        due_date=datetime.now(timezone.utc) + timedelta(hours=10),
        completed=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(task2)
    db.commit()

    # Create reminders for both tasks
    reminder1 = create_reminder(
        task_id=test_task,
        remind_at=datetime.now(timezone.utc) + timedelta(hours=1),
        session=db
    )

    reminder2 = create_reminder(
        task_id=task2.id,
        remind_at=datetime.now(timezone.utc) + timedelta(hours=2),
        session=db
    )

    # List reminders for user
    reminders = list_reminders(
        user_id=test_user,
        session=db
    )

    # Should have at least 2 reminders
    assert len(reminders) >= 2

    # Check that both reminders are in the list
    reminder_ids = [r.id for r in reminders]
    assert reminder1.id in reminder_ids
    assert reminder2.id in reminder_ids

    db.close()
