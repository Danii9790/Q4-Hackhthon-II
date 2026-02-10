# Feature Specification: Chat API for Todo Management

**Feature Branch**: `003-chat-api`
**Created**: 2026-02-06
**Status**: Draft
**Input**: User description: "Todo AI Chatbot — Chat API"

---

## Constitution Alignment

This specification MUST comply with all principles in `.specify/memory/constitution.md`:

**Core Principles Applied**:
- Stateless Architecture with Database-Backed Persistence
- Tool-Driven AI Behavior
- Task Operation Correctness
- Conversational State Persistence
- Natural Language Understanding
- Error Handling and User Safety
- Agent Intent Routing
- Data Integrity and Security
- Spec-Driven Development

**Technology Constraints**:
- Frontend: OpenAI ChatKit, Next.js 16+, TypeScript, Tailwind CSS
- Backend: Python FastAPI, SQLModel, Neon Serverless PostgreSQL
- AI: OpenAI Agents SDK, Official MCP SDK
- Auth: Better Auth

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Send Message and Receive AI Response (Priority: P1)

**Why this priority**: This is the core interaction - users send messages to the chat interface and receive AI responses. Without this, the chat system doesn't function.

**Independent Test**: A user sends a message through the frontend, the backend processes it via the AI agent, and the user receives a complete response with any tool calls that were made.

**Acceptance Scenarios**:

1. **Given** an authenticated user sends "add task buy groceries", **When** the backend receives the POST request, **Then** it fetches conversation history, stores the user message, invokes the AI agent which calls the add_task tool, stores the AI response, and returns both the response message and the tool call details to the frontend
2. **Given** an authenticated user sends "show my tasks", **When** the backend processes the request, **Then** it retrieves conversation history, stores the user message, the agent calls list_tasks tool, and the response includes both the AI's text and the task list from the tool
3. **Given** an authenticated user sends "help", **When** the backend processes, **Then** it stores the message, the agent responds with help text (no tools called), and the response includes the message with an empty tool_calls array

---

### User Story 2 - Resume Conversation After Server Restart (Priority: P1)

**Why this priority**: Conversations must survive server restarts for reliability and user experience. Users should not lose context when the server restarts.

**Independent Test**: A user has a conversation, the server restarts, the user sends another message, and the conversation continues seamlessly with full history available.

**Acceptance Scenarios**:

1. **Given** a user with 5 messages in their conversation, **When** the server restarts and the user sends a 6th message, **Then** the backend fetches all 5 previous messages from the database before processing, and the AI agent responds with full context of the entire conversation
2. **Given** a user asks "remind me to buy milk" in one request, **When** the server restarts and the user says "mark it done", **Then** the agent can correctly identify which task to complete because it has access to the previous message from the database
3. **Given** a server restart occurs while a user is idle, **When** the user returns after 1 hour and sends a message, **Then** their conversation history is preserved and the agent responds appropriately based on earlier context

---

### User Story 3 - Handle Tool Calls in Response (Priority: P1)

**Why this priority**: The AI agent manages tasks by invoking MCP tools. The chat API must return tool call information so the frontend can display what actions were taken.

**Independent Test**: A user sends a message that triggers a tool call (e.g., "add task buy groceries"), and the response includes both the AI's confirmation message and the details of the tool that was invoked.

**Acceptance Scenarios**:

1. **Given** a user sends "add task call mom", **When** the backend processes the request and the agent calls add_task, **Then** the response includes tool_calls array with tool_name="add_task", parameters (title="call mom"), and result (task_id, created task)
2. **Given** a user sends "show my tasks", **When** the agent calls list_tasks, **Then** the response includes tool_calls with tool_name="list_tasks" and result containing the array of tasks
3. **Given** a user sends "complete task 1", **When** the agent calls complete_task, **Then** the response includes tool_calls showing which task was completed and the success status

---

### User Story 4 - Store Messages Reliably (Priority: P1)

**Why this priority**: All messages must be persisted for conversation history and debugging. Message loss is unacceptable.

