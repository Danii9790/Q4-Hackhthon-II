# Feature Specification: Database Schema for Todo Management

**Feature Branch**: `004-database-schema`
**Created**: 2026-02-06
**Status**: Draft
**Input**: User description: "Todo AI Chatbot — Database Design"

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

### User Story 1 - Store Task with User Ownership (Priority: P1)

**Why this priority**: This is the fundamental data operation - tasks must be created and permanently linked to their owning user. Without this, the core todo functionality doesn't work.

**Independent Test**: A user creates a task, and the database stores it with a valid user_id foreign key, ensuring the task belongs to that user and cannot be orphaned.

**Acceptance Scenarios**:

1. **Given** a user with ID "user-123" creates a task titled "buy groceries", **When** the task is stored in the database, **Then** the task record has user_id="user-123", title="buy groceries", completed=false, and a valid created_at timestamp
2. **Given** a task is created with a user_id that doesn't exist in the users table, **When** the insert is attempted, **Then** the database rejects the record with a foreign key constraint violation
3. **Given** a user creates 10 tasks over time, **When** all are stored, **Then** each task has the correct user_id, unique task IDs, and timestamps reflecting when they were created

---

### User Story 2 - Retrieve User's Tasks (Priority: P1)

**Why this priority**: Users need to see their tasks. The database must efficiently retrieve all tasks belonging to a specific user while enforcing user isolation.

**Independent Test**: A user requests their task list, and the database returns only tasks with their user_id, with no possibility of accessing other users' tasks.

**Acceptance Scenarios**:

1. **Given** a user has 5 tasks stored in the database (3 incomplete, 2 complete), **When** the database is queried for that user's tasks, **Then** exactly 5 tasks are returned, all with the correct user_id, and showing their completion status accurately
2. **Given** user-123 has tasks and user-456 has different tasks, **When** user-123 queries for tasks, **Then** only user-123's tasks are returned (zero of user-456's tasks)
3. **Given** a user who has never created any tasks, **When** they query for tasks, **Then** an empty result set is returned (no errors, just zero records)

---

### User Story 3 - Update Task Completion Status (Priority: P1)

**Why this priority**: Task completion is the goal of the todo system. The database must reliably update task status while maintaining ownership and referential integrity.

**Independent Test**: A user marks a task as complete, and the database atomically updates the completed field while preserving all other task data and ownership.

**Acceptance Scenarios**:

1. **Given** a task exists with completed=false and user_id="user-123", **When** the task is marked complete, **Then** the database updates completed to true, keeps all other fields unchanged, and the update is atomic (no partial updates)
2. **Given** two users attempt to update the same task simultaneously, **When** both updates execute, **Then** the database handles the concurrency correctly (either one succeeds or the last write wins, but no corruption occurs)
3. **Given** a user attempts to update a task that doesn't exist, **When** the update is executed, **Then** zero rows are affected (no error, but no change made)

---

### User Story 4 - Store Conversation Messages (Priority: P1)

**Why this priority**: Conversations must be persisted for stateless server operation. Every user message and AI response must be stored to maintain context across requests.

**Independent Test**: A user sends a message and receives an AI response, and both messages are stored in the database linked to the user's conversation, with correct roles and timestamps.

**Acceptance Scenarios**:

1. **Given** a user sends "add task buy groceries", **When** the message is processed, **Then** the database stores a message with role="user", content="add task buy groceries", and a valid timestamp
2. **Given** the AI agent responds "I've added 'buy groceries' to your tasks", **When** the response is generated, **Then** the database stores a message with role="assistant", content="I've added 'buy groceries' to your tasks", and the tool_calls that were executed
3. **Given** a user has a 10-message conversation history, **When** a new message is sent, **Then** all 11 messages can be retrieved in chronological order to provide full context

---

### User Story 5 - Retrieve Conversation History (Priority: P1)

**Why this priority**: The stateless server must fetch complete conversation history on each request to maintain context. The database must efficiently return all messages for a user's conversation.

**Independent Test**: A user sends a message after a server restart, and the database returns all previous messages in the conversation so the AI agent has full context.

**Acceptance Scenarios**:

