# Research Findings: Todo AI Chatbot

**Feature**: 001-todo-ai-chatbot
**Phase**: 0 (Research & Decisions)
**Date**: 2026-01-31

## Overview

This document consolidates research findings and technical decisions for implementing the Todo AI Chatbot feature. All research topics identified in the Technical Context section of plan.md have been investigated and decisions documented.

## Research Topic 1: OpenAI Agents SDK Integration

### Question: How to integrate OpenAI Agents SDK with FastAPI async endpoints?

**Decision**: Use `openai-agents-sdk` Python package with async runner pattern.

### Key Findings

**Integration Pattern**:
```python
# Async agent execution in FastAPI endpoint
from openai import AsyncOpenAI
from openai_agents_sdk import Agent, Runner

async def execute_agent(
    user_message: str,
    conversation_history: List[Message],
    tools: List[MCPTool]
) -> AgentResponse:
    # Build agent with tools
    agent = Agent(
        name="todo_assistant",
        instructions="You help users manage their todo tasks...",
        tools=tools
    )

    # Create runner with async client
    client = AsyncOpenAI()
    runner = Runner(agent, client=client)

    # Execute with conversation context
    response = await runner.run(
        user_message,
        context=conversation_history
    )

    return response
```

**Best Practices**:
1. **Tool Registration**: Register MCP tools before agent creation using `tool` decorator
2. **Error Handling**: Wrap agent execution in try-except for API errors and timeouts
3. **Timeout Management**: Set `max_duration=30` on runner to prevent hanging
4. **Conversation Context**: Pass message history as list of `{"role": "...", "content": "..."}` dicts
5. **Response Streaming**: Use `runner.stream()` for real-time response updates (optional for MVP)

**Configuration**:
- Use environment variable `OPENAI_API_KEY` for authentication
- Set model to `gpt-4o` or `gpt-4-turbo` for best intent understanding
- Enable `parallel_tool_calls=True` for concurrent tool execution

**Alternatives Considered**:
- **Direct OpenAI API calls**: Rejected due to manual tool orchestration complexity
- **LangChain**: Rejected due to over-engineering for simple tool use case
- **Custom agent implementation**: Rejected due to maintenance burden

**References**:
- OpenAI Agents SDK Docs: https://platform.openai.com/docs/agents
- FastAPI Async: https://fastapi.tiangolo.com/async/

---

## Research Topic 2: MCP Server Implementation

### Question: How to implement MCP tools using Official MCP SDK?

**Decision**: Use `mcp` Python package with Type-based tool registration.

### Key Findings

**MCP Tool Implementation Pattern**:
```python
from mcp import Tool, ToolContext
from mcp.server import Server

mcp_server = Server("todo-server")

@mcp_server.tool()
async def add_task(
    context: ToolContext,
    user_id: str,
    title: str,
    description: str | None = None
) -> dict:
    """Create a new task for the user.

    Args:
        user_id: The user's unique identifier
        title: The task title
        description: Optional detailed description

    Returns:
        dict with operation status and created task
    """
    # Database operation here
    task = await create_task_in_db(user_id, title, description)

    return {
        "success": True,
        "task": task.model_dump(),
        "message": f"Task '{title}' created successfully"
    }
```

**Tool Registration Best Practices**:
1. **Type Annotations**: Use Python type hints for all parameters (MCP SDK validates automatically)
2. **Docstrings**: Provide detailed docstrings for AI agent understanding
3. **Error Handling**: Return error dict with `{"success": False, "error": "message"}` on failure
4. **Async Functions**: All tools must be `async def` for FastAPI integration
5. **User ID First**: Always include `user_id` as first parameter for data isolation

**Server Configuration**:
```python
# Expose MCP server to Agents SDK
from mcp.adapters.openai import OpenAIAdapter

# Convert MCP tools to OpenAI function format
adapter = OpenAIAdapter(mcp_server)
openai_tools = adapter.get_tools()
```

**Tool Metadata**:
- Each tool gets auto-generated schema from type hints
- Docstring becomes tool description for AI
- Parameter types enforce validation

**Alternatives Considered**:
- **Custom JSON-RPC implementation**: Rejected due to reinventing the wheel
- **FastAPI routes as tools**: Rejected due to lack of standardization and self-description

**References**:
- MCP Python SDK: https://github.com/modelcontextprotocol/python-sdk
- MCP Specification: https://modelcontextprotocol.io/

---

## Research Topic 3: ChatKit Frontend Integration

### Question: How to integrate ChatKit with FastAPI backend?

**Decision**: Use `@openai/chatkit` React package with REST API adapter.

### Key Findings

**ChatKit Configuration**:
```typescript
// lib/chatkit.ts
import { ChatKit } from '@openai/chatkit'
import { RESTAdapter } from '@openai/chatkit/adapters/rest'

const chatkit = new ChatKit({
  adapter: new RESTAdapter({
    baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    headers: {
      'Authorization': `Bearer ${getAuthToken()}`
    }
  }),
  domain: ['todo', 'tasks'], // Allowed tool domains
  onError: (error) => {
    console.error('ChatKit error:', error)
  }
})

export default chatkit
```

**Component Usage**:
```typescript
// components/ChatInterface.tsx
import { useChat } from '@openai/chatkit/react'

function ChatInterface({ userId }: { userId: string }) {
  const { messages, send, isLoading } = useChat({
    endpoint: `/api/${userId}/chat`
  })

  return (
    <div>
      <MessageList messages={messages} />
      <MessageInput
        onSend={(text) => send(text)}
        disabled={isLoading}
      />
    </div>
  )
}
```

**Authentication Integration**:
```typescript
// Get JWT token from Better Auth client-side storage
function getAuthToken(): string {
  const session = betterAuthClient.getSession()
  return session?.token || ''
}
```

