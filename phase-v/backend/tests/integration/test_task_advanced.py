"""
Integration tests for advanced task features.

Tests task creation with due_date, priority, and tags.
"""
import pytest
import os
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from jose import jwt

from src.main import app
from src.db.session import get_session
from src.models.task import Task, Priority


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


# Override dependency
app.dependency_overrides[get_session] = override_get_session

# Create test client
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Setup test database before each test."""
    # Create tables
    from src.models.task import Task
    from src.models.user import User
    Task.metadata.create_all(bind=test_engine)
    User.metadata.create_all(bind=test_engine)

    yield

    # Cleanup - drop all tables after test
    Task.metadata.drop_all(bind=test_engine)
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
    # Create a test JWT token
    from src.models.user import User
    from sqlalchemy import select

    db = TestSessionLocal()
    result = db.execute(select(User).where(User.id == test_user))
    user = result.scalar_one_or_none()

    if not user:
        db.close()
        raise ValueError(f"Test user {test_user} not found in database")

    # Get JWT config
    secret_key = os.getenv("BETTER_AUTH_SECRET", "test-secret-key-for-development-only")
    algorithm = "HS256"

    # Create token payload
    import time
    now = int(time.time())
    payload = {
        "sub": user.id,
        "email": user.email,
        "name": user.name,
        "iat": now,
        "exp": now + 3600  # 1 hour expiration
    }

    # Generate token
    token = jwt.encode(payload, secret_key, algorithm=algorithm)
    db.close()

    return {"Authorization": f"Bearer {token}"}


def test_create_task_with_due_date(test_user, auth_headers):
    """
    T021: Test task creation with due_date.

    Given a valid user
    When creating a task with a due_date
    Then the task should be persisted with the due_date
    """
    due_date = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

    response = client.post(
        f"/api/users/{test_user}/tasks",
        json={
            "title": "Task with due date",
            "description": "This task has a due date",
            "due_date": due_date,
            "priority": "HIGH"
        },
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Task with due date"
    assert data["due_date"] is not None
    assert data["priority"] == "HIGH"


def test_create_task_with_priority(test_user, auth_headers):
    """
    T021: Test task creation with priority.

    Given a valid user
    When creating a task with priority HIGH
    Then the task should be persisted with priority HIGH
    """
    response = client.post(
        f"/api/users/{test_user}/tasks",
        json={
            "title": "High priority task",
            "priority": "HIGH"
        },
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "High priority task"
    assert data["priority"] == "HIGH"


def test_create_task_with_tags(test_user, auth_headers):
    """
    T021: Test task creation with tags.

    Given a valid user
    When creating a task with tags ["work", "urgent"]
    Then the task should be persisted with the tags array
    """
    response = client.post(
        f"/api/users/{test_user}/tasks",
        json={
            "title": "Tagged task",
            "tags": ["work", "urgent", "frontend"]
        },
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Tagged task"
    assert data["tags"] == ["work", "urgent", "frontend"]


def test_create_task_with_all_advanced_fields(test_user, auth_headers):
    """
    T021: Test task creation with all advanced fields.

    Given a valid user
    When creating a task with due_date, priority, and tags
    Then all fields should be persisted correctly
    """
    due_date = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()

    response = client.post(
        f"/api/users/{test_user}/tasks",
        json={
            "title": "Complete advanced task",
            "description": "This has all advanced fields",
            "due_date": due_date,
            "priority": "MEDIUM",
            "tags": ["work", "phase-v", "important"]
        },
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Complete advanced task"
    assert data["due_date"] is not None
    assert data["priority"] == "MEDIUM"
    assert data["tags"] == ["work", "phase-v", "important"]


def test_invalid_priority_rejected(test_user, auth_headers):
    """
    T021: Test that invalid priority values are rejected.

    Given a valid user
    When creating a task with invalid priority "INVALID"
    Then the request should fail with validation error
    """
    response = client.post(
        f"/api/users/{test_user}/tasks",
        json={
            "title": "Invalid priority task",
            "priority": "INVALID_PRIORITY"
        },
        headers=auth_headers
    )

    assert response.status_code == 422  # Validation error


def test_invalid_tags_array_rejected(test_user, auth_headers):
    """
    T021: Test that invalid tags array is rejected (>10 tags).

    Given a valid user
    When creating a task with more than 10 tags
    Then the request should fail with validation error
    """
    # Create 11 tags (exceeds limit of 10)
    too_many_tags = [f"tag{i}" for i in range(11)]

    response = client.post(
        f"/api/users/{test_user}/tasks",
        json={
            "title": "Too many tags",
            "tags": too_many_tags
        },
        headers=auth_headers
    )

    assert response.status_code == 422  # Validation error


def test_past_due_date_accepted(test_user, auth_headers):
    """
    T021: Test that past due_date is accepted (user can create overdue tasks).

    Given a valid user
    When creating a task with a past due_date
    Then the task should be created (past dates allowed)
    """
    past_date = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()

    response = client.post(
        f"/api/users/{test_user}/tasks",
        json={
            "title": "Overdue task",
            "due_date": past_date
        },
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["due_date"] is not None
