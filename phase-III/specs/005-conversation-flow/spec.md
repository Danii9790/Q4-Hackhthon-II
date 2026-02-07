# Feature Specification: Stateless Conversation Flow for Todo Management

**Feature Branch**: `005-conversation-flow`
**Created**: 2026-02-06
**Status**: Draft
**Input**: User description: "Todo AI Chatbot — Conversation Flow"

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

### User Story 1 - First Message Creates Conversation (Priority: P1)

**Why this priority**: This is the initial state - the system must handle the first message from a new user and establish their conversation context.

**Independent Test**: A new user sends their first message, and the system creates a new conversation, stores the message, processes it through the AI agent, stores the response, and returns the result - all without any server-side memory.

**Acceptance Scenarios**:

1. **Given** a user who has never chatted before sends "add task buy groceries", **When** the system processes the request, **Then** it creates a new conversation record, stores the user message, invokes the AI agent with empty history, stores the assistant response, and returns the response to the frontend
2. **Given** the system is restarted (all memory cleared), **When** the same user sends "show my tasks", **Then** the system fetches the conversation created in scenario 1, retrieves the previous message history, and the AI agent responds with full context of the first message
3. **Given** two new users send their first messages simultaneously, **When** both requests are processed, **Then** each user gets a separate conversation record with their own messages, and no cross-talk occurs

---

### User Story 2 - Subsequent Messages Reconstruct Context (Priority: P1)

**Why this priority**: After the first message, every subsequent request must reconstruct full conversation history from the database to maintain context.

**Independent Test**: A user with existing conversation history sends a new message, and the system fetches all previous messages, processes the new one with full context, and persists the exchange.

**Acceptance Scenarios**:

1. **Given** a user with 10 previous messages sends "mark task 1 as done", **When** the system processes, **Then** it fetches all 10 previous messages from the database, provides them to the AI agent along with the new message, stores the new user message and assistant response, and returns the result
2. **Given** a user with a long conversation (50 messages) sends a new message, **When** the system fetches history, **Then** all 50 previous messages are retrieved in chronological order and provided to the AI agent
3. **Given** a server restart occurs while a user is active, **When** the user sends their next message, **Then** the system has zero in-memory context but fetches the complete conversation history from the database and processes the message correctly

---

### User Story 3 - Request Processing is Independent (Priority: P1)

**Why this priority**: Each request must be completely independent - no session state, no memory between requests. This enables scalability and reliability.

**Independent Test**: Multiple requests are processed concurrently by different server instances, and each completes successfully using only database state.

**Acceptance Scenarios**:

1. **Given** a user sends message A and immediately sends message B (before A completes), **When** both requests are processed, **Then** each request independently fetches conversation history, processes the message, and stores results - no shared state is needed
2. **Given** three server instances are running behind a load balancer, **When** a user sends 5 rapid requests, **Then** any server can handle any request, and all succeed because all state is in the database
3. **Given** a server instance crashes mid-request, **When** the user retries the request, **Then** a different server instance handles it successfully with no data loss

---

### User Story 4 - Database is Source of Truth (Priority: P1)

**Why this priority**: The database must be the only source of truth for conversation state. No in-memory caches or session stores can be used.

**Independent Test**: Server restarts, crashes, and scaling events do not lose any conversation data because everything is in the database.

**Acceptance Scenarios**:

1. **Given** a user has an active conversation, **When** all server instances are shut down and restarted, **Then** the user's conversation history remains intact in the database and is fully available on the next request
2. **Given** a server instance crashes while processing a message, **When** the user retries, **Then** the database still contains all previous messages and the retry succeeds
3. **Given** the database is queried for conversation history, **When** the results are returned, **Then** they are authoritative and complete - no other state source exists

---

### User Story 5 - Full Cycle Completes in One Request (Priority: P1)

**Why this priority**: Each request must complete the full cycle (fetch, process, persist, respond) in a single request-response exchange.

**Independent Test**: A single HTTP request results in the user's message being stored, the AI agent processing it, and the response being stored and returned.

**Acceptance Scenarios**:

1. **Given** a user sends a message via POST request, **When** the system processes, **Then** the following happens in order: fetch conversation history → store user message → invoke AI agent → store assistant response → return response to frontend
2. **Given** a request is processing, **When** any step fails, **Then** the entire request fails gracefully with an error response, and no partial state is committed (transactions rolled back)
3. **Given** a request completes successfully, **When** the response is returned, **Then** both the user message and assistant response are permanently stored in the database and available for future requests

---

### User Story 6 - System Survives Restarts (Priority: P1)

**Why this priority**: The system must maintain zero data loss across server restarts. This is critical for reliability and user trust.