**Independent Test**: Every user message and AI response is stored in the database before the API response is returned to the frontend.

**Acceptance Scenarios**:

1. **Given** a user sends any message, **When** the backend begins processing, **Then** the user message is immediately inserted into the database with role="user" and the current timestamp
2. **Given** the AI agent completes processing, **When** a response is generated, **Then** the assistant message is inserted into the database with role="assistant", content, and any tool_calls before the API returns
3. **Given** a database error occurs while storing a message, **Then** the API returns an error response to the frontend and does not proceed with agent processing

---

### User Story 5 - Handle Multiple Concurrent Users (Priority: P2)

**Why this priority**: The system must support multiple users chatting simultaneously without mixing conversations or losing messages.

**Independent Test**: Multiple users send messages concurrently, and each user's conversation remains isolated with correct message history.

**Acceptance Scenarios**:

1. **Given** user A and user B both send messages simultaneously, **When** the backend processes both requests, **Then** user A's message is stored in user A's conversation, user B's message in user B's conversation, and responses are returned to the correct users
2. **Given** 10 users are actively chatting at the same time, **When** they each send messages, **Then** all messages are correctly stored and each user receives their appropriate response without cross-talk
3. **Given** two users send messages that trigger tools (e.g., both create tasks), **When** the backend processes, **Then** each user's task is created with their correct user_id and ownership

---

### User Story 6 - Handle Errors Gracefully (Priority: P1)

**Why this priority**: Errors must not expose internal details or crash the system. Users receive helpful error messages.

**Independent Test**: When an error occurs (database unavailable, invalid user, agent failure), the API returns a user-friendly error message without exposing technical details.

**Acceptance Scenarios**:

1. **Given** an unauthenticated user sends a message, **When** the backend validates the request, **Then** the API returns 401 Unauthorized with message "Please sign in to continue"
2. **Given** the database is temporarily unavailable, **When** a user sends a message, **Then** the API returns 503 Service Unavailable with message "I'm having trouble right now. Please try again in a moment"
3. **Given** the AI agent fails to process a message, **When** an error occurs, **Then** the API returns 500 Internal Server Error with a user-friendly message, logs the error for debugging, and stores an error message in the conversation history

---

## Functional Requirements

### Requirement 1: Single Stateless Endpoint

**Description**: The chat system MUST expose a single POST endpoint that is completely stateless, with all conversation state stored in the database.

**Acceptance Criteria**:
- Endpoint path: POST /api/{user_id}/chat
- Each request is processed independently without server-side session state
- No in-memory conversation storage
- No session variables or global state
- Request contains user message text (no conversation ID needed)
- Response contains AI response and any tool calls
- Multiple servers can run behind a load balancer without issues

**Priority**: MUST (Non-negotiable - constitution principle)

---

### Requirement 2: Fetch Conversation History on Each Request

**Description**: On every request, the backend MUST fetch the complete conversation history for that user from the database before processing the new message.

**Acceptance Criteria**:
- Fetch all messages (both user and assistant) for the user's conversation
- Messages are returned in chronological order (oldest to newest)
- History includes message content, timestamps, roles (user/assistant), and tool calls
- If no conversation exists for the user, start a new empty conversation
- History fetching occurs before agent invocation
- Entire history is passed to the AI agent for context

**Priority**: MUST (Non-negotiable - constitution principle)

---

### Requirement 3: Store Messages Before and After Agent

**Description**: User messages MUST be stored before agent processing, and assistant responses MUST be stored before returning the API response.

**Acceptance Criteria**:
- User message is inserted into database immediately upon request receipt
- Message record includes: user_id, role="user", content, timestamp
- Only after user message is successfully stored does agent processing begin
- Assistant response is inserted into database after agent completes
- Assistant message record includes: user_id, role="assistant", content, tool_calls (if any), timestamp
- API response is returned only after both messages are stored
- If storage fails, error is returned and agent is not invoked

**Priority**: MUST (Non-negotiable - constitution principle)

---

### Requirement 4: Return Tool Calls with Response

