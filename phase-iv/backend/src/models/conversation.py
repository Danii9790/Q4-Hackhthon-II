"""
Conversation model for Todo Application.

Stores one ongoing conversation per user for chat interactions.
"""
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship
from typing import TYPE_CHECKING, Optional
import uuid

if TYPE_CHECKING:
    from .user import User
    from .message import Message


class Conversation(SQLModel, table=True):
    """
    Represents a chat conversation for a user.

    Each user has one ongoing conversation. All messages in the conversation
    are stored in the messages table with a foreign key to this model.

    Attributes:
        id: Unique conversation identifier (UUID)
        user_id: Foreign key to users table (owner of this conversation)
        created_at: Conversation creation timestamp
        updated_at: Last activity timestamp (message sent/received)
    """
    __tablename__ = "conversations"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="users.id", unique=True, index=True)  # One conversation per user
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationships
    user: "User" = Relationship(back_populates="conversation")
    messages: list["Message"] = Relationship(back_populates="conversation", cascade_delete=True)