1. **Given** a user has exchanged 20 messages with the AI agent, **When** the database is queried for the conversation history, **Then** all 20 messages are returned in chronological order (oldest to newest)
2. **Given** a server restart occurs (all in-memory state lost), **When** a user sends a new message, **Then** the database fetches the complete conversation history and the AI agent responds with full context of previous messages
3. **Given** a user who has never chatted before, **When** they send their first message, **Then** the database returns an empty message history (no errors, just zero records)

---

### User Story 6 - Enforce Referential Integrity (Priority: P1)

**Why this priority**: Orphaned records (tasks without users, messages without conversations) must be prevented to maintain data integrity and prevent data loss.

**Independent Test**: Any attempt to create records with invalid foreign keys is rejected by the database, ensuring all relationships remain valid.

**Acceptance Scenarios**:

1. **Given** a task is created with a non-existent user_id, **When** the insert is attempted, **Then** the database rejects it with a foreign key constraint violation
2. **Given** a message is stored with a non-existent conversation_id, **When** the insert is attempted, **Then** the database rejects it with a foreign key constraint violation
3. **Given** a user is deleted from the system, **When** cascading deletes are configured, **Then** all of that user's tasks and messages are also deleted (or the deletion is blocked if cascading is not configured)
4. **Given** the database has been in use for months, **When** an integrity check is run, **Then** zero orphaned records exist (all tasks have valid users, all messages have valid conversations)

---

## Functional Requirements

### Requirement 1: User Data Model

**Description**: The system MUST store user information with unique identifiers and support authentication and authorization.

**Acceptance Criteria**:
- Users table stores: unique user_id, email (unique), name, password_hash, created_at timestamp
- user_id is the primary key
- Email field has a unique constraint (no duplicate emails)
- All fields are required except password_hash (can be NULL for OAuth users)
- Timestamps are automatically managed by the database
- User records can be created and queried but never deleted (soft delete if needed later)

**Priority**: MUST

---

### Requirement 2: Task Data Model

**Description**: The system MUST store todo tasks with explicit user ownership and completion tracking.

**Acceptance Criteria**:
- Tasks table stores: task_id (primary key), user_id (foreign key), title, description, completed (boolean), created_at timestamp
- task_id is the primary key (globally unique)
- user_id is a foreign key referencing users table (ON DELETE CASCADE)
- title field is required and has a maximum length
- description field is optional and has a maximum length
- completed field defaults to false
- Foreign key constraint prevents tasks without valid users
- Cascade deletion ensures tasks are deleted when user is deleted

**Priority**: MUST (Non-negotiable - constitution principle)

---

### Requirement 3: Conversation Data Model

**Description**: The system MUST store one conversation per user to maintain chat history.

**Acceptance Criteria**:
- Conversations table stores: conversation_id (primary key), user_id (foreign key), created_at timestamp
- conversation_id is the primary key (globally unique)
- user_id is a foreign key referencing users table (ON DELETE CASCADE)
- Each user has exactly one conversation (one-to-one relationship)
- Conversation is automatically created when user sends first message
- Foreign key constraint prevents conversations without valid users
- Cascade deletion ensures conversation is deleted when user is deleted

**Priority**: MUST

---

### Requirement 4: Message Data Model

**Description**: The system MUST store all conversation messages (both user and assistant) with links to their conversation.

**Acceptance Criteria**:
- Messages table stores: message_id (primary key), conversation_id (foreign key), role (enum: user/assistant), content (text), tool_calls (JSON), created_at timestamp
- message_id is the primary key (globally unique)
- conversation_id is a foreign key referencing conversations table (ON DELETE CASCADE)
- role field is restricted to "user" or "assistant" (no other values)
- content field is required and has a maximum length
- tool_calls field is optional (NULL for messages without tool calls)
- tool_calls field stores structured data (JSON array of tool invocations)
- Foreign key constraint prevents messages without valid conversations
- Cascade deletion ensures messages are deleted when conversation is deleted

**Priority**: MUST (Non-negotiable - constitution principle)

---

### Requirement 5: Timestamp Management

**Description**: The system MUST automatically manage timestamps for all records to support auditing and chronological ordering.

