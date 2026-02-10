# Implementation Plan: Stateless Conversation Flow for Todo Management

**Branch**: `005-conversation-flow` | **Date**: 2026-02-06 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/005-conversation-flow/spec.md`

## Summary

This plan implements the complete stateless conversation flow that orchestrates the entire Todo AI Chatbot system. The system processes each user message as an independent request cycle: fetch conversation history from database → store user message → invoke AI agent with context → store assistant response → return response. All state persists in Neon PostgreSQL, enabling horizontal scaling, server restart survival, and zero data loss. The flow integrates 5 layers: Chat API endpoint, Agent Behavior (OpenAI Agents SDK), MCP Tools (official SDK), Database Schema (SQLModel), and Stateless Conversation Flow.

## Technical Context

**Language/Version**: Python 3.12+ (backend), TypeScript 5.8+ (frontend)
**Primary Dependencies**:
- Backend: FastAPI 0.115+, SQLModel 0.15+, OpenAI Agents SDK, Official MCP SDK, Better Auth
- Frontend: Next.js 16+, OpenAI ChatKit, React 19+, Tailwind CSS 4.0

**Storage**: Neon Serverless PostgreSQL (sqlalchemy + psycopg2 connection pooling)
**Testing**: pytest (backend), React Testing Library (frontend)
**Target Platform**: Linux server (backend), Vercel deployment (frontend)
**Project Type**: web (full-stack Next.js + FastAPI)
**Performance Goals**:
- 95% of requests complete within 3 seconds end-to-end
- Conversation history fetch under 200ms for 100 messages
- Support 100+ concurrent users without degradation

**Constraints**:
- Zero server-side state (constitution requirement)
- All agent operations through MCP tools only
- JWT authentication required for all endpoints
- User isolation enforced at database level

**Scale/Scope**:
- 5 feature specifications (agent-behavior, mcp-tools, chat-api, database-schema, conversation-flow)
- 4 database entities (users, tasks, conversations, messages)
- 5 MCP tools (add_task, list_tasks, complete_task, update_task, delete_task)
- Single chat endpoint with stateless request processing

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Before proceeding with this plan, verify compliance with the project constitution (`.specify/memory/constitution.md`):

- [x] **Stateless Architecture**: No in-memory state; all state in database
- [x] **Tool-Driven AI Behavior**: All state changes through MCP tools
- [x] **Task Operation Correctness**: Atomic, traceable operations
- [x] **Conversational State Persistence**: History reconstructed on each request
- [x] **Natural Language Understanding**: Casual, simple phrases supported
- [x] **Error Handling**: Graceful, user-friendly error messages
- [x] **Agent Intent Routing**: Correct tool selection for user intents
- [x] **Data Integrity**: User isolation, referential integrity enforced
- [x] **Spec-Driven Development**: Adheres to Phase-III specification

**Non-Compliance Notes**: None - this plan is the orchestration layer that enforces all constitution principles by implementing the stateless request cycle defined in spec 005-conversation-flow.

## Project Structure

### Documentation (this feature)

```text
specs/005-conversation-flow/
├── spec.md              # Feature specification (already created)
├── plan.md              # This file
├── research.md          # Phase 0: Agent prompt research, ChatKit integration patterns
├── data-model.md        # Phase 1: Message/Conversation entities with relationships
├── quickstart.md        # Phase 1: Development setup and testing guide
├── contracts/           # Phase 1: API contracts
│   ├── chat-api.yaml    # OpenAPI spec for POST /api/{user_id}/chat
│   ├── mcp-tools.yaml   # MCP tool schemas
│   └── request-flow.md  # Sequence diagrams for request cycle
└── tasks.md             # Phase 2: Implementation tasks (created via /sp.tasks)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/
│   │   ├── user.py              # User model (already exists)
│   │   ├── task.py              # Task model (already exists)
│   │   ├── conversation.py      # NEW: Conversation model
│   │   └── message.py           # NEW: Message model
│   ├── services/
│   │   ├── auth.py              # Auth service (already exists)
│   │   ├── task.py              # Task service (already exists)
│   │   ├── agent.py             # NEW: Agent service with OpenAI Agents SDK
│   │   ├── conversation.py      # NEW: Conversation history service
│   │   └── mcp_server.py        # NEW: MCP server with 5 tools
│   ├── api/
│   │   ├── routes/
│   │   │   ├── auth.py          # Auth routes (already exists)
│   │   │   ├── tasks.py         # Task routes (already exists)
│   │   │   └── chat.py          # NEW: Chat endpoint
│   │   └── dependencies.py      # JWT auth dependency (already exists)
│   ├── db.py                    # Database engine (already exists)
│   └── main.py                  # FastAPI app (already exists)
└── tests/
    ├── contract/
    │   └── test_chat_api.py      # NEW: Chat API contract tests
    ├── integration/
    │   ├── test_conversation_state.py  # NEW: Stateless conversation tests
    │   └── test_agent_tools.py         # NEW: Agent tool invocation tests
    └── unit/
        ├── test_agent_service.py       # NEW: Agent logic tests
        └── test_mcp_tools.py           # NEW: MCP tool tests

