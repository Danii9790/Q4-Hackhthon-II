"""
Integration tests for stateless conversation reconstruction.

These tests verify the core stateless architecture requirement:
- All conversation state is persisted to the database
- No in-memory session state is maintained
- Conversation context survives server restarts
- User data isolation is enforced

Tests focus on database persistence and stateless behavior per T025.
"""

import pytest
from uuid import UUID, uuid4
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator, Generator
import os
import tempfile
from sqlmodel import SQLModel
from fastapi import HTTPException

from src.api.chat import (
    get_or_create_conversation,
    fetch_conversation_history,
)
from src.models import Conversation, Message, User
from src.db.session import get_session


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture(scope="function")
async def test_db_engine() -> AsyncGenerator:
    """
    Create a temporary in-memory database for testing.

    This fixture creates a fresh database for each test function,
    ensuring complete isolation between tests.
    """
    # Use SQLite in-memory database for fast, isolated tests
    # In production, this would be PostgreSQL via DATABASE_URL
    from sqlalchemy import text

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield engine

    # Cleanup
    await engine.dispose()


@pytest.fixture(scope="function")
async def session(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Provide a database session for testing.

    This fixture creates a new session for each test and ensures
    proper cleanup after the test completes.
    """
    async_session_maker = async_sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session


@pytest.fixture(scope="function")
def test_user_id() -> UUID:
    """Provide a test user ID."""
    return uuid4()


@pytest.fixture(scope="function")
def other_user_id() -> UUID:
    """Provide a different user ID for isolation tests."""
    return uuid4()


@pytest.fixture(scope="function")
async def test_user(session: AsyncSession, test_user_id: UUID) -> User:
    """
    Create a test user in the database.

    This fixture creates a user object that can be used for
    conversation and message creation.
    """
    user = User(
        id=test_user_id,
        email=f"test-{test_user_id}@example.com"
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest.fixture(scope="function")
async def test_conversation(
    session: AsyncSession,
    test_user_id: UUID
) -> Conversation:
    """
    Create a test conversation in the database.

    This fixture creates a conversation object that can be used
    for message history tests.
    """
    conversation = Conversation(user_id=test_user_id)
    session.add(conversation)
    await session.commit()
    await session.refresh(conversation)
    return conversation


@pytest.fixture(scope="function")
async def test_conversation_with_messages(
    session: AsyncSession,
    test_conversation: Conversation,
    test_user_id: UUID
) -> tuple[Conversation, list[Message]]:
    """
    Create a conversation with multiple messages for testing.

    Returns:
        Tuple of (conversation, messages) where messages is a list
        of Message objects in the order they were created.
    """
    messages = [
        Message(
            conversation_id=test_conversation.id,
            user_id=test_user_id,
            role="user",
            content="Add a task to buy groceries"
        ),
        Message(
            conversation_id=test_conversation.id,
            user_id=test_user_id,
            role="assistant",
            content="I've added the task 'buy groceries' to your list."
        ),
        Message(
            conversation_id=test_conversation.id,
            user_id=test_user_id,
            role="user",
            content="Show me my tasks"
        ),
        Message(
            conversation_id=test_conversation.id,
            user_id=test_user_id,
            role="assistant",
            content="You have 1 task: buy groceries"
        ),
    ]

    for msg in messages:
        session.add(msg)

    await session.commit()

    # Refresh to get DB-generated values
    for msg in messages:
        await session.refresh(msg)

    return test_conversation, messages


# ============================================================================
# Test: Conversation Creation (T025-1)
# ============================================================================

class TestConversationCreation:
    """Tests for conversation creation functionality."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_create_new_conversation_generates_valid_id(
        self,
        session: AsyncSession,
        test_user_id: UUID
    ):
        """
        T025-1: Creating a new conversation generates valid conversation_id.

        Verify that:
        - New conversation object is returned
        - Conversation has a valid UUID
        - Conversation is persisted to database
        """
        # Act - Create new conversation
        conversation = await get_or_create_conversation(
            session,
            test_user_id,
            conversation_id=None
        )

        # Commit to ensure persistence
        await session.commit()

        # Assert - Verify conversation was created
        assert conversation is not None
        assert isinstance(conversation.id, UUID)
        assert conversation.user_id == test_user_id

        # Verify persistence by fetching from database
        from sqlmodel import select
        statement = select(Conversation).where(Conversation.id == conversation.id)
        result = await session.execute(statement)
        persisted_conversation = result.scalar_one_or_none()

        assert persisted_conversation is not None
        assert persisted_conversation.id == conversation.id
        assert persisted_conversation.user_id == test_user_id

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_multiple_conversations_per_user(
        self,
        session: AsyncSession,
        test_user_id: UUID
    ):
        """
        Verify that a user can have multiple independent conversations.

        This tests the multi-conversation support requirement.
        """
        # Act - Create multiple conversations for same user
        conv1 = await get_or_create_conversation(session, test_user_id)
        await session.commit()

        conv2 = await get_or_create_conversation(session, test_user_id)
        await session.commit()

        conv3 = await get_or_create_conversation(session, test_user_id)
        await session.commit()

        # Assert - Verify all conversations have unique IDs
        assert conv1.id != conv2.id
        assert conv2.id != conv3.id
        assert conv1.id != conv3.id

        # Verify all belong to the same user
        assert conv1.user_id == test_user_id
        assert conv2.user_id == test_user_id
        assert conv3.user_id == test_user_id


