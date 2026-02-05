# Data Model: Todo AI Chatbot

**Feature**: 001-todo-ai-chatbot
**Phase**: 1 (Design & Contracts)
**Date**: 2026-01-31

## Overview

This document defines the complete data model for the Todo AI Chatbot feature, including all entities, relationships, validation rules, and state transitions.

## Entity Relationship Diagram

```
┌─────────────┐
│    User     │
│  (external) │
└──────┬──────┘
       │
       │ 1:N
       ├──────────────────────────────────────────────┐
       │                                              │
       ▼                                              ▼
┌─────────────┐                              ┌─────────────┐
│    Task     │                              │Conversation │
└─────────────┘                              └──────┬──────┘
                                                    │ 1:N
                                                    │
                                                    ▼
                                             ┌─────────────┐
                                             │  Message    │
                                             └─────────────┘
```

## Entity Definitions

### User

**Note**: Users are managed by Better Auth authentication system. This entity is referenced but not defined in this feature.

**Attributes**:
- `id`: UUID (primary key)
- `email`: string
- `name`: string
- Metadata managed by Better Auth

**Relationships**:
- One-to-many with Task (via `user_id`)
- One-to-many with Conversation (via `user_id`)

---

### Task

**Purpose**: Represents a todo item with title, optional description, and completion status.

**SQLModel Definition**:
```python
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional
from uuid import UUID

class TaskBase(SQLModel):
    title: str = Field(max_length=500, description="Task title")
    description: Optional[str] = Field(default=None, description="Detailed description")
    completed: bool = Field(default=False, description="Completion status")

class Task(TaskBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: "User" = Relationship(back_populates="tasks")
```

**Fields**:
- `id`: Integer, auto-increment, primary key
- `user_id`: UUID, foreign key to users table, indexed
- `title`: String, max 500 characters, required
- `description`: Text, optional
- `completed`: Boolean, default False
- `created_at`: Timestamp, auto-generated on creation
- `updated_at`: Timestamp, auto-updated on modification

**Validation Rules**:
- `title` must be non-empty and <= 500 characters
- `user_id` must be valid UUID referencing existing user
- `completed` must be boolean
- `created_at` <= `updated_at` (temporal integrity)

**Indexes**:
- Primary key: `id`
- Foreign key index: `user_id`
- Composite index: `(user_id, completed)` for filtering pending/completed tasks

**State Transitions**:
```
┌─────────┐  complete_task()  ┌──────────────┐
│ Pending │ ──────────────────> │  Completed   │
└─────────┘                    └──────────────┘
    ▲                                │
    │                                │
    └────────────────────────────────┘
             Reopen (optional - not in MVP)
```

**Cascade Behavior**:
- `ON DELETE CASCADE`: When user deleted, all their tasks are deleted

---

### Conversation

**Purpose**: Represents a chat session between a user and the AI assistant.

**SQLModel Definition**:
```python
class Conversation(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    user: "User" = Relationship(back_populates="conversations")
    messages: List["Message"] = Relationship(back_populates="conversation")
```

**Fields**:
- `id`: UUID, auto-generated, primary key
- `user_id`: UUID, foreign key to users table, indexed
- `created_at`: Timestamp, auto-generated on creation
- `updated_at`: Timestamp, auto-updated on each new message

**Validation Rules**:
- `user_id` must be valid UUID referencing existing user
- `created_at` <= `updated_at` (temporal integrity)

**Indexes**:
- Primary key: `id`
- Foreign key index: `user_id`
- Timestamp index: `updated_at DESC` for listing recent conversations

**State Transitions**:
None - conversation is immutable container for messages, only `updated_at` changes

**Cascade Behavior**:
- `ON DELETE CASCADE`: When user deleted, all their conversations (and messages) are deleted
- `ON DELETE CASCADE`: When conversation deleted, all its messages are deleted

---

### Message

**Purpose**: Represents a single message exchange in a conversation.

**SQLModel Definition**:
```python
class Message(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    conversation_id: UUID = Field(foreign_key="conversations.id", index=True)
    user_id: UUID = Field(foreign_key="users.id")
    role: str = Field(index=True)  # "user" or "assistant"
    content: str = Field(description="Message text content")
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    conversation: Conversation = Relationship(back_populates="messages")
    user: "User" = Relationship(back_populates="messages")
```

**Fields**:
- `id`: UUID, auto-generated, primary key
- `conversation_id`: UUID, foreign key to conversations table, indexed
- `user_id`: UUID, foreign key to users table
- `role`: String, enum ("user" | "assistant"), indexed
- `content`: Text, required, message content
- `created_at`: Timestamp, auto-generated on creation

**Validation Rules**:
- `conversation_id` must be valid UUID referencing existing conversation
- `user_id` must be valid UUID referencing existing user
- `role` must be exactly "user" or "assistant"
- `content` must be non-empty string
- Message `user_id` must match conversation `user_id` (data isolation constraint)