frontend/
├── src/
│   ├── app/
│   │   ├── (auth)/              # Auth routes (already exists)
│   │   │   ├── login/
│   │   │   └── signup/
│   │   ├── chat/                # NEW: Chat interface page
│   │   │   └── page.tsx
│   │   ├── dashboard/           # Dashboard (already exists)
│   │   │   └── page.tsx
│   │   ├── layout.tsx           # Root layout (already exists)
│   │   └── page.tsx             # Landing page (already exists)
│   ├── components/
│   │   ├── task/                # Task components (already exist)
│   │   ├── auth/                # Auth components (already exist)
│   │   └── chat/                # NEW: Chat components
│   │       ├── ChatInterface.tsx    # Main chat container
│   │       ├── MessageList.tsx      # Message history display
│   │       ├── MessageInput.tsx     # Input field with send button
│   │       └── TypingIndicator.tsx  # Loading state
│   ├── lib/
│   │   ├── api.ts               # API client (already exists)
│   │   ├── auth.ts              # Auth utilities (already exists)
│   │   └── chatkit.ts           # NEW: ChatKit integration
│   ├── types/
│   │   ├── task.ts              # Task types (already exist)
│   │   └── chat.ts              # NEW: Chat message types
│   └── middleware.ts            # Auth middleware (already exists)
└── tests/
    └── chat/
        ├── ChatInterface.test.tsx      # NEW: Chat component tests
        └── chatkit.integration.test.ts # NEW: ChatKit API tests
