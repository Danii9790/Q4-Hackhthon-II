"""
Message model for Todo Application.

Stores individual messages within a conversation.
"""
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import String, JSON
from typing import TYPE_CHECKING, Optional, Dict, Any
import uuid
from enum import Enum

if TYPE_CHECKING:
    from .conversation import Conversation


class MessageRole(str, Enum):
    """Message role enumeration"""
    USER = "user"
    ASSISTANT = "assistant"


class Message(SQLModel, table=True):
    """
    Represents a single message in a conversation.

    Messages can be from the user or from the AI assistant. Assistant messages
    may include tool_calls showing which MCP tools were invoked during processing.

    Attributes:
        id: Unique message identifier (UUID)
        conversation_id: Foreign key to conversations table
        role: Message role (user or assistant)
        content: Message text content
        tool_calls: JSON data about MCP tools invoked (assistant messages only)
        created_at: Message creation timestamp
    """
    __tablename__ = "messages"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    conversation_id: str = Field(foreign_key="conversations.id", index=True)
    role: MessageRole = Field(default=MessageRole.USER)
    content: str = Field(default="")
    tool_calls: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="Tool invocations by assistant (add_task, list_tasks, etc.)"
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    conversation: "Conversation" = Relationship(back_populates="messages")

    def __repr__(self) -> str:
        """String representation of message"""
        return f"Message(id={self.id}, role={self.role}, content={self.content[:50]}...)"