**Indexes**:
- Primary key: `id`
- Foreign key index: `conversation_id`
- Role index: `role`
- Timestamp index: `created_at DESC` for chronological ordering

**State Transitions**:
None - messages are immutable once created

**Cascade Behavior**:
- `ON DELETE CASCADE`: When conversation deleted, all its messages are deleted

---

## Database Schema (SQL)

### Create Tables

```sql
-- Tasks table (may already exist from previous phases)
CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT fk_user
        FOREIGN KEY(user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);

-- Conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT fk_user_conversation
        FOREIGN KEY(user_id)
        REFERENCES users(id)
        ON DELETE CASCADE
);

-- Messages table
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL,
    user_id UUID NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT fk_conversation
        FOREIGN KEY(conversation_id)
        REFERENCES conversations(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_user_message
        FOREIGN KEY(user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,
    CONSTRAINT chk_role CHECK (role IN ('user', 'assistant'))
);
```

### Create Indexes

```sql
-- Task indexes
CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_tasks_user_completed ON tasks(user_id, completed);

-- Conversation indexes
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_updated_at ON conversations(updated_at DESC);

-- Message indexes
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_role ON messages(role);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at DESC);
```

---

## Pydantic Models for API

### Request Models

```python
from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional

class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    conversation_id: Optional[UUID] = Field(
        default=None,
        description="Existing conversation ID (null for new conversation)"
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="User message content"
    )

class TaskCreateRequest(BaseModel):
    """Request model for creating a task"""
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = Field(default=None)

class TaskUpdateRequest(BaseModel):
    """Request model for updating a task"""
    title: Optional[str] = Field(default=None, min_length=1, max_length=500)
    description: Optional[str] = Field(default=None)
```

### Response Models

```python
class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    conversation_id: UUID
    response: str
    tool_calls: List[dict] = Field(default_factory=list)

class TaskResponse(BaseModel):
    """Response model for task operations"""
    id: int
    user_id: UUID
    title: str
    description: Optional[str]
    completed: bool
    created_at: datetime
    updated_at: datetime

class MessageResponse(BaseModel):
    """Response model for message data"""
    id: UUID
    conversation_id: UUID
    user_id: UUID
    role: str
    content: str
    created_at: datetime
```

---

## Data Integrity Rules

### User Isolation

**Rule**: All queries MUST include `user_id` filter to ensure data isolation.

```python
# Good: User-scoped query
SELECT * FROM tasks WHERE user_id = ? AND completed = false

# Bad: Returns tasks for all users
SELECT * FROM tasks WHERE completed = false
```

### Temporal Integrity

**Rule**: `created_at` timestamp must never be after `updated_at` timestamp.

### Cascade Deletion

**Rule**: When a user is deleted:
1. All their tasks are deleted
2. All their conversations are deleted
3. All messages in those conversations are deleted

### Role Validation

**Rule**: Message role must be exactly "user" or "assistant" (case-sensitive).

---

## Migration Strategy

### Alembic Migration

```python
# alembic/versions/001_create_conversation_tables.py

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # Create conversations table
    op.create_table(
        'conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='cascade'),
    )

    # Create messages table
    op.create_table(
        'messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=False),
        sa.CheckConstraint("role IN ('user', 'assistant')", name='chk_role'),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='cascade'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='cascade'),
    )

    # Create indexes
    op.create_index('idx_conversations_user_id', 'conversations', ['user_id'])
    op.create_index('idx_conversations_updated_at', 'conversations', [sa.text('updated_at DESC')])
    op.create_index('idx_messages_conversation_id', 'messages', ['conversation_id'])
    op.create_index('idx_messages_role', 'messages', ['role'])
    op.create_index('idx_messages_created_at', 'messages', [sa.text('created_at DESC')])

def downgrade():
    op.drop_table('messages')
    op.drop_table('conversations')
```

---

## Testing Considerations

### Unit Tests
- Model validation (required fields, length constraints, enum values)
- Relationship integrity (foreign key constraints)
- Cascade behavior (delete user → verify conversations/messages deleted)

### Integration Tests
- Insert and retrieve tasks
- Create conversation and add messages
- Verify user isolation (query with wrong user_id returns empty)
- Test transaction rollback on constraint violations

---

## Performance Considerations

### Query Optimization
- All user-scoped queries use indexed `user_id` column
- Composite index on `(user_id, completed)` for common filter
- Chronological queries use `created_at DESC` index

### Data Volume
- **Tasks**: Up to 1,000 per user (indexed lookups remain fast)
- **Messages**: Up to 500 per conversation (limit history to 50 for agent context)
- **Conversations**: No hard limit per user (users can archive old conversations)

### Connection Pooling
- Use SQLAlchemy connection pooling (default pool size=5, max overflow=10)
- Neon PostgreSQL handles connection pooling server-side
- Async database operations prevent blocking during agent inference

---

**Data Model Version**: 1.0.0 | **Last Updated**: 2026-01-31