**Independent Test**: Server is restarted while users are active, and when users send new messages, their conversations continue seamlessly with full context.

**Acceptance Scenarios**:

1. **Given** 10 users with active conversations, **When** all server instances are restarted, **Then** all users can send new messages and receive correct responses with full conversation context
2. **Given** a server is restarted every minute during a 1-hour period, **When** users continuously send messages, **Then** no conversation data is lost and all messages are correctly persisted
3. **Given** a database backup is restored and server is started, **When** users send messages, **Then** their conversation history from before the backup is available and processing continues normally

---

## Functional Requirements

### Requirement 1: Request Independence

**Description**: Each request MUST be processed independently without any dependency on server-side state from previous requests.

**Acceptance Criteria**:
- No session variables or global state store conversation context
- No in-memory caches store user messages or conversation history
- Each request contains all information needed to process (user_id, message)
- Request processing does not depend on data from previous requests being in memory
- Multiple server instances can process requests interchangeably
- Request order doesn't affect correctness (no sequential dependencies)

**Priority**: MUST (Non-negotiable - constitution principle)

---

### Requirement 2: Conversation History Retrieval

**Description**: On every request, the system MUST fetch the complete conversation history for that user from the database before processing the new message.

**Acceptance Criteria**:
- Query returns all messages (both user and assistant) for the user's conversation
- Messages are ordered chronologically (oldest first, newest last)
- History includes message content, role (user/assistant), timestamps, and tool calls
- History retrieval occurs before any agent processing
- If no conversation exists, create one automatically (for first message)
- Fetched history is passed to AI agent as context

**Priority**: MUST (Non-negotiable - constitution principle)

---

### Requirement 3: User Message Persistence

**Description**: The system MUST persist the user's message to the database before invoking the AI agent.

**Acceptance Criteria**:
- User message is stored immediately upon request receipt
- Message record includes: conversation_id, role="user", content, timestamp
- Storage is atomic (all-or-nothing)
- Only after successful storage does agent processing begin
- If storage fails, request returns error and agent is not invoked
- Stored message is immediately available for history retrieval

**Priority**: MUST

---

### Requirement 4: Agent Invocation with Context

**Description**: The system MUST invoke the AI agent with the complete conversation history plus the new user message.

**Acceptance Criteria**:
- Agent receives array of all previous messages (from database)
- Agent receives the new user message (just stored)
- Agent has full context of entire conversation
- Agent may invoke MCP tools based on this context
- Agent processes message and generates response
- Agent may also invoke tools during processing

**Priority**: MUST

---

### Requirement 5: Assistant Response Persistence

**Description**: The system MUST persist the AI agent's response (including any tool calls) to the database before returning the HTTP response.

**Acceptance Criteria**:
- Assistant response is stored after agent completes processing
- Message record includes: conversation_id, role="assistant", content, tool_calls, timestamp
- tool_calls field stores structured data about any tools invoked by agent
- Storage is atomic (all-or-nothing)
- Response is returned to frontend only after successful storage
- If storage fails, request returns error but user message remains stored

**Priority**: MUST

---

### Requirement 6: Transactional Integrity

**Description**: Database operations MUST be performed transactionally to ensure atomicity and prevent partial state updates.

**Acceptance Criteria**:
- User message storage and assistant response storage are wrapped in database transactions
- If assistant response storage fails, user message storage is rolled back
- If agent processing fails, user message storage is rolled back
- Either all database operations succeed or none do
- No partial state visible to other requests
- Database maintains consistent state at all times

**Priority**: MUST

---

### Requirement 7: Error Recovery

**Description**: The system MUST handle errors gracefully without losing conversation state or exposing internal details.

**Acceptance Criteria**:
- Database errors return user-friendly error messages
- Agent errors are logged but don't expose internal details to users
- Failed requests don't corrupt conversation state
- Users can retry failed requests
- No conversation data is lost due to server restarts or crashes
- Error messages don't reveal database schemas, SQL, or stack traces

**Priority**: MUST

---

## Request Processing Cycle

The complete stateless request cycle consists of these steps:

1. **Receive Request**
   - Backend receives POST request with user_id and message
   - Validates user authentication
   - Extracts message content

2. **Fetch Conversation History**
   - Queries database for all messages in user's conversation
   - Retrieves messages in chronological order
   - Returns empty array if no previous messages

3. **Store User Message**
   - Begins database transaction
   - Inserts user message into messages table
   - Commits transaction (or rolls back on error)

4. **Invoke AI Agent**
   - Passes conversation history + new message to agent
   - Agent may invoke MCP tools based on context
   - Agent generates response message
   - Agent returns response + any tool calls

