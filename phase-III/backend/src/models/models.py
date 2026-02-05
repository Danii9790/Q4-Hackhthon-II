"""
SQLModel database models for Todo AI Chatbot.

Defines all database entities using SQLModel ORM.
All models support automatic timestamp management and user data isolation.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

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


class User(SQLModel, table=True):
    """
    User model representing authenticated users.

    Attributes:
        id: Unique user identifier (UUID)
        email: User's email address (unique)
        created_at: Account creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "users"

    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(SQLUUID, primary_key=True),
        description="Unique user identifier"
    )
    email: str = Field(
        index=True,
        unique=True,
        max_length=255,
        description="User's email address (unique)"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, nullable=False),
        description="Account creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, nullable=False),
        description="Last update timestamp"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"


class Conversation(SQLModel, table=True):
    """
    Conversation model representing chat sessions.

    A conversation contains multiple messages and belongs to a specific user.
    Multiple conversations per user are supported for independent chat sessions.

    Attributes:
        id: Unique conversation identifier (UUID)
        user_id: Foreign key reference to user
        created_at: Conversation creation timestamp
        updated_at: Last message timestamp
    """

    __tablename__ = "conversations"

    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(SQLUUID, primary_key=True),
        description="Unique conversation identifier"
    )
    user_id: UUID = Field(
        sa_column=Column(SQLUUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        description="Foreign key reference to user"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, nullable=False),
        description="Conversation creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, nullable=False),
        description="Last update timestamp"
    )

    # Index for efficient user conversation queries
    __table_args__ = (
        Index("ix_conversation_user_id", "user_id"),
    )

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, user_id={self.user_id})>"


class Message(SQLModel, table=True):
    """
    Message model representing individual conversation messages.

    Messages can be from the user or the AI assistant.
    All messages are persisted to maintain conversation context.

    Attributes:
        id: Unique message identifier (UUID)
        conversation_id: Foreign key reference to conversation
        user_id: Foreign key reference to user (for data isolation)
        role: Message role ("user" or "assistant")
        content: Message text content
        created_at: Message creation timestamp
    """

    __tablename__ = "messages"

    id: UUID = Field(
        default_factory=uuid4,
        sa_column=Column(SQLUUID, primary_key=True),
        description="Unique message identifier"
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
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, nullable=False, index=True),
        description="Message creation timestamp"
    )

    # Indexes for efficient conversation history queries
    __table_args__ = (
        Index("ix_message_conversation_id", "conversation_id"),
        Index("ix_message_user_id", "user_id"),
        Index("ix_message_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"<Message(id={self.id}, role={self.role}, content={content_preview})>"


class Task(SQLModel, table=True):
    """
    Task model representing todo items.

    Tasks belong to specific users and can be created, viewed, completed,
    updated, and deleted through natural language interactions.

    Attributes:
        id: Unique task identifier (auto-incrementing integer)
        user_id: Foreign key reference to user (for data isolation)
        title: Task title (required)
        description: Optional detailed task description
        completed: Task completion status
        created_at: Task creation timestamp
        updated_at: Last update timestamp
    """

    __tablename__ = "tasks"

    id: Optional[int] = Field(
        default=None,
        primary_key=True,
        description="Unique task identifier (auto-incrementing)"
    )
    user_id: UUID = Field(
        sa_column=Column(SQLUUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        description="Foreign key reference to user (for data isolation)"
    )
    title: str = Field(
        max_length=500,
        sa_column=Column(Text, nullable=False),
        description="Task title (required)"
    )
    description: Optional[str] = Field(
        default=None,
        sa_column=Column(Text),
        description="Optional detailed task description"
    )
    completed: bool = Field(
        default=False,
        index=True,
        description="Task completion status"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, nullable=False),
        description="Task creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime, nullable=False),
        description="Last update timestamp"
    )

    # Indexes for efficient task queries
    __table_args__ = (
        Index("ix_task_user_id", "user_id"),
        Index("ix_task_completed", "completed"),
        Index("ix_task_user_completed", "user_id", "completed"),
    )

    def __repr__(self) -> str:
        status = "completed" if self.completed else "pending"
        return f"<Task(id={self.id}, title={self.title}, status={status})>"
