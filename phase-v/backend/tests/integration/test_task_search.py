"""
Integration tests for task full-text search.

Tests searching tasks by title and description text.
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
def test_user_with_searchable_tasks():
    """Create a test user with searchable tasks."""
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

    # Create tasks with searchable content
    tasks = [
        ("Complete backend API implementation", "Build REST API with FastAPI for task management"),
        ("Frontend dashboard design", "Create responsive dashboard UI with React components"),
        ("Database schema migration", "Write Alembic migration for new Phase V tables"),
        ("Write unit tests", "Add comprehensive tests for all backend services"),
        ("Deploy to production", "Set up CI/CD pipeline and deploy to DigitalOcean"),
        ("Code review session", "Review pull requests from team members"),
    ]

    now = datetime.now(timezone.utc)
    for title, description in tasks:
        task = Task(
            title=title,
            description=description,
            user_id=user_id,
            completed=False,
            created_at=now,
            updated_at=now
        )
        db.add(task)

    db.commit()
    db.close()
    return user_id


def test_search_tasks_by_title_keyword(test_user_with_searchable_tasks):
    """
    T024: Test searching tasks by title keyword.

    Given a user with tasks
    When searching for keyword "API"
    Then tasks with "API" in title should be returned
    """
    response = client.get(
        f"/api/users/{test_user_with_searchable_tasks}/tasks?search=API"
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["tasks"]) >= 1

    # At least one task should have "API" in title or description
    found_api = any("API" in t["title"] or (t["description"] and "API" in t["description"])
                   for t in data["tasks"])
    assert found_api


def test_search_tasks_by_description_keyword(test_user_with_searchable_tasks):
    """
    T024: Test searching tasks by description keyword.

    Given a user with tasks
    When searching for keyword "FastAPI"
    Then tasks with "FastAPI" in description should be returned
    """
    response = client.get(
        f"/api/users/{test_user_with_searchable_tasks}/tasks?search=FastAPI"
    )

    assert response.status_code == 200
    data = response.json()

    # Should find the task with FastAPI in description
    assert len(data["tasks"]) >= 1
    found = any(t["description"] and "FastAPI" in t["description"]
                for t in data["tasks"])
    assert found


def test_search_tasks_case_insensitive(test_user_with_searchable_tasks):
    """
    T024: Test that search is case-insensitive.

    Given a user with tasks
    When searching for "dashboard" (lowercase)
    Then tasks with "Dashboard" (capitalized) should be found
    """
    response = client.get(
        f"/api/users/{test_user_with_searchable_tasks}/tasks?search=dashboard"
    )

    assert response.status_code == 200
    data = response.json()

    # Should find task with "Dashboard" (case-insensitive)
    found = any("dashboard" in t["title"].lower() or
                (t["description"] and "dashboard" in t["description"].lower())
                for t in data["tasks"])
    assert found


def test_search_tasks_partial_match(test_user_with_searchable_tasks):
    """
    T024: Test that search supports partial matching.

    Given a user with tasks
    When searching for "test"
    Then tasks with "testing", "tests", etc. should be found
    """
    response = client.get(
        f"/api/users/{test_user_with_searchable_tasks}/tasks?search=test"
    )

    assert response.status_code == 200
    data = response.json()

    # Should find tasks with "test" in any form
    found = any("test" in t["title"].lower() or
                (t["description"] and "test" in t["description"].lower())
                for t in data["tasks"])
    assert found


def test_search_empty_query_returns_all(test_user_with_searchable_tasks):
    """
    T024: Test that empty search query returns all tasks.

    Given a user with tasks
    When searching with empty query string
    Then all tasks should be returned
    """
    response = client.get(
        f"/api/users/{test_user_with_searchable_tasks}/tasks?search="
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["tasks"]) == 6


def test_search_no_results(test_user_with_searchable_tasks):
    """
    T024: Test search with no matching results.

    Given a user with tasks
    When searching for non-existent keyword "xyz123"
    Then empty task list should be returned
    """
    response = client.get(
        f"/api/users/{test_user_with_searchable_tasks}/tasks?search=xyz123"
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["tasks"]) == 0
    assert data["total"] == 0


def test_combine_search_with_filters(test_user_with_searchable_tasks):
    """
    T024: Test combining search with other filters.

    Given a user with tasks
    When searching "API" with limit=2
    Then at most 2 matching tasks should be returned
    """
    response = client.get(
        f"/api/users/{test_user_with_searchable_tasks}/tasks?search=API&limit=2"
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["tasks"]) <= 2
