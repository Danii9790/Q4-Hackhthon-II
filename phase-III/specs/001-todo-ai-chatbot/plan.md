# Implementation Plan: Todo AI Chatbot

**Branch**: `001-todo-ai-chatbot` | **Date**: 2026-01-31 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-todo-ai-chatbot/spec.md`

## Summary

Build an AI-powered chatbot enabling natural language todo task management. The system uses a stateless architecture where conversation history and task data are persisted in Neon PostgreSQL. Users interact through OpenAI ChatKit on the frontend, sending messages to a FastAPI backend that executes OpenAI Agents SDK with MCP tools for task operations (create, read, update, delete, complete). All AI actions are exposed through stateless MCP tools following the Model Context Protocol standard.

## Technical Context

**Language/Version**: Python 3.11+ (backend), TypeScript/JavaScript (frontend)
**Primary Dependencies**:
- Backend: FastAPI 0.104+, SQLModel 0.0.14, OpenAI Agents SDK, Official MCP SDK, asyncio, psycopg3
- Frontend: OpenAI ChatKit, React 18+, Next.js 14+ (if applicable)
- Database: Neon Serverless PostgreSQL
- Auth: Better Auth with JWT tokens

**Storage**: Neon Serverless PostgreSQL (managed PostgreSQL with connection pooling)
**Testing**: pytest (backend), React Testing Library / Playwright (frontend)
**Target Platform**: Linux server (backend), Web browser (frontend)
**Project Type**: Web application (backend + frontend)
**Performance Goals**:
- Chat endpoint: <5s p95 latency for full agent execution with tool calls
- Concurrent conversations: 100 simultaneous users without degradation
- Database queries: <500ms p95 for all operations
- Agent inference: <3s average response time

**Constraints**:
- Stateless architecture: NO in-memory session state
- All conversation state must be database-backed
- MCP tools must be stateless and database-backed
- Tool execution timeout: 30 seconds maximum
- Message size limit: 10,000 characters per message

**Scale/Scope**:
- Users: Up to 1,000 authenticated users
- Conversations: Multiple independent conversations per user
- Messages per conversation: Up to 500 messages
- Tasks per user: Up to 1,000 tasks
- Message retention: All messages persisted indefinitely

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Design Gates (Phase 0 Entry)

- ✅ **I. Stateless Architecture (NON-NEGOTIABLE)**: Plan will enforce stateless endpoint design with database-persisted conversation state
- ✅ **II. MCP Tool Standardization**: All task operations will be exposed through MCP tools using Official MCP SDK
- ✅ **III. Conversation Persistence**: All messages will be persisted to database before client response
- ✅ **IV. Natural Language First**: OpenAI Agents SDK will handle intent interpretation and tool selection
- ✅ **V. Error Transparency**: Error handling strategy will include user-friendly messages and detailed logging
- ✅ **VI. Incremental MVP Delivery**: User stories are prioritized P1-P3; each story is independently testable

**Gate Status**: PASS - All constitution principles addressed in technical approach

### Post-Design Gates (Phase 1 Completion)

*To be verified after design phase*

- [ ] Stateless endpoint implementation verified
- [ ] MCP tools independently tested
- [ ] Database persistence confirmed
- [ ] Error propagation validated
- [ ] P1 user story independently functional

## Project Structure

### Documentation (this feature)

```text
specs/001-todo-ai-chatbot/
├── spec.md              # Feature specification (complete)
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── chat-api.yaml    # OpenAPI spec for chat endpoint
│   └── mcp-tools.yaml   # MCP tool specifications
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
# Web application structure (backend + frontend)
backend/
├── src/
│   ├── models/
│   │   ├── __init__.py
│   │   ├── task.py          # Task SQLModel
│   │   ├── conversation.py  # Conversation SQLModel
│   │   └── message.py       # Message SQLModel
│   ├── api/
│   │   ├── __init__.py
│   │   ├── chat.py          # Chat endpoint
│   │   └── deps.py          # Dependencies (auth, DB session)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── agent.py         # OpenAI Agents SDK integration
│   │   └── mcp_server.py    # MCP server with tools
│   ├── mcp_tools/
│   │   ├── __init__.py
│   │   ├── base.py          # Base MCP tool class
│   │   ├── add_task.py      # add_task tool
│   │   ├── list_tasks.py    # list_tasks tool
│   │   ├── complete_task.py # complete_task tool
│   │   ├── delete_task.py   # delete_task tool
│   │   └── update_task.py   # update_task tool
│   ├── db/
│   │   ├── __init__.py
│   │   ├── session.py       # Database session management
│   │   └── init_db.py       # DB initialization
│   └── main.py              # FastAPI application entry
├── tests/
│   ├── contract/
│   │   ├── test_chat_api.py      # Chat endpoint contract tests
│   │   └── test_mcp_tools.py     # MCP tool contract tests
│   ├── integration/
│   │   ├── test_chat_flow.py     # End-to-end chat flow tests
│   │   └── test_agent_tools.py   # Agent + MCP integration tests
│   └── unit/
│       ├── test_models.py        # Model tests
│       ├── test_mcp_tools.py     # Individual tool tests
│       └── test_agent.py         # Agent logic tests
├── alembic/                  # Database migrations
│   ├── versions/
│   └── env.py
├── alembic.ini
├── pyproject.toml
└── .env.example

