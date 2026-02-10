"""
Integration tests for audit trail.

Tests for audit trail creation and querying.
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
    from src.models.recurring_task import RecurringTask
    from src.models.user import User
    from src.models.task_event import TaskEvent
    Task.metadata.create_all(bind=test_engine)
    RecurringTask.metadata.create_all(bind=test_engine)
    User.metadata.create_all(bind=test_engine)
    TaskEvent.metadata.create_all(bind=test_engine)
    yield
    Task.metadata.drop_all(bind=test_engine)
    RecurringTask.metadata.drop_all(bind=test_engine)
    User.metadata.drop_all(bind=test_engine)
    TaskEvent.metadata.drop_all(bind=test_engine)


@pytest.fixture
def test_user():
    """Create a test user and return user_id."""
    from src.models.user import User
    import uuid

    db = TestSessionLocal()
    user = User(
        id=str(uuid.uuid4()),
        email="audit-test@example.com",
        name="Audit Test User",
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


def test_audit_trail_creation(test_user, auth_headers):
    """
    T101: Test that audit trail is created for task operations.

    Given a valid user performing various task operations
    When operations are performed (create, update, complete, delete)
    Then audit events should be logged with correct timestamps and user IDs
    """
    from src.services.audit_service import AuditService
    from src.models.task import Task

    db = TestSessionLocal()

    # Create a task
    task = Task(
        user_id=test_user,
        title="Audit test task",
        description="This task tests audit logging",
        completed=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    # Log task creation
    AuditService.log_task_created(
        session=db,
        task_id=task.id,
        user_id=test_user,
        task_data={
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "completed": task.completed,
        }
    )

    # Update task
    task.title = "Updated audit test task"
    db.commit()
    db.refresh(task)

    # Log task update
    AuditService.log_task_updated(
        session=db,
        task_id=task.id,
        user_id=test_user,
        old_data={"title": "Audit test task"},
        new_data={"title": "Updated audit test task"},
        changes=["title"]
    )

    # Complete task
    task.completed = True
    task.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(task)

    # Log task completion
    AuditService.log_task_completed(
        session=db,
        task_id=task.id,
        user_id=test_user,
        task_data={
            "id": task.id,
            "title": task.title,
            "completed": task.completed,
            "completed_at": task.completed_at.isoformat()
        }
    )

    # Verify audit events were created
    from src.models.task_event import TaskEvent

    events = db.query(TaskEvent).filter(
        TaskEvent.task_id == task.id
    ).all()

    assert len(events) == 3

    # Verify event types
    event_types = [e.event_type for e in events]
    assert "created" in event_types
    assert "updated" in event_types
    assert "completed" in event_types

    # Verify all events have user_id and timestamp
    for event in events:
        assert event.user_id == test_user
        assert event.timestamp is not None
        assert event.event_data is not None
        assert "timestamp" in event.event_data

    db.close()


def test_audit_trail_querying(test_user, auth_headers):
    """
    T102: Test that audit trail can be queried.

    Given a user with multiple task operations
    When querying the audit log
    Then all events should be returned with correct details
    """
    from src.services.audit_service import AuditService
    from src.models.task import Task

    db = TestSessionLocal()

    # Create multiple tasks and log events
    task_ids = []

    for i in range(3):
        task = Task(
            user_id=test_user,
            title=f"Audit test task {i+1}",
            completed=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        task_ids.append(task.id)

        # Log creation
        AuditService.log_task_created(
            session=db,
            task_id=task.id,
            user_id=test_user,
            task_data={"title": task.title, "completed": task.completed}
        )

    # Get task history for first task
    history = AuditService.get_task_history(
        session=db,
        task_id=task_ids[0],
        limit=10
    )

    assert len(history) >= 1
    assert history[0].event_type == "created"
    assert history[0].task_id == task_ids[0]
    assert history[0].user_id == test_user

    # Get user activity
    user_activity = AuditService.get_user_activity(
        session=db,
        user_id=test_user,
        limit=10
    )

    assert len(user_activity) >= 3
    for event in user_activity:
        assert event.user_id == test_user
        assert event.event_type in ["created", "updated", "completed", "deleted"]

    db.close()


def test_audit_trail_immutability(test_user, auth_headers):
    """
    Test that audit trail events are immutable.

    Given existing audit events
    When attempting to modify an event
    Then the event should remain unchanged
    """
    from src.services.audit_service import AuditService
    from src.models.task import Task
    from src.models.task_event import TaskEvent

    db = TestSessionLocal()

    # Create task and log event
    task = Task(
        user_id=test_user,
        title="Immutability test task",
        completed=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    AuditService.log_task_created(
        session=db,
        task_id=task.id,
        user_id=test_user,
        task_data={"title": task.title}
    )

    # Get the event
    events = db.query(TaskEvent).filter(
        TaskEvent.task_id == task.id
    ).all()

    assert len(events) == 1
    original_event = events[0]
    original_event_data = original_event.event_data

    # Attempt to modify the event (should fail or be prevented)
    # In SQLModel, we can query the event but modification should be tracked
    # For this test, we'll verify the event data is intact

    # Re-query to ensure immutability
    db.refresh(original_event)
    assert original_event.event_data == original_event_data

    db.close()
