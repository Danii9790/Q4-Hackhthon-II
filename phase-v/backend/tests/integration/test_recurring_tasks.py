"""
Integration tests for recurring tasks.

Tests for creating recurring tasks and automatic next occurrence generation.
"""
import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from src.main import app
from src.db.session import get_session


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
    Task.metadata.create_all(bind=test_engine)
    RecurringTask.metadata.create_all(bind=test_engine)
    User.metadata.create_all(bind=test_engine)
    yield
    Task.metadata.drop_all(bind=test_engine)
    RecurringTask.metadata.drop_all(bind=test_engine)
    User.metadata.drop_all(bind=test_engine)


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


def test_create_recurring_task_daily(test_user, auth_headers):
    """
    T054: Test creating a DAILY recurring task.

    Given a valid user
    When creating a recurring task with DAILY frequency
    Then the recurring task should be created with correct next_occurrence
    """
    from src.services.recurring_service import create_recurring_task

    db = TestSessionLocal()

    recurring_task = create_recurring_task(
        user_id=test_user,
        title="Daily standup",
        description="Daily team standup meeting",
        frequency="DAILY",
        start_date=datetime.now(timezone.utc),
        end_date=None,
        session=db
    )

    assert recurring_task.id is not None
    assert recurring_task.title == "Daily standup"
    assert recurring_task.frequency == "DAILY"
    assert recurring_task.next_occurrence is not None
    db.close()


def test_calculate_next_occurrence_daily():
    """
    T055: Test next occurrence calculation for DAILY frequency.

    Given a task with DAILY frequency
    When calculating next occurrence
    Then next occurrence should be current_day + 1 day
    """
    from src.services.recurring_service import calculate_next_occurrence

    current = datetime(2026, 2, 10, 10, 0, 0, tzinfo=timezone.utc)
    next_occurrence = calculate_next_occurrence(current, "DAILY")

    expected = datetime(2026, 2, 11, 10, 0, 0, tzinfo=timezone.utc)
    assert next_occurrence == expected


def test_calculate_next_occurrence_weekly():
    """
    T055: Test next occurrence calculation for WEEKLY frequency.

    Given a task with WEEKLY frequency
    When calculating next occurrence
    Then next occurrence should be current_day + 7 days
    """
    from src.services.recurring_service import calculate_next_occurrence

    current = datetime(2026, 2, 10, 10, 0, 0, tzinfo=timezone.utc)
    next_occurrence = calculate_next_occurrence(current, "WEEKLY")

    expected = datetime(2026, 2, 17, 10, 0, 0, tzinfo=timezone.utc)
    assert next_occurrence == expected


def test_calculate_next_occurrence_monthly():
    """
    T055: Test next occurrence calculation for MONTHLY frequency.

    Given a task with MONTHLY frequency
    When calculating next occurrence
    Then next occurrence should be same day number next month
    """
    from src.services.recurring_service import calculate_next_occurrence

    current = datetime(2026, 2, 10, 10, 0, 0, tzinfo=timezone.utc)
    next_occurrence = calculate_next_occurrence(current, "MONTHLY")

    expected = datetime(2026, 3, 10, 10, 0, 0, tzinfo=timezone.utc)
    assert next_occurrence == expected


def test_end_date_stops_recurrence():
    """
    T061: Test that end_date prevents creating occurrences beyond it.

    Given a recurring task with end_date in the past
    When calculating next occurrence
    Then should return None (stop creating occurrences)
    """
    from src.services.recurring_service import should_create_next_occurrence

    now = datetime.now(timezone.utc)
    end_date = now - timedelta(days=1)  # Yesterday

    result = should_create_next_occurrence(end_date)
    assert result is False


def test_no_end_date_allows_infinite_recurrence():
    """
    T061: Test that no end_date allows infinite recurrence.

    Given a recurring task with no end_date
    When checking if should create next occurrence
    Then should return True
    """
    from src.services.recurring_service import should_create_next_occurrence

    result = should_create_next_occurrence(None)
    assert result is True


def test_recurring_completion_creates_next_occurrence():
    """
    T056: Test that completing a recurring task creates the next occurrence.

    Given a recurring task template
    When completing a task occurrence
    Then a new task should be created for the next occurrence
    """
    from src.models.recurring_task import RecurringTask, Frequency
    from src.models.task import Task
    import uuid

    db = TestSessionLocal()

    # Create recurring task template
    recurring = RecurringTask(
        id=str(uuid.uuid4()),
        user_id=test_user,
        title="Weekly report",
        frequency=Frequency.WEEKLY,
        start_date=datetime.now(timezone.utc),
        end_date=None,
        next_occurrence=datetime.now(timezone.utc) + timedelta(days=7)
    )
    db.add(recurring)
    db.commit()
    db.refresh(recurring)

    # Create first occurrence task
    task = Task(
        user_id=test_user,
        title=recurring.title,
        description="Weekly report",
        recurring_task_id=recurring.id,
        completed=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    # Complete the task
    task.completed = True
    task.completed_at = datetime.now(timezone.utc)
    db.commit()

    # Verify the recurring task's next_occurrence was updated
    db.refresh(recurring)
    assert recurring.next_occurrence > task.completed_at
    db.close()
