"""
Conversation helper functions for Todo AI Chatbot.

Provides shared utilities for conversation history management used by
both the chat API and agent service. This module breaks circular import
dependencies between src.api.chat and src.services.agent.

Functions:
- fetch_conversation_history: Paginated message retrieval from database
- format_messages_for_agent: Convert Message objects to OpenAI format
- truncate_history_to_max: Token-aware conversation truncation
"""

from datetime import datetime
from logging import getLogger
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel import select as sqlmodel_select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Message


# Configure logging
logger = getLogger(__name__)


async def fetch_conversation_history(
    session: AsyncSession,
    conversation_id: UUID,
    limit: int = 50,
    offset: int = 0,
    before: Optional[datetime] = None,
    after: Optional[datetime] = None,
) -> List[Message]:
    """
    Fetch conversation message history from database with pagination.

    Performance: T081 - Pagination support for large conversations.
    Retrieves messages for the specified conversation in chronological order.
    Supports both offset-based pagination and time-based filtering.

    Args:
        session: Async database session
        conversation_id: UUID of conversation to fetch messages for
        limit: Maximum number of messages to retrieve (default: 50, max: 1000)
        offset: Number of messages to skip from beginning (default: 0)
        before: Optional datetime filter - only messages before this time
        after: Optional datetime filter - only messages after this time

    Returns:
        List of Message objects ordered by created_at (oldest first)

    Raises:
        HTTPException: 400 if limit/offset is invalid
        ValueError: If limit exceeds maximum allowed (1000)

    Examples:
        # Fetch first 50 messages (default)
        messages = await fetch_conversation_history(session, conv_id)

        # Fetch next 50 messages (pagination)
        messages = await fetch_conversation_history(session, conv_id, limit=50, offset=50)

        # Fetch messages from last hour (time-based)
        from datetime import datetime, timedelta
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        messages = await fetch_conversation_history(session, conv_id, after=one_hour_ago)

        # Combined: fetch messages before a certain time with pagination
        messages = await fetch_conversation_history(
            session, conv_id, limit=100, offset=0, before=timestamp
        )
    """
    # Validate limit parameter (T081: Default 50, Max 1000)
    DEFAULT_LIMIT = 50
    MAX_LIMIT = 1000

    if limit <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit must be a positive integer"
        )

    if limit > MAX_LIMIT:
        raise ValueError(f"Limit cannot exceed {MAX_LIMIT} messages")

    if offset < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Offset must be a non-negative integer"
        )

    # Build base query with conversation filter
    statement = (
        sqlmodel_select(Message)
        .where(Message.conversation_id == conversation_id)
    )

    # Apply time-based filters if provided (T081: Time range support)
    if before is not None:
        statement = statement.where(Message.created_at < before)

    if after is not None:
        statement = statement.where(Message.created_at > after)

    # Apply ordering and pagination (T081: Offset-based pagination)
    statement = (
        statement
        .order_by(Message.created_at.asc())
        .limit(limit)
        .offset(offset)
    )

    result = await session.execute(statement)
    messages = list(result.scalars().all())

    logger.debug(
        f"Fetch conversation history: conversation_id={conversation_id}, "
        f"messages_returned={len(messages)}, limit={limit}, offset={offset}"
    )

    return messages


def format_messages_for_agent(messages: List[Message]) -> List[dict]:
    """
    Convert list of Message objects to OpenAI format for agent input.

    Performance: T081 - Optimized to handle paginated message batches efficiently.
    Transforms database Message objects into the format expected by OpenAI
    Agents SDK: [{"role": "user"|"assistant", "content": "..."}].

    Preserves chronological order (oldest to newest) as returned from database.
    Handles empty message lists gracefully by returning empty list.
    Compatible with paginated data from fetch_conversation_history.

    Args:
        messages: List of Message objects from database query.
                  Messages should be ordered by created_at ASC.
                  Can be a paginated subset of full conversation history.

    Returns:
        List of dictionaries in OpenAI message format:
        [
            {"role": "user", "content": "first message"},
            {"role": "assistant", "content": "response"},
            {"role": "user", "content": "follow up"}
        ]

    Performance Notes (T081):
        - Efficient for large conversations when used with pagination
        - No additional database queries
        - O(n) time complexity where n = number of messages in batch
        - Memory efficient: only processes requested message batch

    Examples:
        >>> messages = [Message(role="user", content="Hello"), Message(role="assistant", content="Hi there")]
        >>> format_messages_for_agent(messages)
        [{'role': 'user', 'content': 'Hello'}, {'role': 'assistant', 'content': 'Hi there'}]

        >>> format_messages_for_agent([])
        []

        >>> # Works with paginated data
        >>> batch = await fetch_conversation_history(session, conv_id, limit=50, offset=0)
        >>> formatted = format_messages_for_agent(batch)
    """
    # Handle empty list
    if not messages:
        return []

    # Convert each message to OpenAI format (efficient iteration)
    formatted = [
        {
            "role": message.role,
            "content": message.content
        }
        for message in messages
    ]

    return formatted


def truncate_history_to_max(messages: List[dict], max_tokens: int = 8000) -> List[dict]:
    """
    Truncate conversation history to fit within token limit.

    Implements simple truncation strategy:
    - Removes oldest messages first (keeps most recent context)
    - Always keeps at least the 10 most recent messages (minimum context window)
    - Uses approximate character count (assumes ~4 characters per token)

    This is a basic implementation; production systems might use more
    sophisticated tokenization (e.g., tiktoken) for precise counting.

    Args:
        messages: List of formatted message dictionaries (from format_messages_for_agent)
        max_tokens: Maximum tokens allowed (default: 8000 for typical context windows)

    Returns:
        Truncated list of messages within token limit, preserving chronological order.
        Always returns at least the 10 most recent messages if available.

    Examples:
        >>> messages = [{"role": "user", "content": "A" * 1000}] * 50  # 50k characters
        >>> truncated = truncate_history_to_max(messages, max_tokens=2000)
        >>> len(truncated)  # Keeps most recent messages to fit ~8000 chars
        8

        >>> # Keeps minimum 10 messages even if slightly over limit
        >>> short_messages = [{"role": "user", "content": "Hi"}] * 15
        >>> truncate_history_to_max(short_messages, max_tokens=10)
        15  # All 15 kept (minimum guarantee)
    """
    # Handle empty list
    if not messages:
        return []

    # Ensure we keep at least 10 most recent messages (minimum context)
    MINIMUM_MESSAGES = 10
    if len(messages) <= MINIMUM_MESSAGES:
        return messages

    # Approximate token limit in characters (~4 chars per token)
    max_chars = max_tokens * 4

    # Start from the end (most recent) and work backwards
    total_chars = 0
    truncated_indices = []

    for i in range(len(messages) - 1, -1, -1):
        message = messages[i]
        content_length = len(message.get("content", ""))

        # Check if adding this message exceeds limit
        # (but always ensure we keep at least MINIMUM_MESSAGES)
        messages_kept = len(truncated_indices)
        if messages_kept >= MINIMUM_MESSAGES and total_chars + content_length > max_chars:
            # Would exceed limit and we have minimum - stop here
            break

        # Keep this message
        truncated_indices.append(i)
        total_chars += content_length

    # Reverse to restore chronological order and slice messages
    truncated_indices.reverse()
    return [messages[i] for i in truncated_indices]
