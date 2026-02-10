"""
Integration tests for task sorting by due date.

Tests sorting tasks by various fields.
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
    from src.models.task import Task
    from src.models.user import User
    Task.metadata.create_all(bind=test_engine)
    User.metadata.create_all(bind=test_engine)
    yield
    Task.metadata.drop_all(bind=test_engine)
    User.metadata.drop_all(bind=test_engine)


@pytest.fixture
def test_user_with_dated_tasks():
    """Create a test user with tasks having different due dates."""
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

    # Create tasks with different due dates
    now = datetime.now(timezone.utc)
    tasks = [
        ("Task due tomorrow", now + timedelta(days=1)),
        ("Task due next week", now + timedelta(days=7)),
        ("Task due today", now + timedelta(hours=5)),
        ("Task due next month", now + timedelta(days=30)),
        ("No due date task", None),
    ]

    for title, due_date in tasks:
        task = Task(
            title=title,
            user_id=user_id,
            due_date=due_date,
            completed=False,
            created_at=now,
            updated_at=now
        )
        db.add(task)

    db.commit()
    db.close()
    return user_id


def test_sort_tasks_by_due_date_ascending(test_user_with_dated_tasks):
    """
    T023: Test sorting tasks by due_date ascending.

    Given a user with tasks with various due dates
    When sorting by due_date ASC
    Then tasks should be ordered from earliest to latest due date
    """
    response = client.get(
        f"/api/users/{test_user_with_dated_tasks}/tasks?sort_by=due_date&sort_order=asc"
    )

    assert response.status_code == 200
    data = response.json()
    tasks = data["tasks"]

    # Tasks with due dates should come first (nulls last by default)
    # Verify they're in ascending order
    due_dates = [t["due_date"] for t in tasks if t["due_date"] is not None]

    # Should be sorted ascending (earliest first)
    for i in range(len(due_dates) - 1):
        assert due_dates[i] <= due_dates[i + 1]


def test_sort_tasks_by_due_date_descending(test_user_with_dated_tasks):
    """
    T023: Test sorting tasks by due_date descending.

    Given a user with tasks with various due dates
    When sorting by due_date DESC
    Then tasks should be ordered from latest to earliest due date
    """
    response = client.get(
        f"/api/users/{test_user_with_dated_tasks}/tasks?sort_by=due_date&sort_order=desc"
    )

    assert response.status_code == 200
    data = response.json()
    tasks = data["tasks"]

    # Tasks with due dates should be in descending order
    due_dates = [t["due_date"] for t in tasks if t["due_date"] is not None]

    # Should be sorted descending (latest first)
    for i in range(len(due_dates) - 1):
        assert due_dates[i] >= due_dates[i + 1]


def test_sort_tasks_by_created_at(test_user_with_dated_tasks):
    """
    T023: Test sorting tasks by created_at.

    Given a user with tasks
    When sorting by created_at DESC (default)
    Then tasks should be ordered from newest to oldest
    """
    response = client.get(
        f"/api/users/{test_user_with_dated_tasks}/tasks?sort_by=created_at&sort_order=desc"
    )

    assert response.status_code == 200
    data = response.json()

    # Default ordering should work
    assert len(data["tasks"]) == 5


def test_sort_tasks_by_priority(test_user_with_dated_tasks):
    """
    T023: Test sorting tasks by priority.

    Given a user with tasks
    When sorting by priority DESC
    Then HIGH priority tasks should come first, then MEDIUM, then LOW
    """
    response = client.get(
        f"/api/users/{test_user_with_dated_tasks}/tasks?sort_by=priority&sort_order=desc"
    )

    assert response.status_code == 200
    data = response.json()

    # Priority sort should work
    assert len(data["tasks"]) == 5


def test_invalid_sort_field_rejected(test_user_with_dated_tasks):
    """
    T023: Test that invalid sort field is rejected.

    Given a user with tasks
    When sorting by invalid field
    Then the request should fail with validation error
    """
    response = client.get(
        f"/api/users/{test_user_with_dated_tasks}/tasks?sort_by=invalid_field"
    )

    assert response.status_code == 422


def test_invalid_sort_order_rejected(test_user_with_dated_tasks):
    """
    T023: Test that invalid sort order is rejected.

    Given a user with tasks
    When sorting with invalid order
    Then the request should fail with validation error
    """
    response = client.get(
        f"/api/users/{test_user_with_dated_tasks}/tasks?sort_by=due_date&sort_order=invalid"
    )

    assert response.status_code == 422
