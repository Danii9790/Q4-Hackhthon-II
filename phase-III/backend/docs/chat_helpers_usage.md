# Chat Helper Functions - Usage Guide

This document demonstrates how to use the conversation management helper functions in `/home/xdev/Hackhthon-II/phase-III/backend/src/api/chat.py`.

## Overview

The chat helper functions provide:
1. **Conversation retrieval/creation** - `get_or_create_conversation()`
2. **Message history fetching** - `fetch_conversation_history()`

Both functions enforce user data isolation and follow async patterns.

---

## Function: `get_or_create_conversation`

### Purpose
Retrieves an existing conversation or creates a new one for the authenticated user.

### Signature
```python
async def get_or_create_conversation(
    session: AsyncSession,
    user_id: UUID,
    conversation_id: Optional[UUID] = None,
) -> Conversation
```

### Parameters
- `session` (AsyncSession): Database session from FastAPI dependency
- `user_id` (UUID): Authenticated user's ID from JWT token
- `conversation_id` (Optional[UUID]): Conversation UUID to retrieve, or None to create new

### Returns
- `Conversation`: The retrieved or newly created conversation object

### Raises
- `HTTPException 404`: If conversation_id not found or doesn't belong to user

### Usage Examples

#### Example 1: Start a New Conversation
```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from src.api.chat import get_or_create_conversation
from src.api.deps import get_current_user_id
from src.db.session import get_session

@router.post("/api/chat/start")
async def start_conversation(
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    # Create new conversation (conversation_id is None)
    conversation = await get_or_create_conversation(
        session=session,
        user_id=user_id,
        conversation_id=None  # Explicit None for clarity
    )

    await session.commit()

    return {
        "conversation_id": str(conversation.id),
        "created_at": conversation.created_at
    }
```

#### Example 2: Continue Existing Conversation
```python
@router.post("/api/chat/message")
async def send_message(
    conversation_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    # Retrieve existing conversation
    conversation = await get_or_create_conversation(
        session=session,
        user_id=user_id,
        conversation_id=conversation_id
    )

    # Security: Ownership validated automatically
    # Proceed with message processing...

    return {"conversation_id": str(conversation.id)}
```

#### Example 3: Optional Conversation ID
```python
from typing import Optional
from pydantic import BaseModel

class ChatRequest(BaseModel):
    conversation_id: Optional[UUID] = None
    message: str

@router.post("/api/chat")
async def chat(
    request: ChatRequest,
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    # Create new if conversation_id not provided, otherwise continue existing
    conversation = await get_or_create_conversation(
        session=session,
        user_id=user_id,
        conversation_id=request.conversation_id
    )

    # Process message...
    return {"conversation_id": str(conversation.id)}
```

---

## Function: `fetch_conversation_history`

### Purpose
Retrieves conversation messages in chronological order for context building.

### Signature
```python
async def fetch_conversation_history(
    session: AsyncSession,
    conversation_id: UUID,
    limit: int = 50,
) -> List[Message]
```

### Parameters
- `session` (AsyncSession): Database session from FastAPI dependency
- `conversation_id` (UUID): Conversation to fetch messages from
- `limit` (int): Maximum messages to retrieve (default: 50, max: 1000)

### Returns
- `List[Message]`: Messages ordered by `created_at` (oldest first)

### Raises
- `HTTPException 400`: If limit is not a positive integer
- `ValueError`: If limit exceeds 1000

### Usage Examples

#### Example 1: Fetch Default History (50 messages)
```python
@router.get("/api/chat/{conversation_id}/history")
async def get_history(
    conversation_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    # Validate conversation ownership first
    conversation = await get_or_create_conversation(
        session, user_id, conversation_id
    )

    # Fetch message history
    messages = await fetch_conversation_history(
        session=session,
        conversation_id=conversation_id,
        limit=50  # Default
    )

    return {
        "conversation_id": str(conversation_id),
        "message_count": len(messages),
        "messages": [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
    }
```

#### Example 2: Fetch Limited History for Context Window
```python
from openai import AsyncOpenAI

client = AsyncOpenAI()

@router.post("/api/chat/{conversation_id}")
async def chat_with_ai(
    conversation_id: UUID,
    user_message: str,
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    # Validate conversation
    conversation = await get_or_create_conversation(
        session, user_id, conversation_id
    )

    # Fetch recent history (last 10 messages for context)
    messages = await fetch_conversation_history(
        session=session,
        conversation_id=conversation_id,
        limit=10
    )

    # Build OpenAI messages array
    openai_messages = [
        {"role": msg.role, "content": msg.content}
        for msg in messages
    ]
    openai_messages.append({"role": "user", "content": user_message})

    # Call OpenAI API
    response = await client.chat.completions.create(
        model="gpt-4",
        messages=openai_messages
    )

    return {"response": response.choices[0].message.content}
```

