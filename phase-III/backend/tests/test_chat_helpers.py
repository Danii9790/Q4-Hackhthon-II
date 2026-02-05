"""
Tests for chat API helper functions.

Tests conversation creation/retrieval and message history fetching logic.
"""

import pytest
from uuid import UUID, uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.chat import (
    get_or_create_conversation,
    fetch_conversation_history,
)
from src.models import Conversation, Message


class TestGetOrCreateConversation:
    """Tests for get_or_create_conversation function."""

    @pytest.mark.asyncio
    async def test_create_new_conversation_when_no_id_provided(
        self, session: AsyncSession, test_user_id: UUID
    ):
        """Test that new conversation is created when conversation_id is None."""
        # Act
        conversation = await get_or_create_conversation(
            session, test_user_id, conversation_id=None
        )

        # Assert
        assert conversation is not None
        assert conversation.user_id == test_user_id
        assert isinstance(conversation.id, UUID)

    @pytest.mark.asyncio
    async def test_retrieve_existing_conversation(
        self,
        session: AsyncSession,
        test_user_id: UUID,
        test_conversation: Conversation,
    ):
        """Test retrieving existing conversation by ID."""
        # Act
        conversation = await get_or_create_conversation(
            session, test_user_id, conversation_id=test_conversation.id
        )

        # Assert
        assert conversation.id == test_conversation.id
        assert conversation.user_id == test_user_id

    @pytest.mark.asyncio
    async def test_raise_404_when_conversation_not_found(
        self, session: AsyncSession, test_user_id: UUID
    ):
        """Test that 404 is raised when conversation doesn't exist."""
        # Arrange
        non_existent_id = uuid4()

        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_or_create_conversation(
                session, test_user_id, conversation_id=non_existent_id
            )

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_raise_404_when_conversation_belongs_to_other_user(
        self,
        session: AsyncSession,
        test_conversation: Conversation,
        other_user_id: UUID,
    ):
        """Test that 404 is raised when trying to access another user's conversation."""
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await get_or_create_conversation(
                session, other_user_id, conversation_id=test_conversation.id
            )

        assert exc_info.value.status_code == 404
        # Security: Don't reveal conversation exists
        assert "not found" in exc_info.value.detail.lower()


class TestFetchConversationHistory:
    """Tests for fetch_conversation_history function."""

    @pytest.mark.asyncio
    async def test_fetch_empty_conversation_history(
        self, session: AsyncSession, test_conversation: Conversation
    ):
        """Test fetching history from conversation with no messages."""
        # Act
        messages = await fetch_conversation_history(
            session, test_conversation.id, limit=50
        )

        # Assert
        assert messages == []
        assert isinstance(messages, list)

    @pytest.mark.asyncio
    async def test_fetch_messages_in_chronological_order(
        self,
        session: AsyncSession,
        test_conversation: Conversation,
        test_user_id: UUID,
    ):
        """Test that messages are returned in chronological order."""
        # Arrange - Create messages in specific order
        msg1 = Message(
            conversation_id=test_conversation.id,
            user_id=test_user_id,
            role="user",
            content="First message"
        )
        msg2 = Message(
            conversation_id=test_conversation.id,
            user_id=test_user_id,
            role="assistant",
            content="Second message"
        )
        msg3 = Message(
            conversation_id=test_conversation.id,
            user_id=test_user_id,
            role="user",
            content="Third message"
        )
        session.add(msg1)
        session.add(msg2)
        session.add(msg3)
        await session.commit()

        # Act
        messages = await fetch_conversation_history(
            session, test_conversation.id, limit=50
        )

        # Assert
        assert len(messages) == 3
        assert messages[0].content == "First message"
        assert messages[1].content == "Second message"
        assert messages[2].content == "Third message"

    @pytest.mark.asyncio
    async def test_respect_limit_parameter(
        self,
        session: AsyncSession,
        test_conversation: Conversation,
        test_user_id: UUID,
    ):
        """Test that limit parameter restricts number of messages returned."""
        # Arrange - Create 10 messages
        for i in range(10):
            msg = Message(
                conversation_id=test_conversation.id,
                user_id=test_user_id,
                role="user",
                content=f"Message {i}"
            )
            session.add(msg)
        await session.commit()

        # Act - Request only 5 messages
        messages = await fetch_conversation_history(
            session, test_conversation.id, limit=5
        )

        # Assert
        assert len(messages) == 5

    @pytest.mark.asyncio
    async def test_raise_400_for_invalid_limit(
        self, session: AsyncSession, test_conversation: Conversation
    ):
        """Test that 400 is raised for invalid limit values."""
        # Act & Assert - Negative limit
        with pytest.raises(HTTPException) as exc_info:
            await fetch_conversation_history(session, test_conversation.id, limit=-1)

        assert exc_info.value.status_code == 400
        assert "positive integer" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_raise_value_error_for_limit_too_large(
        self, session: AsyncSession, test_conversation: Conversation
    ):
        """Test that ValueError is raised for limit exceeding maximum."""
        # Act & Assert
        with pytest.raises(ValueError, match="cannot exceed 1000"):
            await fetch_conversation_history(
                session, test_conversation.id, limit=1001
            )
