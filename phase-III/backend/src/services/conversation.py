"""
Conversation Service for Todo AI Chatbot.

This service manages conversation state, including history retrieval
and message persistence for the stateless chat system.
"""
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select

from src.models.conversation import Conversation
from src.models.message import Message, MessageRole
from src.models.user import User
from src.db.session import get_session


def get_or_create_conversation(
    user_id: str,
    session: Session
) -> Conversation:
    """
    Get existing conversation for user or create a new one.

    Args:
        user_id: User UUID
        session: Database session

    Returns:
        Conversation object (existing or newly created)
    """
    # Try to get existing conversation
    stmt = select(Conversation).where(Conversation.user_id == user_id)
    conversation = session.execute(stmt).scalar_one_or_none()

    # If no conversation exists, create one
    if not conversation:
        now = datetime.now(timezone.utc)
        conversation = Conversation(
            id=user_id,  # Use user_id as conversation_id for simplicity
            user_id=user_id,
            created_at=now,
            updated_at=now
        )
        session.add(conversation)
        session.commit()
        session.refresh(conversation)

    return conversation


def fetch_conversation_history(
    user_id: str,
    session: Session,
    limit: Optional[int] = None,
    offset: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Fetch conversation history for a user from database.

    Args:
        user_id: User UUID (also serves as conversation_id)
        session: Database session
        limit: Optional limit on number of messages (for pagination)
        offset: Optional offset for pagination (number of messages to skip)

    Returns:
        List of message dictionaries with role, content, tool_calls, created_at
        Example: [
            {
                "role": "user",
                "content": "Add task buy groceries",
                "tool_calls": None,
                "created_at": "2026-02-06T12:00:00"
            },
            {
                "role": "assistant",
                "content": "I've added 'Buy groceries' to your tasks.",
                "tool_calls": [...],
                "created_at": "2026-02-06T12:00:01"
            }
        ]
    """
    # Get conversation
    conversation = get_or_create_conversation(user_id, session)

    # Fetch messages in chronological order (oldest first)
    # Composite index on (conversation_id, created_at) ensures fast queries
    stmt = select(Message).where(
        Message.conversation_id == conversation.id
    ).order_by(Message.created_at.asc())

    if limit:
        stmt = stmt.limit(limit)

    if offset:
        stmt = stmt.offset(offset)

    messages = session.execute(stmt).scalars().all()

    # Format messages for agent
    formatted_messages = []
    for msg in messages:
        formatted_messages.append({
            "role": msg.role.value,
            "content": msg.content,
            "tool_calls": msg.tool_calls,
            "created_at": msg.created_at.isoformat()
        })

    return formatted_messages


def store_message(
    user_id: str,
    role: MessageRole,
    content: str,
    tool_calls: Optional[List[Dict[str, Any]]] = None,
    session: Optional[Session] = None
) -> Message:
    """
    Store a message in the database with transaction wrapper.

    Args:
        user_id: User UUID (also serves as conversation_id)
        role: Message role (user or assistant)
        content: Message content
        tool_calls: Optional tool call data (for assistant messages)
        session: Database session (if None, creates new session)

    Returns:
        Created Message object
    """
    # Get or create session if not provided
    close_session = False
    if session is None:
        for session in get_session():
            close_session = True
            break

    try:
        # Get conversation
        conversation = get_or_create_conversation(user_id, session)

        # Create message
        now = datetime.now(timezone.utc)
        message = Message(
            conversation_id=conversation.id,
            role=role,
            content=content,
            tool_calls=tool_calls,
            created_at=now
        )

        session.add(message)

        # Update conversation updated_at timestamp
        conversation.updated_at = now

        session.commit()
        session.refresh(message)

        return message

    except Exception as e:
        session.rollback()
        raise e

    finally:
        if close_session:
            session.close()


def update_conversation_timestamp(
    user_id: str,
    session: Session
) -> None:
    """
    Update the conversation's updated_at timestamp.

    Args:
        user_id: User UUID (also serves as conversation_id)
        session: Database session
    """
    conversation = get_or_create_conversation(user_id, session)
    conversation.updated_at = datetime.now(timezone.utc)
    session.commit()