```

**Structure Decision**: Web application structure selected because the project is a full-stack application with Next.js frontend and FastAPI backend. The backend follows a layered architecture (models → services → API routes) that aligns with the 5-layer system architecture defined in the specifications. Frontend uses App Router for route organization and component-based architecture.

## Complexity Tracking

> **No constitutional violations - this section not applicable**

## Phase 0: Research

### Goal

Investigate technical unknowns for agent prompt engineering, ChatKit integration patterns, and MCP tool implementation to inform Phase 1 design.

### Research Questions

1. **Agent Prompt Engineering** (001-agent-behavior)
   - What system prompt enables the AI agent to:
     - Interpret user intent accurately (95% target accuracy)
     - Select correct MCP tools for each operation type
     - Handle ambiguous task references ("the groceries task" when multiple exist)
     - Generate natural, conversational responses that confirm actions
   - Research: OpenAI Agents SDK documentation, few-shot examples, conversation context handling
   - Output: Recommended system prompt with tool invocation patterns

2. **ChatKit Integration** (003-chat-api + frontend)
   - How to integrate OpenAI ChatKit with Next.js 16+ App Router
   - What's the message format expected by ChatKit for streaming vs non-streaming responses
   - How to structure tool_calls in ChatKit message format
   - Research: ChatKit React components, TypeScript types, backend integration
   - Output: ChatKit setup guide with code examples for `/chat` page

3. **MCP Server Implementation** (002-mcp-tools)
   - How to implement MCP server using official MCP SDK
   - What's the tool schema format (JSON Schema for tool parameters)
   - How to register 5 tools (add_task, list_tasks, complete_task, update_task, delete_task)
   - How to pass user_id context to each tool invocation
   - Research: Official MCP SDK docs, tool registration patterns, authentication context
   - Output: MCP server setup guide with tool implementations

4. **Conversation State Reconstruction** (005-conversation-flow)
   - How to efficiently fetch 100+ message history for context reconstruction
   - What's the optimal database query pattern (ordering, indexing)
   - How to format conversation history for OpenAI Agents SDK (message array format)
   - Research: SQLModel query optimization, message array construction, token limits
   - Output: Conversation history service with efficient query patterns

5. **Error Handling & Transaction Safety** (005-conversation-flow)
   - How to wrap message storage in database transactions
   - How to handle agent failures without corrupting conversation state
   - What error messages to return to frontend (user-friendly vs internal)
   - Research: SQLAlchemy transaction patterns, error classification, recovery strategies
   - Output: Error handling guide with transaction patterns

### Research Process

For each question:
1. Review official documentation (OpenAI Agents SDK, MCP SDK, ChatKit)
2. Examine existing code in `backend/` and `frontend/` for patterns
3. Create minimal proof-of-concept code if needed
4. Document findings in `research.md` with code examples
5. Update `data-model.md` and `contracts/` based on findings

### Deliverables

- `specs/005-conversation-flow/research.md` - Technical research findings with code examples
- Documentation of agent prompt patterns, ChatKit integration, MCP tool registration
- Performance benchmarks for conversation history fetch (target: <200ms for 100 messages)
- Identified risks and mitigation strategies

### Acceptance Criteria

- [ ] All 5 research questions answered with documentation
- [ ] Proof-of-concept code demonstrates agent tool invocation
- [ ] ChatKit integration example shows message display with tool_calls
- [ ] MCP server example registers all 5 tools with proper schemas
- [ ] Conversation history query benchmark shows <200ms for 100 messages
- [ ] `research.md` reviewed and approved

## Phase 1: Design

### Goal

Create data models, API contracts, and quickstart guide based on Phase 0 research findings.

### 1.1 Data Model Design (`data-model.md`)

Create detailed data model specifications for 4 entities:

**Users Table** (managed by Better Auth - already exists)
- Fields: id (UUID), email (unique), password_hash, name, created_at, reset_token, reset_token_expires
- Indexes: email (unique)
- Relationships: one-to-many with tasks, conversations

**Tasks Table** (already exists, verify against spec)
- Fields: id (auto-increment), user_id (FK), title (200 chars), description (1000 chars), completed (bool), created_at, updated_at
- Indexes: user_id, completed
- Constraints: user_id FK → users.id (cascade delete)
- Ownership enforcement: All queries filtered by user_id

**Conversations Table** (NEW - needs implementation)
- Fields: id (UUID), user_id (FK, unique), created_at, updated_at
- Indexes: user_id (unique - one conversation per user)
- Constraints: user_id FK → users.id (cascade delete)
- Rationale: Single ongoing conversation per user for simplicity

**Messages Table** (NEW - needs implementation)
- Fields: id (UUID), conversation_id (FK), role (enum: "user" | "assistant"), content (text), tool_calls (JSONB, nullable), created_at
- Indexes: conversation_id, created_at (for chronological ordering)
- Constraints: conversation_id FK → conversations.id (cascade delete)
- JSONB structure for tool_calls: `[{tool_name, parameters, result, timestamp}]`

**Entity Relationships**:
- User 1:N Conversation (one user has one conversation)
- User 1:N Tasks (one user has many tasks)
- Conversation 1:N Messages (one conversation has many messages)
- Cascade deletion: Delete user → delete their conversation and tasks

**Validation Rules**:
- user_id required in all entities (enforced at DB level)
- role must be "user" or "assistant"
- content cannot be empty
- tool_calls only allowed when role="assistant"

**Migration Strategy**:
- Use Alembic for schema migrations
- Create migration: `alembic revision --autogenerate -m "add conversations and messages tables"`
- Test migration on development database first
- Rollback procedure documented

### 1.2 API Contracts (`contracts/`)

Create OpenAPI specifications and request/response schemas:

**chat-api.yaml** - OpenAPI 3.0 specification
```yaml
openapi: 3.0.0
info:
  title: Todo AI Chatbot API
  version: 1.0.0