**Acceptance Criteria**:
- All tables include created_at timestamp field
- created_at is automatically set to current time when record is inserted
- created_at cannot be modified after insertion (immutable)
- Timestamps are stored in a consistent format (e.g., ISO 8601)
- Timestamps use database server time (not application server time)
- Timestamps support efficient querying (e.g., ORDER BY created_at DESC)
- All timestamps include timezone information

**Priority**: MUST

---

### Requirement 6: Indexes for Performance

**Description**: The database MUST include indexes on frequently queried fields to ensure efficient data retrieval.

**Acceptance Criteria**:
- Index on tasks.user_id for fast task lookup by user
- Index on tasks.completed for filtering incomplete vs complete tasks
- Index on conversations.user_id for fast conversation lookup
- Index on messages.conversation_id for fast message history retrieval
- Index on messages.created_at for chronological ordering
- Index on users.email for fast user lookup during authentication
- Composite indexes support common query patterns (e.g., user_id + completed)

**Priority**: MUST

---

### Requirement 7: Data Integrity Constraints

**Description**: The database MUST enforce data integrity through constraints including NOT NULL, UNIQUE, and CHECK constraints.

**Acceptance Criteria**:
- Primary key fields are marked NOT NULL and UNIQUE implicitly
- Foreign key fields are marked NOT NULL
- Required fields (task.title, message.content) are marked NOT NULL
- Email field has UNIQUE constraint
- task.completed field has CHECK constraint (boolean)
- message.role field has CHECK constraint (enum: 'user' or 'assistant')
- String fields have maximum length constraints (e.g., title <= 200 chars, content <= 5000 chars)
- All constraints are enforced at the database level (not application level)

**Priority**: MUST

---

## Data Model

### Entity: Users

Stores user account information for authentication and authorization.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| user_id | UUID | PRIMARY KEY, NOT NULL | Unique user identifier |
| email | VARCHAR(255) | UNIQUE, NOT NULL | User's email address |
| name | VARCHAR(255) | NOT NULL | User's display name |
| password_hash | VARCHAR(255) | NULL | Hashed password (NULL for OAuth) |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Account creation timestamp |

**Indexes**:
- PRIMARY KEY on user_id
- UNIQUE INDEX on email

---

### Entity: Tasks

Stores todo tasks with explicit user ownership.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| task_id | UUID | PRIMARY KEY, NOT NULL | Unique task identifier |
| user_id | UUID | FOREIGN KEY, NOT NULL | Owner of the task |
| title | VARCHAR(200) | NOT NULL | Task title |
| description | TEXT | NULL | Optional task description |
| completed | BOOLEAN | NOT NULL, DEFAULT FALSE | Completion status |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Task creation timestamp |

**Foreign Keys**:
- user_id REFERENCES users(user_id) ON DELETE CASCADE

**Indexes**:
- PRIMARY KEY on task_id
- INDEX on user_id
- INDEX on completed
- COMPOSITE INDEX on (user_id, completed)

---

### Entity: Conversations

Stores one conversation per user for chat history.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| conversation_id | UUID | PRIMARY KEY, NOT NULL | Unique conversation identifier |
| user_id | UUID | FOREIGN KEY, NOT NULL, UNIQUE | Owner of the conversation |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Conversation creation timestamp |

**Foreign Keys**:
- user_id REFERENCES users(user_id) ON DELETE CASCADE

**Indexes**:
- PRIMARY KEY on conversation_id
- UNIQUE INDEX on user_id (ensures one conversation per user)

---

### Entity: Messages

Stores all messages exchanged between user and AI assistant.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| message_id | UUID | PRIMARY KEY, NOT NULL | Unique message identifier |
| conversation_id | UUID | FOREIGN KEY, NOT NULL | Conversation this message belongs to |
| role | VARCHAR(50) | NOT NULL, CHECK IN ('user', 'assistant') | Message sender role |
| content | TEXT | NOT NULL | Message text content |
| tool_calls | JSONB | NULL | Tool invocations made by assistant |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | Message creation timestamp |

**Foreign Keys**:
- conversation_id REFERENCES conversations(conversation_id) ON DELETE CASCADE

**Indexes**:
- PRIMARY KEY on message_id
- INDEX on conversation_id
- INDEX on created_at