#### Example 3: Full Conversation History
```python
@router.get("/api/chat/{conversation_id}/full")
async def get_full_history(
    conversation_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    # Validate conversation
    conversation = await get_or_create_conversation(
        session, user_id, conversation_id
    )

    # Fetch up to 1000 messages (practical maximum)
    messages = await fetch_conversation_history(
        session=session,
        conversation_id=conversation_id,
        limit=1000
    )

    return {
        "conversation_id": str(conversation_id),
        "total_messages": len(messages),
        "created_at": conversation.created_at,
        "messages": messages
    }
```

---

## Complete Chat Endpoint Example

Here's a complete example showing both functions working together:

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID, Optional
from pydantic import BaseModel

from src.api.chat import (
    get_or_create_conversation,
    fetch_conversation_history,
)
from src.api.deps import get_current_user_id
from src.db.session import get_session
from src.models import Message

router = APIRouter()

class ChatRequest(BaseModel):
    conversation_id: Optional[UUID] = None
    message: str

class ChatResponse(BaseModel):
    conversation_id: UUID
    response: str

@router.post("/api/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    """
    Send a message and receive AI response.

    - If conversation_id provided: continue existing conversation
    - If conversation_id omitted: start new conversation
    """
    # Step 1: Get or create conversation
    conversation = await get_or_create_conversation(
        session=session,
        user_id=user_id,
        conversation_id=request.conversation_id
    )

    # Step 2: Fetch conversation history for context
    history = await fetch_conversation_history(
        session=session,
        conversation_id=conversation.id,
        limit=50  # Last 50 messages for context
    )

    # Step 3: Save user message to database
    user_message = Message(
        conversation_id=conversation.id,
        user_id=user_id,
        role="user",
        content=request.message
    )
    session.add(user_message)
    await session.commit()

    # Step 4: Build context for AI (in real implementation)
    # messages_for_ai = [{"role": m.role, "content": m.content} for m in history]
    # ai_response = await call_ai_agent(messages_for_ai + [{"role": "user", "content": request.message}])

    # Step 5: Save AI response to database
    ai_response = Message(
        conversation_id=conversation.id,
        user_id=user_id,
        role="assistant",
        content="This is a placeholder AI response"
    )
    session.add(ai_response)
    await session.commit()

    return ChatResponse(
        conversation_id=conversation.id,
        response=ai_response.content
    )
```

---

## Security Considerations

### User Data Isolation
- `get_or_create_conversation()` validates that conversation belongs to user
- Returns 404 (not 403) to prevent conversation enumeration
- All database queries scoped by `user_id`

### Error Messages
- Generic "not found" for both missing and unauthorized conversations
- Prevents information leakage about conversation existence

### Limit Enforcement
- `fetch_conversation_history()` enforces maximum of 1000 messages
- Prevents memory exhaustion from very long conversations

---

## Performance Notes

### Database Queries
- **`get_or_create_conversation()`**: Single SELECT query for retrieval, INSERT for new
- **`fetch_conversation_history()`**: Single SELECT with ORDER BY and LIMIT
- Both use indexed columns (`conversation_id`, `user_id`)

### Optimization Tips
1. **Use appropriate limit values**: Default 50 is good for most use cases
2. **Avoid fetching entire history**: Use limit to reduce memory usage
3. **Index utilization**: Both functions leverage existing database indexes

### Expected Performance
- Conversation retrieval: <50ms p95
- History fetch (50 messages): <100ms p95
- History fetch (1000 messages): <500ms p95

---

## Testing

See `/home/xdev/Hackhthon-II/phase-III/backend/tests/test_chat_helpers.py` for comprehensive test coverage.

Run tests:
```bash
cd /home/xdev/Hackhthon-II/phase-III/backend
pytest tests/test_chat_helpers.py -v
```

---

## Files Modified/Created

**Created:**
- `/home/xdev/Hackhthon-II/phase-III/backend/src/api/chat.py` - Helper functions implementation
- `/home/xdev/Hackhthon-II/phase-III/backend/tests/test_chat_helpers.py` - Unit tests
- `/home/xdev/Hackhthon-II/phase-III/backend/docs/chat_helpers_usage.md` - This usage guide

**Modified:**
- `/home/xdev/Hackhthon-II/phase-III/backend/src/api/__init__.py` - Added exports

---

## Next Steps

1. **Integration**: Use these helpers in the main chat endpoint
2. **AI Agent Integration**: Pass conversation history to OpenAI Agents SDK
3. **Error Handling**: Add custom exception classes for domain-specific errors
4. **Logging**: Add structured logging for monitoring conversation operations
5. **Performance**: Add caching for frequently accessed conversations