paths:
  /api/{user_id}/chat:
    post:
      summary: Send message to AI chatbot
      parameters:
        - name: user_id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [message]
              properties:
                message:
                  type: string
                  minLength: 1
                  maxLength: 5000
      responses:
        200:
          description: Successful AI response
          content:
            application/json:
              schema:
                type: object
                required: [response, tool_calls]
                properties:
                  response:
                    type: string
                    description: AI assistant's text response
                  tool_calls:
                    type: array
                    items:
                      type: object
                      required: [tool_name, parameters, result]
                      properties:
                        tool_name:
                          type: string
                          enum: [add_task, list_tasks, complete_task, update_task, delete_task]
                        parameters:
                          type: object
                        result:
                          type: object
        400:
          description: Validation error
        401:
          description: Unauthorized (invalid JWT)
        500:
          description: Server error
      security:
        - BearerAuth: []
```

**mcp-tools.yaml** - MCP tool schemas (JSON Schema format)
```yaml
tools:
  add_task:
    name: add_task
    description: Create a new task for the user
    parameters:
      type: object
      required: [title]
      properties:
        title:
          type: string
          minLength: 1
          maxLength: 200
          description: Task title
        description:
          type: string
          maxLength: 1000
          description: Optional task details
    returns:
      type: object
      properties:
        success:
          type: boolean
        task:
          type: object
          properties:
            id:
              type: integer
            title:
              type: string
            description:
              type: string
            completed:
              type: boolean

  list_tasks:
    name: list_tasks
    description: List all tasks for the user
    parameters:
      type: object
      properties:
        include_completed:
          type: boolean
          description: Include completed tasks (default: true)
    returns:
      type: object
      properties:
        success:
          type: boolean
        tasks:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              title:
                type: string
              description:
                type: string
              completed:
                type: boolean

  complete_task:
    name: complete_task
    description: Mark a task as completed
    parameters:
      type: object
      required: [task_id]
      properties:
        task_id:
          type: integer
          description: Task ID to mark complete
    returns:
      type: object
      properties:
        success:
          type: boolean
        task:
          type: object
          properties:
            id:
              type: integer
            completed:
              type: boolean

  update_task:
    name: update_task
    description: Update task title and/or description
    parameters:
      type: object
      required: [task_id]
      properties:
        task_id:
          type: integer
        title:
          type: string
          minLength: 1
          maxLength: 200
        description:
          type: string
          maxLength: 1000
    returns:
      type: object
      properties:
        success:
          type: boolean
        task:
          type: object

  delete_task:
    name: delete_task
    description: Delete a task permanently
    parameters:
      type: object
      required: [task_id]
      properties:
        task_id:
          type: integer
    returns:
      type: object
      properties:
        success:
          type: boolean
        message:
          type: string
```

**request-flow.md** - Sequence diagrams for request cycle
```markdown
# Request Flow Sequence Diagrams

## Normal Flow: User Creates Task

