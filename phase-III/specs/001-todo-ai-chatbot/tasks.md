# Tasks: Todo AI Chatbot

**Input**: Design documents from `/specs/001-todo-ai-chatbot/`
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/, research.md

**Tests**: Tests are OPTIONAL and not included unless explicitly requested.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, etc.)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `backend/src/`
- **Frontend**: `frontend/src/`
- Tests: `backend/tests/`, `frontend/tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create backend directory structure per plan (backend/src/{models,api,services,mcp_tools,db}, backend/tests/{contract,integration,unit}, backend/alembic)
- [X] T002 Create frontend directory structure per plan (frontend/src/{components,services,hooks,lib,pages}, frontend/tests/{unit,integration})
- [X] T003 [P] Initialize Python project with pyproject.toml including FastAPI 0.104+, SQLModel 0.0.14, OpenAI Agents SDK, MCP SDK, pytest dependencies
- [X] T004 [P] Initialize Node.js project with package.json including @openai/chatkit, React 18+, Next.js 14+, Better Auth
- [X] T005 [P] Create backend/.env.example with DATABASE_URL, OPENAI_API_KEY, BETTER_AUTH_SECRET placeholders
- [X] T006 [P] Create frontend/.env.example with VITE_API_URL, VITE_BETTER_AUTH_URL placeholders
- [X] T007 [P] Configure Alembic for database migrations (alembic.ini, alembic/env.py, alembic/versions/ directory)
- [X] T008 [P] Setup pytest configuration in backend/pyproject.toml with async support and test discovery
- [X] T009 [P] Setup ESLint and Prettier configuration for frontend code quality

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Database & Models

- [X] T010 Create Conversation SQLModel in backend/src/models/conversation.py with id, user_id, created_at, updated_at fields
- [X] T011 [P] Create Message SQLModel in backend/src/models/message.py with id, conversation_id, user_id, role, content, created_at fields
- [X] T012 [P] Create Task SQLModel in backend/src/models/task.py with id, user_id, title, description, completed, created_at, updated_at fields (may already exist from previous phases)
- [X] T013 Create backend/src/models/__init__.py exporting all models
- [X] T014 Create Alembic migration for conversations and messages tables in backend/alembic/versions/001_create_conversation_tables.py

### Database Connection

- [X] T015 Implement database session management in backend/src/db/session.py with engine configuration and get_session dependency
- [X] T016 Create database initialization in backend/src/db/init_db.py for table creation and connection verification

### API Infrastructure

- [X] T017 Create FastAPI application in backend/src/main.py with CORS middleware, OpenAPI documentation, and lifespan management
- [X] T018 [P] Create authentication dependency in backend/src/api/deps.py extracting user_id from JWT token
- [X] T019 [P] Create error handlers in backend/src/main.py for 401, 403, 404, 500 status codes with standardized error response format

### MCP Server Foundation

- [X] T020 Create MCP server instance in backend/src/services/mcp_server.py using Official MCP SDK
- [X] T021 Create base MCP tool class in backend/src/mcp_tools/base.py with common error handling and user_id validation

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 6 - Continuous Conversation Context (Priority: P1) 🎯 MVP

**Goal**: Enable persistent conversation memory across multiple message exchanges

**Independent Test**: Send a sequence of related messages and verify the system maintains context and references previous exchanges correctly. After server restart, conversation history is preserved from database.

**Rationale for Priority**: This foundational infrastructure enables all other stories. Without conversation memory, each message is isolated. Implementing this first ensures the conversation persistence pattern is established.

### Implementation for Conversation Context

- [X] T022 [US6] Implement conversation creation/retrieval logic in backend/src/api/chat.py helper functions (get_or_create_conversation, fetch_conversation_history)
- [X] T023 [US6] Implement message persistence in backend/src/api/chat.py (save_user_message, save_assistant_message)
- [X] T024 [US6] Create conversation history formatting in backend/src/api/chat.py (format_messages_for_agent, truncate_history_to_max)
- [X] T025 [US6] Test stateless conversation reconstruction in backend/tests/integration/test_conversation_state.py (verify context persists after server restart)

**Checkpoint**: Conversation context infrastructure complete - can now support agent interactions

---

## Phase 4: User Story 1 - Natural Language Task Creation (Priority: P1) 🎯 MVP

**Goal**: Users can create tasks by sending natural language messages like "Add a task to buy groceries"

**Independent Test**: Send a single natural language message and verify a task is created with correct details extracted. System responds with friendly confirmation.

### MCP Tool: add_task

- [X] T026 [P] [US1] Implement add_task MCP tool in backend/src/mcp_tools/add_task.py with user_id, title, description parameters and database insertion
- [X] T027 [P] [US1] Implement add_task input validation in backend/src/mcp_tools/add_task.py (title max 500 chars, non-empty; optional description max 5000 chars)
- [X] T028 [P] [US1] Register add_task tool with MCP server in backend/src/services/mcp_server.py using @mcp_server.tool() decorator with docstring for AI understanding

### OpenAI Agent Integration

- [X] T029 [US1] Create agent service in backend/src/services/agent.py with OpenAI Agents SDK initialization
- [X] T030 [US1] Implement agent configuration in backend/src/services/agent.py with instructions for task creation intent interpretation
- [X] T031 [US1] Implement agent executor in backend/src/services/agent.py (execute_agent function) with async runner, conversation context, and tool registration
- [X] T032 [US1] Add OpenAI adapter in backend/src/services/agent.py to convert MCP tools to OpenAI function format

### Chat Endpoint

- [X] T033 [US1] Implement POST /api/{user_id}/chat endpoint in backend/src/api/chat.py with conversation_id and message request body
- [X] T034 [US1] Integrate agent executor in chat endpoint to process user message and invoke add_task tool
- [X] T035 [US1] Implement response formatting in chat endpoint returning conversation_id, assistant response, and tool_calls list
- [X] T036 [US1] Add error handling in chat endpoint for agent failures and tool execution errors with user-friendly messages

**Checkpoint**: At this point, users can create tasks via natural language - core value proposition delivered

---

## Phase 5: User Story 2 - Natural Language Task Viewing (Priority: P1) 🎯 MVP

**Goal**: Users can view their tasks by asking "Show my tasks" or "What's left to do?"

**Independent Test**: Create tasks via US1, then ask to view them and verify correct tasks are displayed based on query type (all, pending, completed).

### MCP Tool: list_tasks

- [X] T037 [P] [US2] Implement list_tasks MCP tool in backend/src/mcp_tools/list_tasks.py with user_id and status ("all"|"pending"|"completed") parameters
- [X] T038 [P] [US2] Implement task filtering logic in backend/src/mcp_tools/list_tasks.py with database queries by user_id and completed status
- [X] T039 [P] [US2] Register list_tasks tool with MCP server in backend/src/services/mcp_server.py with docstring for AI understanding

### Agent Configuration Update

- [X] T040 [US2] Update agent instructions in backend/src/services/agent.py to include list_tasks intent interpretation patterns ("show tasks", "what's pending", etc.)
- [X] T041 [US2] Register list_tasks tool with agent in backend/src/services/agent.py for automatic invocation

### Response Formatting

- [X] T042 [US2] Implement conversational response formatting in backend/src/services/agent.py for task lists (not raw data dumps, readable format for 25+ tasks)
- [X] T043 [US2] Add empty task list handling in backend/src/services/agent.py with friendly "no tasks yet" message

**Checkpoint**: At this point, users have full CRUD-lite (create + view) - MVP is functionally complete for basic todo management

---

## Phase 6: User Story 3 - Natural Language Task Completion (Priority: P2)

**Goal**: Users can mark tasks as done by saying "I finished buying groceries" or "Mark task 3 as done"

**Independent Test**: Create tasks, then complete them via natural language and verify status changes correctly in database.

### MCP Tool: complete_task

- [X] T044 [P] [US3] Implement complete_task MCP tool in backend/src/mcp_tools/complete_task.py with user_id and task_id parameters
- [X] T045 [P] [US3] Implement task completion logic in backend/src/mcp_tools/complete_task.py with database update (completed=True, updated_at=now)
- [X] T046 [P] [US3] Add task ownership validation in backend/src/mcp_tools/complete_task.py (verify task belongs to user_id)
- [X] T047 [P] [US3] Register complete_task tool with MCP server in backend/src/services/mcp_server.py with docstring

### Agent Configuration Update

- [X] T048 [US3] Update agent instructions in backend/src/services/agent.py to include completion intent patterns ("finished", "done", "complete")
- [X] T049 [US3] Register complete_task tool with agent in backend/src/services/agent.py
- [X] T050 [US3] Implement ambiguous task reference handling in backend/src/services/agent.py to ask clarification when multiple similar tasks exist

**Checkpoint**: At this point, full task lifecycle works (create → view → complete)

---

## Phase 7: User Story 4 - Natural Language Task Modification (Priority: P2)

**Goal**: Users can update task details by saying "Change the dentist task to Tuesday" or "Update task 2 title to..."

**Independent Test**: Create tasks, then modify them via natural language and verify changes are persisted correctly.

### MCP Tool: update_task

- [X] T051 [P] [US4] Implement update_task MCP tool in backend/src/mcp_tools/update_task.py with user_id, task_id, optional title, optional description parameters
- [X] T052 [P] [US4] Implement task update logic in backend/src/mcp_tools/update_task.py with database update and updated_at refresh
- [X] T053 [P] [US4] Add validation in backend/src/mcp_tools/update_task.py (at least one of title or description provided, title max 500 chars)
- [X] T054 [P] [US4] Register update_task tool with MCP server in backend/src/services/mcp_server.py with docstring

### Agent Configuration Update

- [X] T055 [US4] Update agent instructions in backend/src/services/agent.py to include modification intent patterns ("change", "update", "modify")
- [X] T056 [US4] Register update_task tool with agent in backend/src/services/agent.py
- [X] T057 [US4] Implement confirmation response in backend/src/services/agent.py summarizing what was changed

**Checkpoint**: At this point, tasks can be modified after creation without deletion

---

## Phase 8: User Story 5 - Natural Language Task Deletion (Priority: P3)

**Goal**: Users can delete tasks by saying "Delete the grocery task" or "Remove task 4"

**Independent Test**: Create tasks, then delete them via natural language and verify they're removed from system.

### MCP Tool: delete_task

- [X] T058 [P] [US5] Implement delete_task MCP tool in backend/src/mcp_tools/delete_task.py with user_id and task_id parameters
- [X] T059 [P] [US5] Implement task deletion logic in backend/src/mcp_tools/delete_task.py with database DELETE operation
- [X] T060 [P] [US5] Add task ownership validation in backend/src/mcp_tools/delete_task.py (verify task belongs to user before deletion)
- [X] T061 [P] [US5] Register delete_task tool with MCP server in backend/src/services/mcp_server.py with docstring

### Agent Configuration Update

- [X] T062 [US5] Update agent instructions in backend/src/services/agent.py to include deletion intent patterns ("delete", "remove")
- [X] T063 [US5] Register delete_task tool with agent in backend/src/services/agent.py
- [X] T064 [US5] Implement confirmation response in backend/src/services/agent.py confirming task was deleted

**Checkpoint**: All CRUD operations now available through natural language

---

## Phase 9: Frontend Implementation (All Stories)

**Goal**: Provide ChatKit-based UI for all backend functionality

**Independent Test**: Full workflow through frontend - send messages, view responses, verify tasks created/modified.

### ChatKit Configuration

- [X] T065 [P] Configure ChatKit in frontend/src/lib/chatkit.ts with REST adapter pointing to VITE_API_URL
- [X] T066 [P] Setup ChatKit domain allowlist in frontend/src/lib/chatkit.ts for todo/task-related tools
- [X] T067 [P] Add error handling in frontend/src/lib/chatkit.ts for network failures and API errors

### Chat Components

- [X] T068 [P] Create ChatInterface component in frontend/src/components/ChatInterface.tsx with useChat hook integration
- [X] T069 [P] Create MessageList component in frontend/src/components/MessageList.tsx displaying user and assistant messages with styling
- [X] T070 [P] Create MessageInput component in frontend/src/components/MessageInput.tsx with send button and disabled state during loading
- [X] T071 [P] Create TypingIndicator component in frontend/src/components/TypingIndicator.tsx showing during agent execution

### Chat Service

- [X] T072 [P] Implement chat service in frontend/src/services/chatService.ts with fetch wrapper for /api/{user_id}/chat endpoint
- [X] T073 [P] Add authentication token handling in frontend/src/services/chatService.ts extracting JWT from Better Auth session
- [X] T074 [P] Implement error display in frontend/src/services/chatService.ts with toast notifications for API errors

### Chat Page

- [X] T075 Create chat page in frontend/src/pages/chat.tsx integrating ChatInterface, MessageList, MessageInput components
- [X] T076 Add Better Auth integration in frontend/src/pages/chat.tsx to get user ID from session

**Checkpoint**: Full-stack application complete - users can interact with AI chatbot through web UI

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

### Error Handling & Logging

- [X] T077 [P] Implement structured logging in backend/src/main.py with request/response logging and error context
- [X] T078 [P] Add database query logging in backend/src/db/session.py for performance monitoring
- [X] T079 [P] Add agent execution logging in backend/src/services/agent.py capturing tool calls and responses

### Performance

- [X] T080 [P] Add database connection pooling configuration in backend/src/db/session.py for Neon PostgreSQL
- [X] T081 [P] Implement conversation history pagination in backend/src/api/chat.py for conversations with 100+ messages
- [X] T082 [P] Add response caching headers in backend/src/api/chat.py for browser caching

### Security Hardening

- [X] T083 [P] Add rate limiting to chat endpoint in backend/src/api/chat.py (max 10 requests per minute per user)
- [X] T084 [P] Implement message length validation in backend/src/api/chat.py (max 10,000 characters)
- [X] T085 [P] Add CORS configuration in backend/src/main.py restricting to frontend domain only

### Documentation

- [X] T086 [P] Create README.md in backend/ with setup instructions, environment variables, and testing guide
- [X] T087 [P] Create README.md in frontend/ with ChatKit setup, environment variables, and development server guide
- [X] T088 [P] Update quickstart.md in specs/001-todo-ai-chatbot/ with any discovered setup issues or corrections

### Validation

- [X] T089 Run all acceptance scenarios from spec.md for each user story and verify pass
- [X] T090 Verify constitution compliance: stateless architecture (no in-memory session state), all conversation state persisted to database
- [X] T091 Test server restart scenario: create conversation, send messages, restart server, verify conversation context preserved

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **Conversation Context (Phase 3)**: Depends on Foundational - BLOCKS all user stories that need agent interaction
- **User Stories (Phases 4-8)**: All depend on Conversation Context completion
  - US1, US2, US3 can then proceed in parallel (if staffed)
  - US4, US5 are lower priority (P2, P3)
- **Frontend (Phase 9)**: Depends on backend user stories being complete (at minimum US1+US2 for MVP)
- **Polish (Phase 10)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US6 (Conversation Context)**: Must be FIRST - foundational for all agent interactions
- **US1 (Task Creation)**: Can start after US6 - No dependencies on other stories
- **US2 (Task Viewing)**: Can start after US6 - Integrates with US1 but independently testable
- **US3 (Task Completion)**: Can start after US6 - Depends on US1 (needs tasks to complete) but independently testable
- **US4 (Task Modification)**: Can start after US6 - Depends on US1 (needs tasks to modify) but independently testable
- **US5 (Task Deletion)**: Can start after US6 - Depends on US1 (needs tasks to delete) but independently testable

### Within Each User Story

- MCP tools must be registered with MCP server before agent configuration
- Agent configuration must be complete before chat endpoint integration
- Chat endpoint implementation integrates all components

### Parallel Opportunities

- **Setup Phase**: T003, T004, T005, T006, T007, T008, T009 can all run in parallel
- **Foundational Phase**: T011, T012 can run in parallel (different model files)
- **US1 (Task Creation)**: T026, T027, T028 can run in parallel (different tool files)
- **US2 (Task Viewing)**: T037, T038, T039 can run in parallel (different tool files)
- **US3 (Task Completion)**: T044, T045, T046, T047 can run in parallel (different tool files)
- **US4 (Task Modification)**: T051, T052, T053, T054 can run in parallel (different tool files)
- **US5 (Task Deletion)**: T058, T059, T060, T061 can run in parallel (different tool files)
- **Frontend Phase**: T065, T066, T067 can run in parallel (ChatKit config)
- **Frontend Phase**: T068, T069, T070, T071 can run in parallel (different components)
- **Frontend Phase**: T072, T073, T074 can run in parallel (service layer)
- **Polish Phase**: Most tasks marked [P] can run in parallel

---

## Parallel Example: User Story 1 (Task Creation)

```bash
# Launch all MCP tool tasks together:
Task: "Implement add_task MCP tool in backend/src/mcp_tools/add_task.py"
Task: "Implement add_task input validation in backend/src/mcp_tools/add_task.py"
Task: "Register add_task tool with MCP server in backend/src/services/mcp_server.py"