**Error Handling**:
- Display error messages from API in toast notifications
- Implement retry logic for network failures
- Show typing indicator during agent execution

**Streaming Consideration**:
- For MVP: Use complete response (wait for full agent execution)
- Future: Implement Server-Sent Events (SSE) for streaming responses

**Alternatives Considered**:
- **Custom chat UI**: Rejected due to reinventing conversation management
- **Other chatbot libraries**: Rejected due to lack of OpenAI integration

**References**:
- ChatKit Docs: https://platform.openai.com/docs/chatkit
- ChatKit React: https://npmjs.com/package/@openai/chatkit/react

---

## Research Topic 4: Database Schema Design

### Question: What is the optimal schema for conversations, messages, and tasks?

**Decision**: Use separate tables with foreign keys and proper indexing.

### Key Findings

**Schema Design**:
```sql
-- Tasks table (extends existing from previous phases)
CREATE TABLE tasks (
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
CREATE TABLE conversations (
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
CREATE TABLE messages (
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
        ON DELETE CASCADE
);
```

**Indexing Strategy**:
```sql
-- Critical indexes for performance
CREATE INDEX idx_tasks_user_id ON tasks(user_id);
CREATE INDEX idx_tasks_user_completed ON tasks(user_id, completed);
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_created_at ON messages(created_at DESC);
```

**Cascade Behavior**:
- `ON DELETE CASCADE` on user: Removes all user data when account deleted
- `ON DELETE CASCADE` on conversation: Removes all messages when conversation deleted

**Migration Strategy**:
- Use Alembic for versioned migrations
- Create initial migration for new tables
- Tasks table may already exist from previous phases (use `alembic revision --autogenerate`)

**Data Model Validation**:
- Use SQLModel for type-safe Python models
- Pydantic validation on all API inputs
- Database constraints as final validation layer

**Alternatives Considered**:
- **Single table for messages and tasks**: Rejected due to different data structures
- **JSONB for message storage**: Rejected due to query complexity and lack of relational integrity

---

## Research Topic 5: Stateless Conversation Context Management

### Question: How to efficiently fetch and format conversation history for agent input?

**Decision**: Fetch all messages for conversation, format as OpenAI message list, pass to agent.

### Key Findings

**Conversation Fetching**:
```python
async def get_conversation_history(
    db: Session,
    conversation_id: UUID,
    user_id: str
) -> List[dict]:
    """Fetch all messages for a conversation."""
    messages = db.exec(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .where(Message.user_id == user_id)
        .order_by(Message.created_at)
    ).all()

    # Format for OpenAI Agents SDK
    return [
        {
            "role": msg.role,  # "user" or "assistant"
            "content": msg.content
        }
        for msg in messages
    ]
```

**Performance Optimization**:
- Limit conversation history to last 50 messages for context window management
- Use database indexes for fast queries (see Topic 4)
- Cache recent conversations in application layer (optional optimization)

**Context Window Management**:
```python
MAX_HISTORY_MESSAGES = 50

def truncate_history(history: List[dict]) -> List[dict]:
    """Keep only recent messages to fit in context window."""
    if len(history) <= MAX_HISTORY_MESSAGES:
        return history
    return history[-MAX_HISTORY_MESSAGES:]
```

**Pagination Consideration**:
- For MVP: Load all messages (sufficient for <100 messages per conversation)
- Future: Implement cursor-based pagination for very long conversations

**Agent Input Construction**:
```python
async def build_agent_input(
    user_message: str,
    conversation_id: UUID | None,
    user_id: str,
    db: Session
) -> tuple[List[dict], UUID]:
    """Build agent input with conversation context."""

    # Get or create conversation
    if conversation_id is None:
        conversation = Conversation(user_id=user_id)
        db.add(conversation)
        db.commit()
        conversation_id = conversation.id
    else:
        # Verify conversation belongs to user
        conversation = db.get(Conversation, conversation_id)
        if conversation.user_id != user_id:
            raise HTTPException(403, "Access denied")

    # Fetch history
    history = await get_conversation_history(db, conversation_id, user_id)
    history = truncate_history(history)

    # Append new user message
    history.append({"role": "user", "content": user_message})

    return history, conversation_id
```

**Alternatives Considered**:
- **In-memory conversation cache**: Rejected due to statelessness requirement
- **Summary-based context compression**: Rejected due to complexity (future enhancement)

---

## Summary of Decisions

| Topic | Decision | Rationale |
|-------|----------|-----------|
| OpenAI Agents SDK | Use `openai-agents-sdk` with async runner | Native tool orchestration, async support |
| MCP Server | Use `mcp` package with Type-based registration | Standard protocol, auto-validation |
| ChatKit Frontend | Use `@openai/chatkit` React package | Official integration, less custom code |
| Database Schema | Separate tables with foreign keys | Relational integrity, clear separation |
| Context Management | Fetch all messages, truncate to 50 | Simple, sufficient for MVP |

## Technology Stack Confirmation

**Final Technology Choices**:
- Python 3.11+ for backend
- FastAPI 0.104+ for async web framework
- SQLModel 0.0.14+ for ORM
- OpenAI Agents SDK for agent logic
- Official MCP SDK for tools
- Neon PostgreSQL for database
- OpenAI ChatKit for frontend
- React 18+ / Next.js 14+ for UI
- Better Auth for authentication
- Alembic for database migrations
- pytest for backend testing

**All Technical Context Items Resolved**: ✅

## Next Steps

1. ✅ Research complete - all decisions documented
2. → Proceed to Phase 1: Generate data-model.md
3. → Generate API contracts in contracts/
4. → Create quickstart.md
5. → Update agent context file

---

**Research Version**: 1.0.0 | **Completed**: 2026-01-31