```
User → Frontend: Send "add task buy groceries"
Frontend → Backend: POST /api/{user_id}/chat {message: "add task buy groceries"}
Backend → JWT Middleware: Verify token
Backend → Database: SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at
Database → Backend: [] (empty history for first message)
Backend → Database: BEGIN TRANSACTION
Backend → Database: INSERT INTO messages (role="user", content="add task buy groceries")
Backend → Database: COMMIT
Backend → Agent Service: Process message with history
Agent Service → MCP Tools: add_task(title="buy groceries")
MCP Tools → Database: INSERT INTO tasks (title="buy groceries", user_id=?, completed=false)
Database → MCP Tools: {id: 1, title: "buy groceries", completed: false}
MCP Tools → Agent Service: Tool result
Agent Service → Backend: "I've added 'buy groceries' to your tasks"
Backend → Database: BEGIN TRANSACTION
Backend → Database: INSERT INTO messages (role="assistant", content="...", tool_calls=[...])
Backend → Database: COMMIT
Backend → Frontend: {response: "I've added...", tool_calls: [{tool_name: "add_task", ...}]}
Frontend → User: Display AI response with tool confirmation
```

## Flow: Server Restart Survival

```
User: Has 10 messages in conversation
Server: Restarted (memory cleared)
User → Frontend: Send "mark task 1 as done"
Frontend → Backend: POST /api/{user_id}/chat {message: "mark task 1 as done"}
Backend → Database: SELECT * FROM messages WHERE conversation_id = ? (reconstructs context)
Database → Backend: [10 previous messages]
Backend → Agent: Process with full history
Agent → MCP: complete_task(task_id=1)
[Rest of flow continues normally]
```
```

### 1.3 Quickstart Guide (`quickstart.md`)

Create developer onboarding guide:

```markdown
# Conversation Flow Quickstart Guide

## Prerequisites

- Python 3.12+ installed
- Node.js 20+ installed
- PostgreSQL database (Neon recommended)
- OpenAI API key
- Better Auth configured

## Backend Setup

1. **Install dependencies**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your values:
   # DATABASE_URL=postgresql://...
   # OPENAI_API_KEY=sk-...
   # BETTER_AUTH_SECRET=your-secret-key-min-32-chars
   ```

3. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

4. **Start backend server**
   ```bash
   uvicorn src.main:app --reload --port 8000
   ```

5. **Verify backend**
   - Open http://localhost:8000/docs for API documentation
   - Check `/health` endpoint returns `{"status": "healthy"}`

## Frontend Setup

1. **Install dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env.local
   # Edit .env.local:
   # NEXT_PUBLIC_API_URL=http://localhost:8000
   # NEXT_PUBLIC_BETTER_AUTH_URL=http://localhost:3000
   ```

3. **Start frontend dev server**
   ```bash
   npm run dev
   ```

4. **Access chat interface**
   - Open http://localhost:3000/chat
   - Login/signup first at http://localhost:3000/login

## Testing the Chat Flow

1. **Create a task via chat**
   - Send: "add task buy groceries"
   - Expected: AI responds "I've added 'buy groceries' to your tasks" with tool confirmation

2. **View tasks**
   - Send: "show my tasks"
   - Expected: AI lists all tasks with completion status

3. **Complete a task**
   - Send: "mark task 1 as done"
   - Expected: AI confirms task completion

4. **Test restart survival**
   - Send a few messages to create conversation history
   - Restart backend server (Ctrl+C, then `uvicorn src.main:app --reload`)
   - Send another message
   - Expected: AI remembers full conversation context

## Development Workflow

1. **Make code changes**
2. **Run tests**: `cd backend && pytest` or `cd frontend && npm test`
3. **Check API docs**: http://localhost:8000/docs
4. **Verify database**: Use Neon dashboard or `psql` to inspect tables
5. **Test manually**: Use chat interface at /chat

## Troubleshooting

**Issue**: "Database connection failed"
- **Fix**: Verify DATABASE_URL in .env, check Neon console

**Issue**: "JWT validation failed"
- **Fix**: Ensure BETTER_AUTH_SECRET is same in frontend and backend .env