# These can execute concurrently as they're in different files or add to same file in non-conflicting ways
```

---

## Implementation Strategy

### MVP First (User Stories 6 + 1 + 2 Only)

1. Complete Phase 1: Setup (T001-T009)
2. Complete Phase 2: Foundational (T010-T021) - CRITICAL
3. Complete Phase 3: US6 Conversation Context (T022-T025)
4. Complete Phase 4: US1 Task Creation (T026-T036)
5. Complete Phase 5: US2 Task Viewing (T037-T043)
6. **STOP and VALIDATE**: Test MVP independently - create and view tasks through natural language
7. Deploy/demo MVP if ready

### Incremental Delivery

1. **Foundation** (Phases 1-2): Infrastructure ready for all stories
2. **MVP Release** (Phases 3-5): US6 + US1 + US2 - Core value delivered
3. **Enhancement 1** (Phase 6): Add US3 - Full task lifecycle
4. **Enhancement 2** (Phase 7): Add US4 - Task modification
5. **Enhancement 3** (Phase 8): Add US5 - Task deletion
6. **Frontend** (Phase 9): Add ChatKit UI after backend validated
7. **Polish** (Phase 10): Performance, security, documentation

Each increment adds value without breaking previous functionality.

### Parallel Team Strategy

With multiple developers after Foundational phase completes:

**Sequential approach** (single developer or small team):
- Complete US6 → US1 → US2 → US3 → US4 → US5 in order
- Each story builds confidence before moving to next

**Parallel approach** (multiple developers):
- Developer A: US6 (Conversation Context) - FOUNDATIONAL, must be first
- After US6 completes:
  - Developer B: US1 (Task Creation)
  - Developer C: US2 (Task Viewing)
  - Developer D: US3 (Task Completion)
- After US1-US3 complete:
  - Developer E: US4 (Task Modification)
  - Developer F: US5 (Task Deletion)
- After all backend stories: Frontend team (Phase 9)

---

## Notes

- Total tasks: 91
- Setup tasks: 9
- Foundational tasks: 12 (CRITICAL - blocks everything)
- User Story 6 (Conversation Context): 4 tasks - PRIORITY 1, must be first
- User Story 1 (Task Creation): 11 tasks - PRIORITY 1 (MVP)
- User Story 2 (Task Viewing): 7 tasks - PRIORITY 1 (MVP)
- User Story 3 (Task Completion): 7 tasks - PRIORITY 2
- User Story 4 (Task Modification): 7 tasks - PRIORITY 2
- User Story 5 (Task Deletion): 7 tasks - PRIORITY 3
- Frontend tasks: 11 tasks
- Polish tasks: 15 tasks
- Parallel opportunities: 45+ tasks marked with [P]

**MVP Scope**: Phases 1-5 (Tasks T001-T043) = 43 tasks
  - Delivers: Conversation context + task creation + task viewing
  - Independent test: Complete workflow from creating to viewing tasks

**Increment 1 (Full CRUD)**: Add Phase 6 (US3) = 7 more tasks
**Increment 2 (Modification)**: Add Phase 7 (US4) = 7 more tasks
**Increment 3 (Deletion)**: Add Phase 8 (US5) = 7 more tasks
**Frontend**: Phase 9 = 11 tasks
**Production Ready**: Phase 10 = 15 tasks