---

## Entity Relationships

```
users (1) ----< (1) conversations
users (1) ----< (N) tasks
conversations (1) ----< (N) messages
```

**Relationship Rules**:
- Each user has exactly one conversation
- Each user has zero or more tasks
- Each conversation has zero or more messages
- All relationships enforce referential integrity through foreign keys
- Cascade deletion ensures no orphaned records when users are deleted

---

## Non-Functional Requirements

### Performance
- Queries for user's tasks complete in under 100ms for 1000 tasks
- Conversation history fetch completes in under 200ms for 100 messages
- Database can support 10,000 concurrent users
- Indexes support efficient query execution

### Scalability
- Schema supports horizontal scaling (no shared state between servers)
- No database-specific features that prevent multi-instance deployment
- Connection pooling supported for high concurrency

### Reliability
- ACID compliance for all transactions
- No data loss due to crashes (atomic writes)
- Referential integrity prevents orphaned records
- Automatic timestamp management prevents clock skew issues

### Security
- User isolation enforced at database level (foreign keys)
- No cross-user data access possible through queries
- Cascade deletion prevents orphaned records
- Constraints prevent invalid data insertion

---

## Out of Scope

The following are explicitly OUT OF SCOPE for this feature:

- Analytics or reporting tables (e.g., usage statistics, task completion rates)
- Soft-delete system (deleted records are permanently removed)
- Multi-tenant schemas (single schema for all users)
- Data warehousing or OLAP features
- Audit logging tables (beyond basic timestamps)
- Task categories, tags, or priority tables
- Task scheduling or due date fields
- File or attachment storage
- Real-time synchronization tables
- Database views or materialized views
- Triggers or stored procedures
- Full-text search indexes

---

## Assumptions

1. **PostgreSQL version**: Database supports UUID data type, JSONB, and foreign key constraints
2. **Single database instance**: All tables exist in a single database schema
3. **Time zone consistency**: Database server and application server use consistent time zones
4. **UUID generation**: Application or ORM generates UUIDs for primary keys
5. **Connection pooling**: Application uses connection pooling for database connections
6. **Migration system**: Schema changes are managed through a migration tool (e.g., Alembic)
7. **Backup strategy**: Database backups are performed regularly (not part of this schema)

---

## Success Criteria

The feature is successful when:

1. **User Ownership**: 100% of tasks have valid user_id foreign keys (zero orphaned tasks)
2. **Conversation Persistence**: 100% of messages are retrievable after server restart
3. **Referential Integrity**: 100% of foreign key constraints are enforced (zero constraint violations)
4. **Query Performance**: 95% of queries complete within performance targets (100ms for tasks, 200ms for messages)
5. **Data Consistency**: 100% of records comply with constraints (no invalid data)
6. **Cascade Operations**: 100% of cascading deletes work correctly (no orphaned records after user deletion)
7. **Timestamp Accuracy**: 100% of timestamps are automatically set and immutable

---

## Dependencies

### Internal Dependencies
- User authentication system (provides user_id for records)
- MCP tools (create and update task records)
- Chat API (creates conversation and message records)

### External Dependencies
- PostgreSQL database (data persistence)
- SQLModel ORM (schema definition and migrations)

---

## Notes

This specification defines the database schema that supports the entire Todo AI Chatbot system. The schema is:

1. **User-Centric**: All data is scoped to users through foreign keys
2. **Integrity-Enforcing**: Foreign keys and constraints prevent invalid data
3. **Performance-Optimized**: Indexes support efficient querying
4. **Stateless-Supporting**: No server-side state required; all state in database
5. **Cascade-Safe**: Deletions cascade to prevent orphaned records

**Schema Design Principles**:
- Explicit ownership through foreign keys
- Atomic operations through ACID compliance
- Automatic timestamp management
- Immutable primary keys (UUIDs)
- Structured data storage (JSONB for tool_calls)

**Relationship to Other Specifications**:
- 001-agent-behavior: Uses message history for context
- 002-mcp-tools: Operates on tasks table
- 003-chat-api: Creates and queries conversations and messages tables

This schema is the foundation that enables the stateless, tool-driven, conversation-aware architecture defined in the project constitution.
