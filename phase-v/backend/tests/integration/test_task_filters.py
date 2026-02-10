"""
Integration tests for task filtering by priority.

Tests filtering tasks by priority level.
"""
import pytest
from datetime import datetime, timezone
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
def test_user_with_tasks():
    """Create a test user with multiple tasks of different priorities."""
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

    # Create tasks with different priorities
    tasks = [
        ("High priority task 1", "HIGH"),
        ("High priority task 2", "HIGH"),
        ("Medium priority task 1", "MEDIUM"),
        ("Medium priority task 2", "MEDIUM"),
        ("Low priority task 1", "LOW"),
    ]

    for title, priority in tasks:
        task = Task(
            title=title,
            description=f"Description for {title}",
            user_id=user_id,
            priority=priority,
            completed=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(task)

    db.commit()
    db.close()
    return user_id


def test_filter_tasks_by_high_priority(test_user_with_tasks):
    """
    T022: Test filtering tasks by HIGH priority.

    Given a user with tasks of various priorities
    When filtering by priority=HIGH
    Then only HIGH priority tasks should be returned
    """
    response = client.get(
        f"/api/users/{test_user_with_tasks}/tasks?priority=HIGH"
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["tasks"]) == 2
    for task in data["tasks"]:
        assert task["priority"] == "HIGH"


def test_filter_tasks_by_medium_priority(test_user_with_tasks):
    """
    T022: Test filtering tasks by MEDIUM priority.

    Given a user with tasks of various priorities
    When filtering by priority=MEDIUM
    Then only MEDIUM priority tasks should be returned
    """
    response = client.get(
        f"/api/users/{test_user_with_tasks}/tasks?priority=MEDIUM"
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["tasks"]) == 2
    for task in data["tasks"]:
        assert task["priority"] == "MEDIUM"


def test_filter_tasks_by_low_priority(test_user_with_tasks):
    """
    T022: Test filtering tasks by LOW priority.

    Given a user with tasks of various priorities
    When filtering by priority=LOW
    Then only LOW priority tasks should be returned
    """
    response = client.get(
        f"/api/users/{test_user_with_tasks}/tasks?priority=LOW"
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["tasks"]) == 1
    assert data["tasks"][0]["priority"] == "LOW"


def test_filter_tasks_by_invalid_priority(test_user_with_tasks):
    """
    T022: Test that invalid priority filter is rejected.

    Given a user with tasks
    When filtering by invalid priority
    Then the request should fail with validation error
    """
    response = client.get(
        f"/api/users/{test_user_with_tasks}/tasks?priority=INVALID"
    )

    assert response.status_code == 422


def test_no_filter_returns_all_tasks(test_user_with_tasks):
    """
    T022: Test that no filter returns all tasks.

    Given a user with tasks
    When requesting tasks without priority filter
    Then all tasks should be returned
    """
    response = client.get(
        f"/api/users/{test_user_with_tasks}/tasks"
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["tasks"]) == 5
    assert data["total"] == 5


def test_combine_priority_filter_with_pagination(test_user_with_tasks):
    """
    T022: Test combining priority filter with pagination.

    Given a user with tasks
    When filtering by priority=HIGH with limit=1
    Then only 1 HIGH priority task should be returned
    """
    response = client.get(
        f"/api/users/{test_user_with_tasks}/tasks?priority=HIGH&limit=1"
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["tasks"]) == 1
    assert data["tasks"][0]["priority"] == "HIGH"
    assert data["total"] == 2  # Total should still show all matching tasks