5. **Store Assistant Response**
   - Begins database transaction
   - Inserts assistant message into messages table
   - Includes tool_calls if any tools were invoked
   - Commits transaction (or rolls back on error)

6. **Return Response**
   - Returns assistant message to frontend
   - Includes tool_calls information
   - Request cycle complete

**Stateless Properties**:
- No conversation state stored in memory between steps
- Each step uses only database state + request data
- Request can be processed by any server instance
- Server restarts don't affect the cycle (database persists everything)

---

## Non-Functional Requirements

### Performance
- Complete request cycle completes in under 3 seconds for 95% of requests
- Conversation history fetch completes in under 200ms for 100 messages
- No performance degradation as conversation length grows

### Scalability
- Stateless design supports horizontal scaling
- Multiple server instances can run behind load balancer
- No shared state or sticky sessions required
- Independent requests enable concurrent processing

### Reliability
- Zero conversation data loss across server restarts
- Database transactions prevent partial updates
- Failed requests don't corrupt conversation state
- System recovers gracefully from crashes

### Maintainability
- Simple request flow (no complex session management)
- Easy to debug (all state in database)
- Easy to test (stateless, deterministic)
- Easy to deploy (no shared state to synchronize)

---

## Out of Scope

The following are explicitly OUT OF SCOPE for this feature:

- Long-running sessions or connections
- Background workers or job queues
- Real-time streaming responses
- In-memory conversation caching
- Partial context loading (e.g., "last N messages only")
- Session tokens or session IDs
- WebSocket connections
- Server-sent events
- Optimistic locking for concurrent requests
- Request ordering guarantees

---

## Assumptions

1. **Database reliability**: PostgreSQL database is available and responds within performance targets
2. **User authentication**: User identity is validated before request processing begins
3. **Agent availability**: AI agent service is available and responds within performance targets
4. **Network reliability**: Network between backend and database is stable
5. **Request size**: User messages are reasonably sized (fit within database field limits)
6. **Response size**: Agent responses are reasonably sized (no multi-megabyte responses)
7. **Transaction isolation**: Database transactions provide ACID guarantees

---

## Success Criteria

The feature is successful when:

1. **Request Independence**: 100% of requests process correctly without server-side state (verified through concurrency tests)
2. **Context Reconstruction**: 100% of requests fetch complete conversation history (verified through restart tests)
3. **Message Persistence**: 100% of messages (user and assistant) are stored in database
4. **Restart Survival**: 100% of conversations survive server restarts with zero data loss
5. **Cycle Completion**: 100% of requests complete full cycle (fetch → store user → agent → store assistant → respond)
6. **Transaction Integrity**: 100% of database operations are atomic (no partial state)
7. **Performance**: 95% of requests complete within 3 seconds

---

## Dependencies

### Internal Dependencies
- Database schema (004-database-schema) provides tables for users, conversations, messages
- AI agent service (001-agent-behavior) processes messages with context
- MCP tools (002-mcp-tools) may be invoked by agent
- Chat API endpoint (003-chat-api) initiates request cycle

### External Dependencies
- PostgreSQL database for state persistence
- AI agent service for message processing
- MCP tools for task operations

---

## Notes

This specification defines the stateless conversation flow that enables the entire Todo AI Chatbot system to function without server-side state. The flow is:

1. **Stateless by Design**: No in-memory conversation state; everything in database
2. **Independent Requests**: Each request is self-contained; no session dependencies
3. **Database as Truth**: Database is only source of truth for conversation state
4. **Full Cycle**: Each request completes entire fetch-process-persist-return cycle
5. **Restart-Safe**: Server restarts don't lose any conversation data

**Relationship to Other Specifications**:
- 001-agent-behavior: Receives conversation history from this flow
- 002-mcp-tools: May be invoked during agent processing step
- 003-chat-api: Initiates this request flow
- 004-database-schema: Provides tables for storing state

**Why This Matters**:
This flow is the key to the stateless architecture. By fetching conversation history on every request and persisting all messages, the system achieves:
- **Scalability**: Any server instance can handle any request
- **Reliability**: No conversation data lost during crashes or restarts
- **Simplicity**: No session management, no cache invalidation, no sticky sessions
- **Debuggability**: All state visible in database, easy to inspect and verify

**Request Flow Visualization**:
```
User Request
    ↓
[No Memory Lookup - Stateless]
    ↓
Fetch History from Database
    ↓
Store User Message in Database
    ↓
Invoke AI Agent with History
    ↓
Agent May Invoke MCP Tools
    ↓
Store Assistant Response in Database
    ↓
Return Response to User
    ↓
[No Memory Update - Stateless]
```

This flow ensures that after the response is returned, the server instance can be shut down or repurposed immediately without any loss of conversation state.
