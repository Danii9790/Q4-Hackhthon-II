"""
Message model for Todo AI Chatbot.

Defines the message entity which represents individual conversation messages.
Messages can be from the user or the AI assistant.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import text
from sqlmodel import (
    Column,
    DateTime,
    Field,
    ForeignKey,
    Index,
    SQLModel,
    Text,
)
from sqlmodel import UUID as SQLUUID


class Message(SQLModel, table=True):
    """
    Message model representing individual conversation messages.

    Messages can be from the user or the AI assistant.
    All messages are persisted to maintain conversation context.

    Attributes:
        id: Unique message identifier (UUID, generated via gen_random_uuid())
        conversation_id: Foreign key reference to conversation (indexed)
        user_id: Foreign key reference to user (for data isolation)
        role: Message role ("user" or "assistant", indexed)
        content: Message text content (required)
        created_at: Message creation timestamp
    """

    __tablename__ = "messages"

    id: UUID = Field(
        default=None,
        sa_column=Column(
            SQLUUID,
            primary_key=True,
            server_default=text("gen_random_uuid()"),
        ),
        description="Unique message identifier (UUID, PostgreSQL-generated)"
    )
    conversation_id: UUID = Field(
        sa_column=Column(SQLUUID, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True),
        description="Foreign key reference to conversation"
    )
    user_id: UUID = Field(
        sa_column=Column(SQLUUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        description="Foreign key reference to user (for data isolation)"
    )
    role: str = Field(
        max_length=20,
        index=True,
        description="Message role ('user' or 'assistant')"
    )
    content: str = Field(
        sa_column=Column(Text, nullable=False),
        description="Message text content"
    )
    created_at: datetime = Field(
        default=None,
        sa_column=Column(DateTime, nullable=False, server_default=text("now()")),
        description="Message creation timestamp"
    )

    # Indexes for efficient conversation history queries
    __table_args__ = (
        Index("ix_message_conversation_id", "conversation_id"),
        Index("ix_message_user_id", "user_id"),
        Index("ix_message_role", "role"),
    )

    def __repr__(self) -> str:
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"<Message(id={self.id}, role={self.role}, content={content_preview})>"