**Description**: The API response MUST include any tool calls made by the AI agent during message processing.

**Acceptance Criteria**:
- Response includes a tool_calls array (empty if no tools were called)
- Each tool call includes: tool_name, parameters (input), and result (output)
- Tool calls are returned in the order they were executed
- Tool result includes the actual data returned by the MCP tool
- Frontend can display what actions were taken (e.g., "Task created: buy groceries")
- Tool call information is sufficient for debugging and auditing

**Priority**: MUST

---

### Requirement 5: User Isolation

**Description**: Each request MUST be scoped to a specific user, and users MUST NEVER access other users' conversations or messages.

**Acceptance Criteria**:
- user_id in URL path identifies the user
- All database queries filter by user_id
- No cross-user data access is possible
- Conversation history fetch only returns messages for that user
- Tool invocations automatically validate user ownership
- If user_id doesn't exist or is invalid, return 404 Not Found
- User cannot access another user's conversation by modifying user_id in request

**Priority**: MUST (Non-negotiable - security requirement)

---

### Requirement 6: Error Handling and Logging

**Description**: All errors MUST be handled gracefully with user-friendly messages, and all errors MUST be logged for debugging.

**Acceptance Criteria**:
- Database errors return 503 with "try again" message
- Validation errors return 400 with explanation
- Authentication errors return 401
- User not found returns 404
- Agent failures return 500 with generic error message
- All errors are logged with stack traces for debugging (internal only)
- Error messages never expose database schemas, SQL, or internal IDs
- Error messages are actionable and user-friendly

**Priority**: MUST

---

### Requirement 7: Response Format Consistency

**Description**: All successful responses MUST follow a consistent format, making them predictable for the frontend.

**Acceptance Criteria**:
- Success responses include: message_id, content, role="assistant", tool_calls array
- Message timestamps are included in ISO 8601 format
- tool_calls is always present (empty array if no tools called)
- Response structure matches API contract exactly
- No unexpected or optional fields in success responses
- Error responses follow consistent error format

**Priority**: MUST

---

## Non-Functional Requirements

### Performance
- 95% of requests complete within 3 seconds (including database operations and agent processing)
- Database queries are optimized with proper indexes
- No N+1 query patterns when fetching conversation history

### Scalability
- Stateless design supports horizontal scaling
- Multiple instances can run behind a load balancer
- No shared state between server instances

### Reliability
- Messages are never lost (stored before processing)
- Server restarts don't lose conversations
- Database transaction failures are handled gracefully

### Security
- User authentication is validated before processing
- User isolation is enforced on all database operations
- Error messages don't leak sensitive information

---

## API Contract

### Endpoint: POST /api/{user_id}/chat

**Description**: Processes a user message through the AI agent and returns the assistant's response

**Path Parameters**:
- `user_id` (string, required): Unique identifier for the user

**Request Body**:
```json
{
  "type": "object",
  "properties": {
    "message": {
      "type": "string",
      "description": "User's message text",
      "minLength": 1,
      "maxLength": 5000
    }
  },
  "required": ["message"]
}
```

**Success Response** (200 OK):
```json
{
  "type": "object",
  "properties": {
    "message_id": {
      "type": "string",
      "description": "Unique identifier for the assistant's message"
    },
    "content": {
      "type": "string",
      "description": "Assistant's response text"
    },
    "role": {
      "type": "string",
      "enum": ["assistant"],
      "description": "Message role"
    },
    "created_at": {
      "type": "string",
      "format": "date-time",
      "description": "Timestamp when message was created"
    },
    "tool_calls": {
      "type": "array",
      "description": "Tool calls made by the agent during processing",
      "items": {
        "type": "object",
        "properties": {
          "tool_name": {
            "type": "string",
            "description": "Name of the tool that was called"
          },
          "parameters": {
            "type": "object",
            "description": "Parameters passed to the tool"
          },
          "result": {
            "type": "object",
            "description": "Result returned by the tool"
          }
        }
      }
    }
  }
}
```