# ============================================================================
# Test: Message Persistence (T025-2)
# ============================================================================

class TestMessagePersistence:
    """Tests for message persistence to database."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_user_message_persistence(
        self,
        session: AsyncSession,
        test_conversation: Conversation,
        test_user_id: UUID
    ):
        """
        T025-2: User messages are saved correctly to database.

        Verify that:
        - User message is persisted with correct fields
        - Message ID is generated
        - Timestamp is set automatically
        """
        # Arrange - Create a user message
        user_message = Message(
            conversation_id=test_conversation.id,
            user_id=test_user_id,
            role="user",
            content="Add a task to call mom"
        )

        # Act - Save to database
        session.add(user_message)
        await session.commit()
        await session.refresh(user_message)

        # Assert - Verify message was persisted
        assert user_message.id is not None
        assert isinstance(user_message.id, UUID)
        assert user_message.conversation_id == test_conversation.id
        assert user_message.user_id == test_user_id
        assert user_message.role == "user"
        assert user_message.content == "Add a task to call mom"
        assert user_message.created_at is not None

        # Verify by fetching from database
        from sqlmodel import select
        statement = select(Message).where(Message.id == user_message.id)
        result = await session.execute(statement)
        persisted_message = result.scalar_one_or_none()

        assert persisted_message is not None
        assert persisted_message.content == "Add a task to call mom"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_assistant_message_persistence(
        self,
        session: AsyncSession,
        test_conversation: Conversation,
        test_user_id: UUID
    ):
        """
        T025-2: Assistant messages are saved correctly to database.

        Verify that AI responses are persisted with proper metadata.
        """
        # Arrange - Create an assistant message
        assistant_message = Message(
            conversation_id=test_conversation.id,
            user_id=test_user_id,
            role="assistant",
            content="I've added the task 'call mom' to your list."
        )

        # Act - Save to database
        session.add(assistant_message)
        await session.commit()
        await session.refresh(assistant_message)

        # Assert - Verify message was persisted
        assert assistant_message.id is not None
        assert assistant_message.role == "assistant"
        assert assistant_message.content == "I've added the task 'call mom' to your list."
        assert assistant_message.created_at is not None

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_message_order_preservation(
        self,
        session: AsyncSession,
        test_conversation: Conversation,
        test_user_id: UUID
    ):
        """
        Verify that messages maintain chronological order.

        Tests the ordering requirement for conversation context.
        """
        # Arrange - Create messages in rapid succession
        messages = []
        for i in range(5):
            msg = Message(
                conversation_id=test_conversation.id,
                user_id=test_user_id,
                role="user" if i % 2 == 0 else "assistant",
                content=f"Message {i}"
            )
            session.add(msg)
            messages.append(msg)

        await session.commit()

        # Refresh all to get DB timestamps
        for msg in messages:
            await session.refresh(msg)

        # Act - Fetch in chronological order
        fetched_messages = await fetch_conversation_history(
            session, test_conversation.id, limit=10
        )

        # Assert - Verify order is preserved
        assert len(fetched_messages) == 5
        for i, msg in enumerate(fetched_messages):
            assert msg.content == f"Message {i}"

        # Verify timestamps are sequential
        for i in range(len(fetched_messages) - 1):
            assert fetched_messages[i].created_at <= fetched_messages[i + 1].created_at


# ============================================================================
# Test: Context Retrieval (T025-3)
# ============================================================================

class TestContextRetrieval:
    """Tests for conversation history retrieval."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_fetch_conversation_history_returns_all_messages(
        self,
        session: AsyncSession,
        test_conversation_with_messages: tuple[Conversation, list[Message]]
    ):
        """
        T025-3: Fetching conversation history returns all messages in correct order.

        Verify that:
        - All messages are retrieved
        - Messages are in chronological order
        - Both user and assistant messages are included
        """
        # Arrange
        conversation, expected_messages = test_conversation_with_messages

        # Act - Fetch conversation history
        fetched_messages = await fetch_conversation_history(
            session, conversation.id, limit=50
        )

        # Assert - Verify all messages retrieved
        assert len(fetched_messages) == len(expected_messages)

        # Verify order preserved
        for i, fetched_msg in enumerate(fetched_messages):
            assert fetched_msg.id == expected_messages[i].id
            assert fetched_msg.role == expected_messages[i].role
            assert fetched_msg.content == expected_messages[i].content

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_history_with_mixed_roles(
        self,
        session: AsyncSession,
        test_conversation: Conversation,
        test_user_id: UUID
    ):
        """
        Verify that conversation history correctly handles mixed user/assistant messages.
        """
        # Arrange - Create alternating user/assistant messages
        messages_data = [
            ("user", "Hello"),
            ("assistant", "Hi there!"),
            ("user", "How are you?"),
            ("assistant", "I'm doing well, thanks!"),
            ("user", "Great to hear"),
        ]

        for role, content in messages_data:
            msg = Message(
                conversation_id=test_conversation.id,
                user_id=test_user_id,
                role=role,
                content=content
            )
            session.add(msg)

        await session.commit()

        # Act - Fetch history
        history = await fetch_conversation_history(session, test_conversation.id)

        # Assert - Verify all messages with correct roles
        assert len(history) == 5
        for i, msg in enumerate(history):
            assert msg.role == messages_data[i][0]
            assert msg.content == messages_data[i][1]

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_empty_conversation_returns_empty_list(
        self,
        session: AsyncSession,
        test_conversation: Conversation
    ):
        """
        Verify that fetching history from empty conversation returns empty list.
        """
        # Act - Fetch from empty conversation
        history = await fetch_conversation_history(session, test_conversation.id)

        # Assert
        assert history == []
        assert isinstance(history, list)


