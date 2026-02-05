"""
Test suite for performance optimizations (T080-T082).

Tests database connection pooling, conversation pagination,
and response caching headers.
"""

import pytest
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from src.api.chat import (
    fetch_conversation_history,
    format_messages_for_agent,
    generate_etag,
)
from src.models import Message, Conversation, User
from fastapi import HTTPException


# ============================================================================
# T081: Conversation Pagination Tests
# ============================================================================

@pytest.mark.asyncio
async def test_fetch_conversation_history_default_limit(
    session: AsyncSession,
    test_user: User,
    test_conversation: Conversation
):
    """Test T081: Default limit of 50 messages."""
    # Create 100 messages
    for i in range(100):
        message = Message(
            conversation_id=test_conversation.id,
            user_id=test_user.id,
            role="user" if i % 2 == 0 else "assistant",
            content=f"Message {i}"
        )
        session.add(message)
    await session.commit()

    # Fetch with default limit (50)
    messages = await fetch_conversation_history(
        session, test_conversation.id
    )

    assert len(messages) == 50
    assert messages[0].content == "Message 0"
    assert messages[-1].content == "Message 49"


@pytest.mark.asyncio
async def test_fetch_conversation_history_with_offset(
    session: AsyncSession,
    test_user: User,
    test_conversation: Conversation
):
    """Test T081: Offset-based pagination."""
    # Create 100 messages
    for i in range(100):
        message = Message(
            conversation_id=test_conversation.id,
            user_id=test_user.id,
            role="user",
            content=f"Message {i}"
        )
        session.add(message)
    await session.commit()

    # Fetch first page
    page1 = await fetch_conversation_history(
        session, test_conversation.id, limit=50, offset=0
    )
    assert len(page1) == 50
    assert page1[0].content == "Message 0"

    # Fetch second page
    page2 = await fetch_conversation_history(
        session, test_conversation.id, limit=50, offset=50
    )
    assert len(page2) == 50
    assert page2[0].content == "Message 50"


@pytest.mark.asyncio
async def test_fetch_conversation_history_time_filtering(
    session: AsyncSession,
    test_user: User,
    test_conversation: Conversation
):
    """Test T081: Time-based filtering (before/after)."""
    now = datetime.utcnow()

    # Create messages at different times
    old_message = Message(
        conversation_id=test_conversation.id,
        user_id=test_user.id,
        role="user",
        content="Old message",
        created_at=now - timedelta(hours=2)
    )
    session.add(old_message)

    new_message = Message(
        conversation_id=test_conversation.id,
        user_id=test_user.id,
        role="user",
        content="New message",
        created_at=now - timedelta(minutes=5)
    )
    session.add(new_message)

    await session.commit()

    # Fetch messages after 1 hour ago
    one_hour_ago = now - timedelta(hours=1)
    messages = await fetch_conversation_history(
        session, test_conversation.id, after=one_hour_ago
    )

    assert len(messages) == 1
    assert messages[0].content == "New message"


@pytest.mark.asyncio
async def test_fetch_conversation_history_max_limit_enforcement(
    session: AsyncSession,
    test_conversation: Conversation
):
    """Test T081: Maximum limit of 1000 messages enforced."""
    with pytest.raises(ValueError, match="Limit cannot exceed 1000"):
        await fetch_conversation_history(
            session, test_conversation.id, limit=1001
        )


@pytest.mark.asyncio
async def test_fetch_conversation_history_invalid_offset(
    session: AsyncSession,
    test_conversation: Conversation
):
    """Test T081: Negative offset rejected."""
    with pytest.raises(HTTPException, match="Offset must be non-negative"):
        await fetch_conversation_history(
            session, test_conversation.id, offset=-1
        )


# ============================================================================
# T081: Message Formatting Tests
# ============================================================================

@pytest.mark.asyncio
async def test_format_messages_for_agent_paginated_data(
    session: AsyncSession,
    test_user: User,
    test_conversation: Conversation
):
    """Test T081: format_messages_for_agent handles paginated batches efficiently."""
    # Create a paginated batch of messages
    messages = []
    for i in range(50):
        msg = Message(
            conversation_id=test_conversation.id,
            user_id=test_user.id,
            role="user" if i % 2 == 0 else "assistant",
            content=f"Message {i}"
        )
        messages.append(msg)

    # Format for agent
    formatted = format_messages_for_agent(messages)

    assert len(formatted) == 50
    assert formatted[0] == {"role": "user", "content": "Message 0"}
    assert formatted[1] == {"role": "assistant", "content": "Message 1"}


def test_format_messages_for_agent_empty_list():
    """Test T081: Empty message list handled correctly."""
    formatted = format_messages_for_agent([])
    assert formatted == []


# ============================================================================
# T082: ETag Generation Tests
# ============================================================================

def test_generate_etag_basic():
    """Test T082: ETag generation for conversation state."""
    conv_id = uuid4()
    etag = generate_etag(conv_id, 42, datetime.utcnow())

    assert isinstance(etag, str)
    assert len(etag) == 64  # SHA256 hex string
    assert etag.isalnum()


def test_generate_etag_same_state_same_tag():
    """Test T082: Same conversation state produces same ETag."""
    conv_id = uuid4()
    timestamp = datetime.utcnow()

    etag1 = generate_etag(conv_id, 42, timestamp)
    etag2 = generate_etag(conv_id, 42, timestamp)

    assert etag1 == etag2


def test_generate_etag_different_state_different_tag():
    """Test T082: Different conversation state produces different ETag."""
    conv_id = uuid4()
    timestamp = datetime.utcnow()

    etag1 = generate_etag(conv_id, 42, timestamp)
    etag2 = generate_etag(conv_id, 43, timestamp)  # Different message count

    assert etag1 != etag2


def test_generate_etag_without_timestamp():
    """Test T082: ETag generation works without timestamp."""
    conv_id = uuid4()
    etag = generate_etag(conv_id, 42, None)

    assert isinstance(etag, str)
    assert len(etag) == 64


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.asyncio
async def test_pagination_integration_large_conversation(
    session: AsyncSession,
    test_user: User,
    test_conversation: Conversation
):
    """
    Integration test: T081 - Handle large conversations (100+ messages).
    Requirement: Test with large conversations (100+ messages).
    """
    # Create 150 messages
    for i in range(150):
        message = Message(
            conversation_id=test_conversation.id,
            user_id=test_user.id,
            role="user" if i % 2 == 0 else "assistant",
            content=f"Message {i}: " + "x" * 50  # 50 char content
        )
        session.add(message)
    await session.commit()

    # Fetch in pages of 50
    all_messages = []
    for offset in [0, 50, 100]:
        page = await fetch_conversation_history(
            session, test_conversation.id, limit=50, offset=offset
        )
        all_messages.extend(page)

    assert len(all_messages) == 150

    # Verify chronological order maintained
    for i, msg in enumerate(all_messages):
        assert msg.content == f"Message {i}: " + "x" * 50

    # Format for agent (should handle all 150 efficiently)
    formatted = format_messages_for_agent(all_messages)
    assert len(formatted) == 150
    assert formatted[0]["content"] == "Message 0: " + "x" * 50
    assert formatted[-1]["content"] == "Message 149: " + "x" * 50