**Issue**: "Agent not responding"
- **Fix**: Check OPENAI_API_KEY is valid, has credits

**Issue**: "Tool calls not showing"
- **Fix**: Check browser console for errors, verify tool_calls in message object

## Next Steps

- Read `data-model.md` for entity relationships
- Read `contracts/chat-api.yaml` for API details
- Run `pytest tests/integration/test_conversation_state.py` for stateless flow tests
```

### Deliverables

- `specs/005-conversation-flow/data-model.md` - Complete entity specifications with relationships
- `specs/005-conversation-flow/contracts/chat-api.yaml` - OpenAPI specification
- `specs/005-conversation-flow/contracts/mcp-tools.yaml` - MCP tool schemas
- `specs/005-conversation-flow/contracts/request-flow.md` - Sequence diagrams
- `specs/005-conversation-flow/quickstart.md` - Developer onboarding guide

### Acceptance Criteria

- [ ] Data model defines all 4 entities with fields, indexes, constraints
- [ ] Entity relationships documented (one-to-many, cascade rules)
- [ ] Migration strategy defined (Alembic)
- [ ] OpenAPI spec validates successfully (use `swagger-cli validate`)
- [ ] MCP tool schemas use JSON Schema format
- [ ] Sequence diagrams show normal flow and restart survival flow
- [ ] Quickstart guide tested by fresh developer (step-by-step works)
- [ ] All contracts reviewed against specifications (001-005)

## Phase 2: Implementation Tasks

**NOTE**: This phase is executed via `/sp.tasks` command, which creates `tasks.md` with testable, dependency-ordered tasks. This plan does NOT include tasks - they are generated separately.

The `tasks.md` file will include:
- Database migration creation and execution
- Model implementations (conversation, message)
- Service implementations (agent, mcp_server, conversation)
- API route implementation (chat endpoint)
- Frontend chat interface components
- ChatKit integration
- Integration tests for stateless flow
- Unit tests for agent logic and MCP tools
- End-to-end tests for full request cycle

**Transition to Phase 2**: Run `/sp.tasks` after Phase 1 is complete and approved.

## Definition of Done

This feature is **DONE** when:

### Code Complete
- [ ] All database migrations applied successfully
- [ ] All 4 models implemented (user, task, conversation, message) with relationships
- [ ] All 3 services implemented (agent, mcp_server, conversation) with tests
- [ ] Chat API endpoint (`/api/{user_id}/chat`) working with authentication
- [ ] Frontend chat interface (`/chat`) displaying messages and tool_calls
- [ ] MCP server registered with all 5 tools
- [ ] Agent correctly interpreting intents and invoking tools

### Testing Complete
- [ ] Unit tests: Agent service (prompt engineering, tool selection)
- [ ] Unit tests: MCP tools (all 5 tools with edge cases)
- [ ] Integration tests: Stateless conversation flow (request cycle)
- [ ] Integration tests: Restart survival (conversation history reconstruction)
- [ ] Contract tests: Chat API matches OpenAPI spec
- [ ] Contract tests: MCP tool outputs match schemas
- [ ] Frontend tests: Chat components render and handle user input
- [ ] E2E tests: Full user journey (create → list → complete task)

### Documentation Complete
- [ ] `data-model.md` reviewed and matches implementation
- [ ] `contracts/*.yaml` validated and current
- [ ] `quickstart.md` tested by fresh developer
- [ ] Code comments explain request flow and stateless design
- [ ] README.md updated with chat feature

### Quality Checks
- [ ] All tests passing (`pytest` and `npm test`)
- [ ] No linting errors (`ruff check` and `eslint`)
- [ ] No type errors (`mypy` and `tsc --noEmit`)
- [ ] Performance benchmarks met (<3s p95 latency, <200ms history fetch)
- [ ] Security scan passes (no SQL injection, XSS, or auth bypasses)
- [ ] Constitution compliance verified (all 9 principles)

### Deployment Ready
- [ ] Environment variables documented (`.env.example` updated)
- [ ] Migration rollback procedure documented
- [ ] Error monitoring configured (logs, metrics)
- [ ] Health checks passing (`/health/ready` includes database connectivity)
- [ ] Frontend deployed to Vercel and backend to Render (or equivalent)
- [ ] Production tested with smoke tests

## Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| **Agent intent accuracy < 95%** | Medium | High | Invest in Phase 0 research on prompt engineering, create comprehensive few-shot examples, A/B test prompt variations |
| **Conversation history fetch > 200ms** | Low | Medium | Optimize database queries (add composite index on conversation_id + created_at), consider pagination for 1000+ messages |
| **OpenAI API rate limits** | Low | Medium | Implement exponential backoff, cache common responses, monitor usage metrics |
| **ChatKit integration complexity** | Medium | Low | Complete Phase 0 research early, create proof-of-concept before full implementation |
| **MCP tool schema mismatch** | Low | Medium | Validate schemas against OpenAI specification, write contract tests for each tool |
| **Database migration failures** | Low | High | Test migrations on development database first, create rollback procedures, backup before production migration |
| **JWT token expiration during request** | Low | Low | Set reasonable token expiration (24 hours), implement refresh token flow if needed |

## Follow-up Work

**Post-MVP enhancements** (not in scope for this feature):
- Streaming responses (currently non-streaming for simplicity)
- Multi-conversation support (currently one conversation per user)
- File attachments in messages
- Voice input/output
- Task priorities and due dates
- Task categories and tags
- Shared/collaborative tasks
- Task reminders and notifications
- Analytics dashboard (task completion rates, agent accuracy metrics)

## Architectural Decision Records

This plan identified the following significant architectural decisions that should be documented as ADRs:

1. **Single Conversation Per User**
   - Decision: One conversation per user (not multiple conversations)
   - Rationale: Simplicity for MVP, reduces complexity, matches core todo use case
   - Trade-offs: Less flexibility vs simpler data model and queries
   - **Action**: Run `/sp.adr single-conversation-per-user` to document

2. **Non-Streaming Chat API**
   - Decision: Use non-streaming responses (wait for full response before returning)
   - Rationale: Simpler implementation, easier to store in database, matches stateless requirement
   - Trade-offs: Slower perceived latency vs simpler architecture and transaction safety
   - **Action**: Run `/sp.adr non-streaming-chat-api` to document

3. **JSONB for tool_calls Storage**
   - Decision: Store tool_calls as JSONB in messages table
   - Rationale: Flexible schema, supports any tool structure, queryable
   - Trade-offs: No type safety at DB level vs schema flexibility
   - **Action**: Run `/sp.adr jsonb-tool-calls-storage` to document

**Note**: ADRs should be created after plan approval but before implementation begins. Use `/sp.adr <title>` to create each ADR.

## References

- **Project Constitution**: `.specify/memory/constitution.md`
- **Feature Specifications**:
  - `specs/001-agent-behavior/spec.md` - AI agent intent interpretation
  - `specs/002-mcp-tools/spec.md` - MCP tool definitions
  - `specs/003-chat-api/spec.md` - Chat API endpoint
  - `specs/004-database-schema/spec.md` - Database entity definitions
  - `specs/005-conversation-flow/spec.md` - Stateless request flow
- **Existing Code**:
  - Backend: `backend/src/models/task.py`, `backend/src/api/routes/tasks.py`
  - Frontend: `frontend/src/lib/api.ts`, `frontend/src/components/task/`
- **External Documentation**:
  - OpenAI Agents SDK: https://platform.openai.com/docs/agents
  - Official MCP SDK: https://modelcontextprotocol.io/docs
  - ChatKit: https://chatkit.ai/docs
  - FastAPI: https://fastapi.tiangolo.com/
  - SQLModel: https://sqlmodel.tiangolo.com/
