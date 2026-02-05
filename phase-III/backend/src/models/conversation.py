"""
Conversation model for Todo AI Chatbot.

Defines the conversation entity which represents chat sessions.
A conversation contains multiple messages and belongs to a specific user.
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
)
from sqlmodel import UUID as SQLUUID


class Conversation(SQLModel, table=True):
    """
    Conversation model representing chat sessions.

    A conversation contains multiple messages and belongs to a specific user.
    Multiple conversations per user are supported for independent chat sessions.

    Attributes:
        id: Unique conversation identifier (UUID, generated via gen_random_uuid())
        user_id: Foreign key reference to user (indexed)
        created_at: Conversation creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "conversations"

    id: UUID = Field(
        default=None,
        sa_column=Column(
            SQLUUID,
            primary_key=True,
            server_default=text("gen_random_uuid()"),
        ),
        description="Unique conversation identifier (UUID, PostgreSQL-generated)"
    )
    user_id: UUID = Field(
        sa_column=Column(SQLUUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        description="Foreign key reference to user"
    )
    created_at: datetime = Field(
        default=None,
        sa_column=Column(DateTime, nullable=False, server_default=text("now()")),
        description="Conversation creation timestamp"
    )
    updated_at: datetime = Field(
        default=None,
        sa_column=Column(DateTime, nullable=False, server_default=text("now()")),
        description="Last update timestamp"
    )

    # Index for efficient user conversation queries
    __table_args__ = (
        Index("ix_conversation_user_id", "user_id"),
    )

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, user_id={self.user_id})>"