frontend/
├── src/
│   ├── components/
│   │   ├── ChatInterface.tsx    # Main chat UI component
│   │   ├── MessageList.tsx      # Message display
│   │   ├── MessageInput.tsx     # Input field
│   │   └── TypingIndicator.tsx  # Loading state
│   ├── services/
│   │   └── chatService.ts       # Chat API client
│   ├── hooks/
│   │   └── useChat.ts           # Chat state management hook
│   ├── lib/
│   │   └── chatkit.ts           # ChatKit configuration
│   └── pages/
│       └── chat.tsx             # Chat page
├── tests/
│   ├── unit/
│   │   └── chatService.test.ts
│   └── integration/
│       └── chatFlow.test.tsx
├── package.json
└── .env.example
```

**Structure Decision**: Web application structure selected because the feature requires both backend API (FastAPI) and frontend client (ChatKit). Backend handles AI agent logic, MCP tool execution, and database operations. Frontend provides chat UI using OpenAI ChatKit for conversational interface. The separation enables independent deployment and scaling.

## Complexity Tracking

> **No constitution violations requiring justification**

All design decisions align with constitution principles:
- Stateless architecture enforced through database-backed sessions
- MCP tools provide standardized interface for AI operations
- Conversation persistence ensures no data loss
- Natural language understanding delegated to OpenAI Agents SDK
- Error transparency maintained through structured error responses
- MVP delivery enabled through prioritized user stories

## Phase 0: Research & Decisions

### Research Topics

1. **OpenAI Agents SDK Integration Patterns**
   - How to integrate Agents SDK with FastAPI async endpoints
   - Best practices for tool registration and agent configuration
   - Error handling for agent failures and timeouts
   - Conversation history formatting for agent context

2. **MCP Server Implementation with Official SDK**
   - Official MCP SDK patterns for tool registration
   - Tool parameter validation and type checking
   - Error propagation from tools to agents
   - Tool discovery and metadata format

3. **ChatKit Frontend Integration**
   - ChatKit configuration for FastAPI backend
   - Authentication token handling
   - Message streaming vs complete response handling
   - Error display and retry mechanisms

4. **Database Schema Design for Conversation State**
   - Optimal table structure for conversations, messages, tasks
   - Indexing strategy for user_id and conversation_id queries
   - Cascade delete behavior for data cleanup
   - Migration strategy with Alembic

5. **Stateless Conversation Context Management**
   - Fetching conversation history on each request
   - Efficient serialization of messages for agent input
   - Pagination strategy for long conversations
   - Context window management for large histories

### Research Artifacts

See [research.md](./research.md) for detailed findings and decisions.

## Phase 1: Design & Contracts

### Data Model

See [data-model.md](./data-model.md) for detailed schema definitions.

**Entity Overview**:
- **Task**: Todo items with title, description, completion status
- **Conversation**: Chat sessions linking messages to users
- **Message**: Individual messages with role (user/assistant) and content
- **User**: Authenticated users (managed by Better Auth)

### API Contracts

See [contracts/](./contracts/) directory for OpenAPI specifications.

**Primary Endpoint**:
- `POST /api/{user_id}/chat` - Stateless chat endpoint

**MCP Tools** (exposed through MCP server):
- `add_task` - Create new task
- `list_tasks` - Retrieve tasks with optional status filter
- `complete_task` - Mark task as complete
- `update_task` - Modify task details
- `delete_task` - Remove task

### Quick Start Guide

See [quickstart.md](./quickstart.md) for:
- Environment setup
- Database initialization
- Backend server startup
- Frontend development server
- Testing procedures

## Implementation Phases

### Phase 0: Research (In Progress)

**Deliverables**:
- [x] research.md with technical decisions
- [ ] Technology selection confirmation
- [ ] Architecture diagrams

**Completion Criteria**: All NEEDS CLARIFICATION items resolved, design decisions documented

### Phase 1: Design (Current)

**Deliverables**:
- [ ] data-model.md with complete schema
- [ ] contracts/ with OpenAPI specs
- [ ] quickstart.md with setup instructions
- [ ] Agent context file updated

**Completion Criteria**: All data models defined, API contracts specified, constitution re-check passes

### Phase 2: Task Breakdown (Next)

**Command**: `/sp.tasks`

**Deliverables**:
- [ ] tasks.md organized by user story priority
- [ ] Testable tasks with acceptance criteria
- [ ] Dependency tracking between tasks

**Completion Criteria**: Each P1 user story broken into independently implementable tasks

## Architectural Decisions

### Decision 1: Stateless Chat Endpoint

**Choice**: Chat endpoint fetches conversation history from database on each request, reconstructs full context, executes agent, persists new messages, returns response.

**Rationale**:
- Enables horizontal scaling without session affinity
- Server restarts don't lose conversation state
- Simplifies deployment and operations
- Aligns with constitution principle I (NON-NEGOTIABLE)

**Alternatives Considered**:
- In-memory session storage: Rejected due to statefulness and scaling limitations
- Redis cache for sessions: Rejected due to added complexity and constitution requirement for database persistence

### Decision 2: MCP Tools for All AI Operations

**Choice**: Expose all task CRUD operations through MCP tools using Official MCP SDK. OpenAI Agents SDK calls these tools based on natural language interpretation.

**Rationale**:
- MCP provides standardized contract between AI and application logic
- Tools are stateless and self-describing
- Enables agent to chain multiple operations in single turn
- Aligns with constitution principle II

**Alternatives Considered**:
- Direct function calls from agent: Rejected due to lack of standardization
- REST API endpoints for agent: Rejected due to higher latency and complexity

### Decision 3: Database-Backed Conversation History

**Choice**: Every user message and assistant response persisted to database before returning to client. Chat endpoint queries full history on each request.

**Rationale**:
- Provides audit trail and debugging capability
- Enables conversation resumption after interruptions
- Supports future analytics features
- Aligns with constitution principle III

**Alternatives Considered**:
- Hybrid memory + disk cache: Rejected due to complexity and data loss risk
- Session-only storage: Rejected due to constitution requirement

### Decision 4: OpenAI Agents SDK for Intent Interpretation

**Choice**: Use OpenAI Agents SDK to interpret natural language messages and select appropriate MCP tools.

**Rationale**:
- Delegates NLP complexity to specialized framework
- Provides built-in tool orchestration
- Maintains conversation context automatically
- Aligns with constitution principle IV

**Alternatives Considered**:
- Custom intent classification: Rejected due to complexity and maintenance burden
- Rule-based parsing: Rejected due to poor UX for natural language

### Decision 5: FastAPI Async Backend

**Choice**: Python FastAPI with async/await for backend API and agent execution.

**Rationale**:
- Async operations prevent blocking during agent inference
- Native OpenAPI documentation generation
- Type safety with Pydantic models
- Excellent ecosystem for AI/ML integrations

**Alternatives Considered**:
- Express.js (Node.js): Rejected due to weaker Python AI ecosystem integration
- Django: Rejected due to synchronous request handling and heavier weight

## Risk Analysis

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| OpenAI API rate limits | Medium | High | Implement exponential backoff, queue requests |
| Agent hallucination/incorrect tool use | Medium | Medium | Comprehensive testing, clear tool descriptions |
| Database connection pool exhaustion | Low | High | Connection pooling, max connections limit |
| MCP SDK integration complexity | Medium | Medium | Prototype early, reference official examples |
| ChatKit frontend limitations | Low | Medium | Evaluate alternatives during prototyping |

### Operational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Slow agent inference affecting UX | Medium | High | Set appropriate timeouts, implement streaming responses |
| Database query performance degradation | Low | High | Index user_id and conversation_id, query optimization |
| Authentication token expiration mid-conversation | Medium | Medium | Token refresh logic, graceful re-auth prompt |

## Next Steps

1. **Complete Phase 0**: Finalize research.md with all technical decisions
2. **Execute Phase 1**: Generate data-model.md, contracts/, quickstart.md
3. **Update Agent Context**: Run `update-agent-context.sh` to inject technology knowledge
4. **Constitution Re-Check**: Verify design decisions align with all principles
5. **Proceed to Phase 2**: Run `/sp.tasks` to generate actionable task breakdown

## Dependencies

### External Dependencies
- OpenAI API key (GPT-4 for agent inference)
- Neon PostgreSQL database connection string
- Better Auth JWT secret
- Domain for frontend deployment (if applicable)

### Internal Dependencies
- Existing Better Auth configuration (from previous phases)
- Existing Task model and database schema (from previous phases)
- Existing user authentication flow

## References

- [Feature Specification](./spec.md)
- [Project Constitution](../../.specify/memory/constitution.md)
- [OpenAI Agents SDK Documentation](https://platform.openai.com/docs/agents)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLModel Documentation](https://sqlmodel.tiangolo.com/)
- [ChatKit Documentation](https://chatkit.openai.com/)

---

**Plan Version**: 1.0.0 | **Last Updated**: 2026-01-31
