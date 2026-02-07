# Stateless Conversation Flow - Quickstart Guide

## Overview

The Stateless Conversation Flow feature enables AI-powered task management through natural language chat. The system maintains complete conversation context in the database with zero server-side memory, enabling horizontal scaling and server restart survival.

## Architecture Highlights

**Stateless Design:**
- No in-memory conversation state
- All conversation data persisted in Neon PostgreSQL
- Any server instance can handle any request
- Server restarts don't lose conversation data

**6-Step Request Cycle:**
1. Receive & validate request
2. Fetch conversation history from database
3. Store user message in database
4. Invoke AI agent with history + new message
5. Store assistant response with tool_calls
6. Return response to frontend

## Database Schema

```sql
-- Conversations table (one per user)
CREATE TABLE conversations (
    id VARCHAR PRIMARY KEY,  -- UUID = user_id for simplicity
    user_id VARCHAR UNIQUE NOT NULL,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Messages table (all conversation messages)
CREATE TABLE messages (
    id VARCHAR PRIMARY KEY,
    conversation_id VARCHAR REFERENCES conversations(id),
    role VARCHAR NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    tool_calls JSONB,  -- MCP tool invocation results
    created_at TIMESTAMP
);

-- Performance index
CREATE INDEX ix_messages_conversation_id_created_at
    ON messages(conversation_id, created_at);
```

## API Endpoints

### POST /api/users/{user_id}/chat

Send a message to the AI assistant.

**Request:**
```bash
curl -X POST "https://api.example.com/api/users/{user_id}/chat" \
  -H "Authorization: Bearer {jwt_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Add a task to buy groceries"
  }'
```

**Response:**
```json
{
  "response": "I've added 'Buy groceries' to your tasks.",
  "tool_calls": [
    {
      "tool_name": "add_task",
      "parameters": {"title": "Buy groceries"},
      "result": {
        "success": true,
        "data": {
          "id": "123",
          "title": "Buy groceries",
          "completed": false
        }
      }
    }
  ]
}
```

**Rate Limiting:** 20 requests per minute per user

## MCP Tools Available

The AI agent can invoke these tools to manage tasks:

| Tool | Description | Parameters |
|------|-------------|------------|
| `add_task` | Create a new task | `title`, `description` (optional) |
| `list_tasks` | List all tasks | `status` (optional: "all", "pending", "completed") |
| `complete_task` | Mark task as completed | `task_id` |
| `update_task` | Modify task title/description | `task_id`, `title`, `description` |
| `delete_task` | Remove a task | `task_id` |

## Example Conversations

### Creating Tasks

**User:** "Add a task to buy groceries"

**AI:** Calls `add_task(title="Buy groceries")` → "I've added 'Buy groceries' to your tasks."

### Listing Tasks

**User:** "What do I need to do?"

**AI:** Calls `list_tasks(status="pending")` → "Here are your incomplete tasks: 1. Buy groceries"

### Completing Tasks

**User:** "Mark the groceries task as done"

**AI:** Calls `complete_task(task_id=1)` → "Great! I've marked task 1 (Buy groceries) as completed."

## Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@host/database

# AI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini

# Authentication
BETTER_AUTH_SECRET=your-secret-key-min-32-chars

# Logging
LOG_LEVEL=INFO
```

## Testing

1. **Start Backend:**
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn src.main:app --reload
   ```

2. **Start Frontend:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. **Test Chat:**
   - Navigate to `http://localhost:3000/chat`
   - Login with your account
   - Send a message: "Add a task to test the chat"
   - Verify task is created in database

## Performance Characteristics

- **History Fetch:** <200ms for 100 messages (composite index)
- **End-to-End Latency:** <3 seconds (including AI processing)
- **Concurrent Users:** Unlimited (stateless architecture)
- **Database Connections:** Pool size 10, max overflow 20

## Troubleshooting

### "Conversation not found"
- First message automatically creates conversation
- Check `user_id` matches authenticated user

### "Rate limit exceeded"
- 20 requests per minute per user
- Wait 60 seconds before retrying

### "Agent processing error"
- Check OPENAI_API_KEY is valid
- Verify OPENAI_MODEL is accessible
- Check logs for detailed error

### Tool calls not executing
- Verify task service is running
- Check user has permission to modify tasks
- Review tool call results in response

## Constitution Compliance

✅ **Stateless**: No server-side conversation state
✅ **Tool-Driven**: Agent only acts through MCP tools
✅ **Correctness**: All state persisted before response
✅ **Persistence**: Complete audit trail in database
✅ **NL Understanding**: OpenAI GPT-4o-mini for intent routing
✅ **Error Handling**: Graceful degradation, sanitized errors
✅ **Intent Routing**: Automatic tool selection via function calling
✅ **Data Integrity**: Transaction-wrapped database operations
✅ **Spec-Driven**: Implementation follows specification

## Next Steps

1. Run database migration: `alembic upgrade head`
2. Add OpenAI API key to `.env`
3. Test with example conversations
4. Monitor logs for performance metrics
5. Scale horizontally as needed (stateless design)
