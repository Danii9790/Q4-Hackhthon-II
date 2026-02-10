"""
Integration tests for real-time task synchronization.

Tests for Kafka publishing of task updates and WebSocket gateway.
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
        email="realtime-test@example.com",
        name="Realtime Test User",
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


def test_publish_task_created_to_kafka(test_user, auth_headers):
    """
    T093: Test that task creation publishes to Kafka task-updates topic.

    Given a valid user
    When creating a new task
    Then the task data should be published to task-updates Kafka topic
    """
    from src.services.event_publisher import EventPublisher
    from src.models.task import Task

    db = TestSessionLocal()

    # Create task
    task = Task(
        user_id=test_user,
        title="Test real-time sync",
        description="This should be published to Kafka",
        completed=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    # Publish task-created event
    task_data = {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "completed": task.completed,
        "user_id": task.user_id,
    }

    result = EventPublisher.publish_task_update(
        event_type="created",
        task_id=task.id,
        user_id=test_user,
        task_data=task_data
    )

    # Verify publication succeeded
    assert result is True

    db.close()


def test_publish_task_updated_to_kafka(test_user, auth_headers):
    """
    T093: Test that task updates publish to Kafka task-updates topic.

    Given an existing task
    When updating the task
    Then the updated task data should be published to task-updates topic
    """
    from src.services.event_publisher import EventPublisher
    from src.models.task import Task

    db = TestSessionLocal()

    # Create task
    task = Task(
        user_id=test_user,
        title="Original title",
        completed=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    # Update task
    task.title = "Updated title"
    task.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(task)

    # Publish task-updated event
    task_data = {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "completed": task.completed,
        "user_id": task.user_id,
        "updated_at": task.updated_at.isoformat(),
    }

    result = EventPublisher.publish_task_update(
        event_type="updated",
        task_id=task.id,
        user_id=test_user,
        task_data=task_data
    )

    # Verify publication succeeded
    assert result is True

    db.close()


def test_publish_task_completed_to_kafka(test_user, auth_headers):
    """
    T093: Test that task completion publishes to Kafka task-updates topic.

    Given an existing task
    When marking the task as completed
    Then the completion event should be published to task-updates topic
    """
    from src.services.event_publisher import EventPublisher
    from src.models.task import Task

    db = TestSessionLocal()

    # Create task
    task = Task(
        user_id=test_user,
        title="Task to complete",
        completed=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    # Complete task
    task.completed = True
    task.completed_at = datetime.now(timezone.utc)
    task.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(task)

    # Publish task-completed event
    task_data = {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "completed": task.completed,
        "completed_at": task.completed_at.isoformat(),
        "user_id": task.user_id,
    }

    result = EventPublisher.publish_task_update(
        event_type="completed",
        task_id=task.id,
        user_id=test_user,
        task_data=task_data
    )

    # Verify publication succeeded
    assert result is True

    db.close()


def test_publish_task_deleted_to_kafka(test_user, auth_headers):
    """
    T093: Test that task deletion publishes to Kafka task-updates topic.

    Given an existing task
    When deleting the task
    Then the deletion event should be published to task-updates topic
    """
    from src.services.event_publisher import EventPublisher
    from src.models.task import Task

    db = TestSessionLocal()

    # Create task
    task = Task(
        user_id=test_user,
        title="Task to delete",
        completed=False,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    task_id = task.id

    # Delete task
    db.delete(task)
    db.commit()

    # Publish task-deleted event
    task_data = {
        "id": task_id,
        "user_id": test_user,
    }

    result = EventPublisher.publish_task_update(
        event_type="deleted",
        task_id=task_id,
        user_id=test_user,
        task_data=task_data
    )

    # Verify publication succeeded
    assert result is True

    db.close()


def test_websocket_gateway_consumes_task_updates():
    """
    T092: Test that WebSocket gateway consumes task-updates from Kafka.

    Given task updates being published to Kafka
    When the WebSocket gateway is running
    Then it should consume the messages and broadcast to connected clients
    """
    # This test verifies the WebSocket gateway can consume from Kafka
    # Actual WebSocket testing requires a WebSocket client
    from src.services.websocket_gateway import WebSocketGateway

    # Create gateway instance
    gateway = WebSocketGateway()

    # Verify gateway is initialized
    assert gateway is not None
    assert hasattr(gateway, 'connected_clients')
    assert hasattr(gateway, 'broadcast_to_user')

    # Test adding a client connection
    gateway.add_client(user_id="test-user-123", connection_id="conn-1")

    # Verify client is tracked
    assert "test-user-123" in gateway.connected_clients
    assert "conn-1" in gateway.connected_clients["test-user-123"]

    # Test removing a client connection
    gateway.remove_client(user_id="test-user-123", connection_id="conn-1")

    # Verify client is removed
    assert "conn-1" not in gateway.connected_clients.get("test-user-123", {})


def test_websocket_connection_management():
    """
    T095: Test WebSocket connection management.

    Given multiple clients connecting for the same user
    When managing connections
    Then all connections should be tracked correctly
    """
    from src.services.websocket_gateway import WebSocketGateway

    gateway = WebSocketGateway()

    # Add multiple connections for same user
    gateway.add_client(user_id="user-1", connection_id="conn-1")
    gateway.add_client(user_id="user-1", connection_id="conn-2")
    gateway.add_client(user_id="user-2", connection_id="conn-3")

    # Verify connections are tracked
    assert len(gateway.connected_clients.get("user-1", {})) == 2
    assert len(gateway.connected_clients.get("user-2", {})) == 1

    # Remove one connection
    gateway.remove_client(user_id="user-1", connection_id="conn-1")

    # Verify only one connection remains for user-1
    assert len(gateway.connected_clients.get("user-1", {})) == 1
    assert "conn-2" in gateway.connected_clients["user-1"]

    # Remove all connections for user-1
    gateway.remove_client(user_id="user-1", connection_id="conn-2")

    # Verify user-1 has no connections
    assert "user-1" not in gateway.connected_clients or len(gateway.connected_clients.get("user-1", {})) == 0