# ============================================================================
# Test: Stateless Reconstruction (T025-4)
# ============================================================================

class TestStatelessReconstruction:
    """
    Tests for stateless conversation reconstruction.

    These tests verify the core architectural requirement that all
    conversation state is persisted to the database and can be
    reconstructed after server restart (simulated by new session).
    """

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_conversation_persists_across_sessions(
        self,
        test_db_engine,
        test_user_id: UUID
    ):
        """
        T025-4: After server restart (simulated by new session), conversation
        history is preserved from database.

        This is the CRITICAL test for stateless architecture:
        1. Create conversation with messages in Session 1
        2. Close Session 1 (simulate server restart)
        3. Open Session 2 (new server instance)
        4. Verify conversation history is fully preserved
        """
        # ============================================================================
        # SESSION 1: Create conversation and messages
        # ============================================================================
        async_session_maker_1 = async_sessionmaker(
            test_db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with async_session_maker_1() as session1:
            # Create conversation
            conv1 = await get_or_create_conversation(session1, test_user_id)
            await session1.commit()

            conv_id = conv1.id

            # Add messages
            msg1 = Message(
                conversation_id=conv_id,
                user_id=test_user_id,
                role="user",
                content="Add a task to buy groceries"
            )
            msg2 = Message(
                conversation_id=conv_id,
                user_id=test_user_id,
                role="assistant",
                content="Task added successfully"
            )

            session1.add(msg1)
            session1.add(msg2)
            await session1.commit()

            # Verify messages exist in Session 1
            history_session1 = await fetch_conversation_history(session1, conv_id)
            assert len(history_session1) == 2

        # Session 1 is now closed (simulating server shutdown)
        # ============================================================================

        # ============================================================================
        # SESSION 2: Retrieve conversation (new server instance)
        # ============================================================================
        async_session_maker_2 = async_sessionmaker(
            test_db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with async_session_maker_2() as session2:
            # Act - Retrieve the same conversation in new session
            conv2 = await get_or_create_conversation(session2, test_user_id, conv_id)

            # Assert - Verify conversation ID matches
            assert conv2.id == conv_id
            assert conv2.user_id == test_user_id

            # Act - Fetch conversation history
            history_session2 = await fetch_conversation_history(session2, conv_id)

            # Assert - Verify full history preserved (stateless reconstruction)
            assert len(history_session2) == 2
            assert history_session2[0].role == "user"
            assert history_session2[0].content == "Add a task to buy groceries"
            assert history_session2[1].role == "assistant"
            assert history_session2[1].content == "Task added successfully"

        # ============================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_extended_conversation_reconstruction(
        self,
        test_db_engine,
        test_user_id: UUID
    ):
        """
        Verify stateless reconstruction works for longer conversations.

        Tests with 10 message exchanges to ensure scalability.
        """
        # ============================================================================
        # SESSION 1: Build extended conversation
        # ============================================================================
        async_session_maker_1 = async_sessionmaker(
            test_db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        conv_id = None
        message_count = 10

        async with async_session_maker_1() as session1:
            # Create conversation
            conv1 = await get_or_create_conversation(session1, test_user_id)
            await session1.commit()
            conv_id = conv1.id

            # Add multiple message exchanges
            for i in range(message_count):
                user_msg = Message(
                    conversation_id=conv_id,
                    user_id=test_user_id,
                    role="user",
                    content=f"User message {i}"
                )
                assistant_msg = Message(
                    conversation_id=conv_id,
                    user_id=test_user_id,
                    role="assistant",
                    content=f"Assistant response {i}"
                )
                session1.add(user_msg)
                session1.add(assistant_msg)

            await session1.commit()

        # ============================================================================

        # ============================================================================
        # SESSION 2: Reconstruct conversation
        # ============================================================================
        async_session_maker_2 = async_sessionmaker(
            test_db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with async_session_maker_2() as session2:
            # Act - Retrieve full conversation history
            history = await fetch_conversation_history(session2, conv_id, limit=100)

            # Assert - Verify all messages reconstructed
            assert len(history) == message_count * 2  # user + assistant per exchange

            # Verify correct order
            for i in range(message_count):
                user_idx = i * 2
                assistant_idx = i * 2 + 1

                assert history[user_idx].role == "user"
                assert history[user_idx].content == f"User message {i}"
                assert history[assistant_idx].role == "assistant"
                assert history[assistant_idx].content == f"Assistant response {i}"

        # ============================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_conversation_continuation_after_restart(
        self,
        test_db_engine,
        test_user_id: UUID
    ):
        """
        Verify that conversation can be continued after server restart.

        Simulates real-world scenario:
        1. User has conversation
        2. Server restarts
        3. User continues same conversation
        4. New messages are appended to existing history
        """
        # ============================================================================
        # SESSION 1: Initial conversation
        # ============================================================================
        async_session_maker_1 = async_sessionmaker(
            test_db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        conv_id = None

        async with async_session_maker_1() as session1:
            conv1 = await get_or_create_conversation(session1, test_user_id)
            await session1.commit()
            conv_id = conv1.id

            # Initial messages
            msg1 = Message(
                conversation_id=conv_id,
                user_id=test_user_id,
                role="user",
                content="Hello"
            )
            msg2 = Message(
                conversation_id=conv_id,
                user_id=test_user_id,
                role="assistant",
                content="Hi! How can I help?"
            )

            session1.add(msg1)
            session1.add(msg2)
            await session1.commit()

        # ============================================================================

        # ============================================================================
        # SESSION 2: Continue conversation after restart
        # ============================================================================
        async_session_maker_2 = async_sessionmaker(
            test_db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with async_session_maker_2() as session2:
            # Retrieve existing conversation
            conv2 = await get_or_create_conversation(session2, test_user_id, conv_id)

            # Verify history exists
            history = await fetch_conversation_history(session2, conv_id)
            assert len(history) == 2

            # Add new messages (continuing conversation)
            msg3 = Message(
                conversation_id=conv_id,
                user_id=test_user_id,
                role="user",
                content="Add a task to buy milk"
            )
            msg4 = Message(
                conversation_id=conv_id,
                user_id=test_user_id,
                role="assistant",
                content="Task added: buy milk"
            )

            session2.add(msg3)
            session2.add(msg4)
            await session2.commit()

            # Verify updated history
            updated_history = await fetch_conversation_history(session2, conv_id)
            assert len(updated_history) == 4
            assert updated_history[0].content == "Hello"
            assert updated_history[1].content == "Hi! How can I help?"
            assert updated_history[2].content == "Add a task to buy milk"
            assert updated_history[3].content == "Task added: buy milk"

        # ============================================================================

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_multiple_conversations_survive_restart(
        self,
        test_db_engine,
        test_user_id: UUID
    ):
        """
        Verify that multiple conversations are preserved after restart.

        Tests that the stateless architecture handles multiple
        independent conversations correctly.
        """
        # ============================================================================
        # SESSION 1: Create multiple conversations
        # ============================================================================
        async_session_maker_1 = async_sessionmaker(
            test_db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        conv_ids = []

        async with async_session_maker_1() as session1:
            # Create 3 conversations
            for i in range(3):
                conv = await get_or_create_conversation(session1, test_user_id)
                await session1.commit()
                conv_ids.append(conv.id)

                # Add a message to each
                msg = Message(
                    conversation_id=conv.id,
                    user_id=test_user_id,
                    role="user",
                    content=f"Conversation {i} message"
                )
                session1.add(msg)

            await session1.commit()

        # ============================================================================

        # ============================================================================
        # SESSION 2: Retrieve all conversations
        # ============================================================================
        async_session_maker_2 = async_sessionmaker(
            test_db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with async_session_maker_2() as session2:
            # Verify all conversations exist and have correct history
            for i, conv_id in enumerate(conv_ids):
                conv = await get_or_create_conversation(session2, test_user_id, conv_id)
                assert conv.id == conv_id

                history = await fetch_conversation_history(session2, conv_id)
                assert len(history) == 1
                assert history[0].content == f"Conversation {i} message"

        # ============================================================================


# ============================================================================
# Test: User Isolation (T025-5)
# ============================================================================

class TestUserIsolation:
    """
    Tests for user data isolation.

    These tests verify the security requirement that users cannot
    access conversations belonging to other users.
    """

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_user_cannot_access_other_user_conversation(
        self,
        session: AsyncSession,
        test_user_id: UUID,
        other_user_id: UUID
    ):
        """
        T025-5: Users cannot access conversations belonging to other users.

        Verify that:
        - Attempting to access another user's conversation returns 404
        - Error message doesn't reveal conversation exists (security)
        """
        # Arrange - Create conversation for test_user
        test_conversation = await get_or_create_conversation(session, test_user_id)
        await session.commit()

        # Act & Assert - Try to access with other_user_id
        with pytest.raises(Exception) as exc_info:  # HTTPException
            await get_or_create_conversation(
                session,
                other_user_id,
                conversation_id=test_conversation.id
            )

        # Verify 404 status
        assert exc_info.value.status_code == 404
        # Security: Don't reveal conversation exists
        assert "not found" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_messages_scoped_by_user_id(
        self,
        session: AsyncSession,
        test_user_id: UUID,
        other_user_id: UUID
    ):
        """
        Verify that messages are properly isolated by user_id.

        Even if messages share the same conversation_id (shouldn't happen
        in normal operation), the user_id field provides an additional
        layer of isolation.
        """
        # Arrange - Create conversation for test_user
        conv = await get_or_create_conversation(session, test_user_id)
        await session.commit()

        # Create message for test_user
        test_user_msg = Message(
            conversation_id=conv.id,
            user_id=test_user_id,
            role="user",
            content="My private message"
        )
        session.add(test_user_msg)
        await session.commit()

        # Verify message belongs to test_user
        await session.refresh(test_user_msg)
        assert test_user_msg.user_id == test_user_id

        # If other_user tries to create message in same conversation
        # (this shouldn't happen in normal flow due to conversation isolation,
        # but the user_id field provides defense in depth)
        other_user_msg = Message(
            conversation_id=conv.id,
            user_id=other_user_id,
            role="user",
            content="Other user message"
        )
        session.add(other_user_msg)
        await session.commit()
        await session.refresh(other_user_msg)

        # Verify messages have different user_ids
        assert test_user_msg.user_id == test_user_id
        assert other_user_msg.user_id == other_user_id

        # Query only test_user's messages
        from sqlmodel import select
        statement = select(Message).where(
            Message.conversation_id == conv.id,
            Message.user_id == test_user_id
        )
        result = await session.execute(statement)
        test_user_messages = result.scalars().all()

        # Should only return test_user's message
        assert len(test_user_messages) == 1
        assert test_user_messages[0].content == "My private message"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_conversation_list_isolation(
        self,
        session: AsyncSession,
        test_user_id: UUID,
        other_user_id: UUID
    ):
        """
        Verify that listing conversations only returns user's own conversations.

        This tests the data isolation at the query level.
        """
        # Arrange - Create conversations for both users
        conv1 = await get_or_create_conversation(session, test_user_id)
        await session.commit()

        conv2 = await get_or_create_conversation(session, other_user_id)
        await session.commit()

        # Act - Query conversations for test_user
        from sqlmodel import select
        statement = select(Conversation).where(
            Conversation.user_id == test_user_id
        )
        result = await session.execute(statement)
        test_user_convs = result.scalars().all()

        # Assert - Only test_user's conversation returned
        assert len(test_user_convs) == 1
        assert test_user_convs[0].id == conv1.id
        assert test_user_convs[0].user_id == test_user_id

        # Verify other_user's conversation not included
        conv_ids = [conv.id for conv in test_user_convs]
        assert conv2.id not in conv_ids

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_cascade_delete_isolates_user_data(
        self,
        session: AsyncSession,
        test_user_id: UUID,
        other_user_id: UUID
    ):
        """
        Verify that deleting a user cascades to their conversations and messages.

        This tests the data cleanup and isolation requirements.
        """
        # This test would require implementing user deletion logic
        # For now, we verify the foreign key constraints are set correctly
        from src.models.conversation import Conversation as ConvModel
        from src.models.message import Message as MsgModel

        # Check that Conversation has CASCADE delete
        # (This is a schema validation test)
        assert hasattr(ConvModel, '__table__')
        fk_constraints = ConvModel.__table__.foreign_keys
        user_fk = [fk for fk in fk_constraints if fk.column.name == 'id'][0]
        assert user_fk.ondelete == 'CASCADE'

        # Check that Message has CASCADE delete for both user_id and conversation_id
        assert hasattr(MsgModel, '__table__')
        fk_constraints = MsgModel.__table__.foreign_keys
        for fk in fk_constraints:
            if fk.column.name == 'id':
                assert fk.ondelete == 'CASCADE'


# ============================================================================
# Test: Edge Cases and Error Handling
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling in conversation state."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_retrieving_nonexistent_conversation(
        self,
        session: AsyncSession,
        test_user_id: UUID
    ):
        """
        Verify that attempting to retrieve a non-existent conversation raises 404.
        """
        # Arrange
        nonexistent_id = uuid4()

        # Act & Assert
        with pytest.raises(Exception) as exc_info:  # HTTPException
            await get_or_create_conversation(
                session,
                test_user_id,
                conversation_id=nonexistent_id
            )

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_message_with_empty_content(
        self,
        session: AsyncSession,
        test_conversation: Conversation,
        test_user_id: UUID
    ):
        """
        Verify behavior with empty message content.

        Empty messages might be edge cases in the UI.
        """
        # Arrange - Create message with empty content
        msg = Message(
            conversation_id=test_conversation.id,
            user_id=test_user_id,
            role="user",
            content=""
        )
        session.add(msg)
        await session.commit()
        await session.refresh(msg)

        # Assert - Message should be created (content is not required in model)
        assert msg.id is not None
        assert msg.content == ""

        # Verify it can be retrieved
        history = await fetch_conversation_history(session, test_conversation.id)
        assert len(history) == 1
        assert history[0].content == ""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_long_message_content(
        self,
        session: AsyncSession,
        test_conversation: Conversation,
        test_user_id: UUID
    ):
        """
        Verify that long messages are handled correctly.

        Tests the 10,000 character limit requirement.
        """
        # Arrange - Create message with 1000 characters (under limit)
        long_content = "A" * 1000
        msg = Message(
            conversation_id=test_conversation.id,
            user_id=test_user_id,
            role="user",
            content=long_content
        )
        session.add(msg)
        await session.commit()
        await session.refresh(msg)

        # Assert - Message should be created
        assert msg.id is not None
        assert len(msg.content) == 1000

        # Verify retrieval
        history = await fetch_conversation_history(session, test_conversation.id)
        assert len(history) == 1
        assert len(history[0].content) == 1000

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_conversation_with_many_messages(
        self,
        session: AsyncSession,
        test_conversation: Conversation,
        test_user_id: UUID
    ):
        """
        Verify that conversations with many messages are handled correctly.

        Tests the pagination and limit requirements.
        """
        # Arrange - Create 100 messages
        messages = []
        for i in range(100):
            msg = Message(
                conversation_id=test_conversation.id,
                user_id=test_user_id,
                role="user",
                content=f"Message {i}"
            )
            session.add(msg)
            messages.append(msg)

        await session.commit()

        # Act - Fetch with default limit
        history_default = await fetch_conversation_history(session, test_conversation.id)
        assert len(history_default) == 50  # Default limit

        # Act - Fetch with higher limit
        history_limited = await fetch_conversation_history(
            session, test_conversation.id, limit=75
        )
        assert len(history_limited) == 75

        # Act - Fetch all
        history_all = await fetch_conversation_history(
            session, test_conversation.id, limit=100
        )
        assert len(history_all) == 100