**Error Responses**:

**400 Bad Request**:
```json
{
  "success": false,
  "error": "Invalid request",
  "message": "Message is required and must be between 1 and 5000 characters"
}
```

**401 Unauthorized**:
```json
{
  "success": false,
  "error": "Unauthorized",
  "message": "Please sign in to continue"
}
```

**404 Not Found**:
```json
{
  "success": false,
  "error": "Not found",
  "message": "User not found"
}
```

**500 Internal Server Error**:
```json
{
  "success": false,
  "error": "Internal server error",
  "message": "I'm having trouble processing your request. Please try again."
}
```

**503 Service Unavailable**:
```json
{
  "success": false,
  "error": "Service unavailable",
  "message": "I'm having trouble right now. Please try again in a moment."
}
```

---

## Out of Scope

The following are explicitly OUT OF SCOPE for this feature:

- Streaming responses or real-time message delivery
- WebSocket connections or Server-Sent Events
- Multiple chat endpoints (e.g., separate endpoints for different conversation types)
- Client-side conversation state management
- Message editing or deletion
- File uploads or attachments
- Typing indicators or presence information
- Push notifications for new messages
- Conversation archiving or export
- Multi-user conversations or group chats
- Message search or filtering
- Conversation branching or forking

---

## Assumptions

1. **User authentication**: User is authenticated before reaching this endpoint (auth layer validates user_id)
2. **Agent availability**: AI agent service is available and responsive
3. **Database availability**: PostgreSQL database is accessible and properly configured
4. **Conversation per user**: Each user has exactly one active conversation (no multiple conversations per user)
5. **Message ordering**: Messages are processed in the order they are received
6. **Request size**: Message text is reasonably sized (max 5000 characters)
7. **Response size**: AI agent responses are reasonably sized (no multi-megabyte responses)

---

## Success Criteria

The feature is successful when:

1. **Stateless Operation**: Server can be restarted at any time without losing conversation context (verified through restart tests)
2. **Message Persistence**: 100% of messages (both user and assistant) are stored in the database
3. **Conversation Continuity**: 100% of post-restart messages include full conversation context
4. **Tool Call Transparency**: 100% of agent tool invocations are returned in API responses
5. **User Isolation**: 100% of requests properly isolate user data (zero cross-user data leakage)
6. **Performance**: 95% of requests complete within 3 seconds
7. **Error Safety**: 100% of errors return user-friendly messages with no internal details exposed

---

## Dependencies

### Internal Dependencies
- User authentication system (validates user_id)
- AI agent service (processes messages and invokes tools)
- MCP tools (add_task, list_tasks, complete_task, update_task, delete_task)
- Database schema (users, conversations, messages tables)

### External Dependencies
- PostgreSQL database for message storage
- AI agent (defined in feature 001-agent-behavior)
- MCP tools (defined in feature 002-mcp-tools)

---

## Notes

This specification defines the Chat API that connects the frontend to the AI backend. The API is:

1. **Stateless**: No server-side conversation state
2. **Database-Backed**: All messages stored in PostgreSQL
3. **Transparent**: Returns tool calls for frontend display
4. **Reliable**: Messages stored before and after agent processing
5. **Secure**: User-scoped with authentication validation

**Request Flow**:
1. Frontend POSTs message to /api/{user_id}/chat
2. Backend validates user authentication
3. Backend fetches conversation history from database
4. Backend stores user message in database
5. Backend invokes AI agent with history + new message
6. Agent may invoke MCP tools (add_task, list_tasks, etc.)
7. Backend stores assistant response (with tool calls) in database
8. Backend returns response to frontend

**Separation of Concerns**:
- **Frontend**: Displays chat interface, sends messages, displays responses
- **Chat API**: Stateless request processing, message persistence, conversation history retrieval
- **AI Agent**: Interprets natural language, determines intent, invokes MCP tools
- **MCP Tools**: Perform stateless CRUD operations on tasks

This architecture ensures the system is stateless, scalable, and reliable while maintaining full conversation context across server restarts.
