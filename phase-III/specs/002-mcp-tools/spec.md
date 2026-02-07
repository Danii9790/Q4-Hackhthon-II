# Feature Specification: MCP Server Tools for Todo Management

**Feature Branch**: `002-mcp-tools`
**Created**: 2026-02-06
**Status**: Draft
**Input**: User description: "Todo AI Chatbot — MCP Server Tools"

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

### User Story 1 - AI Agent Creates Task via Tool (Priority: P1)

**Why this priority**: This is the foundational operation - the AI agent must be able to create tasks on behalf of users through MCP tools. Without this, the core todo functionality doesn't work.

**Independent Test**: An AI agent can invoke the `add_task` tool with a title and description, and the system creates a task belonging to the authenticated user, returning the new task details.

**Acceptance Scenarios**:

1. **Given** an authenticated user with ID "user-123", **When** the AI agent invokes `add_task` with title "buy groceries", **Then** a task is created in the database with title "buy groceries", user_id "user-123", and completed=false, and the tool returns success=true with the task details
2. **Given** an authenticated user, **When** the AI agent invokes `add_task` with title "call mom" and description "about birthday party", **Then** a task is created with both title and description stored, and the tool returns the complete task object
3. **Given** an authenticated user, **When** the AI agent invokes `add_task` with an empty title, **Then** the tool returns success=false with an error message explaining that title is required

---

### User Story 2 - AI Agent Lists User's Tasks via Tool (Priority: P1)

**Why this priority**: Users need to see their tasks. The AI agent must be able to retrieve tasks to display them or reference them in conversation.

**Independent Test**: An AI agent can invoke the `list_tasks` tool for a user, and the system returns all tasks belonging to that user with their completion status.

**Acceptance Scenarios**:

1. **Given** an authenticated user with 3 tasks (2 incomplete, 1 complete), **When** the AI agent invokes `list_tasks`, **Then** the tool returns success=true with an array of all 3 tasks, each containing id, title, description, completed status, and creation timestamp
2. **Given** an authenticated user with 5 tasks, **When** the AI agent invokes `list_tasks` with include_completed=false, **Then** the tool returns only incomplete tasks
3. **Given** an authenticated user with no tasks, **When** the AI agent invokes `list_tasks`, **Then** the tool returns success=true with an empty task array and count=0

---

### User Story 3 - AI Agent Completes Task via Tool (Priority: P1)

**Why this priority**: Task completion is the goal of the todo system. The AI agent must be able to mark tasks as done on behalf of users.

**Independent Test**: An AI agent can invoke the `complete_task` tool with a valid task ID, and the system marks that specific task as complete, but only if it belongs to the authenticated user.

**Acceptance Scenarios**:

1. **Given** an authenticated user with task ID "task-456" that belongs to them, **When** the AI agent invokes `complete_task` with task_id="task-456", **Then** the task is marked as completed=true in the database, and the tool returns success=true with a confirmation message
2. **Given** an authenticated user attempting to complete task ID "task-789" that belongs to a different user, **When** the AI agent invokes `complete_task`, **Then** the tool returns success=false with an error message "Task not found" (without revealing it belongs to another user)
3. **Given** an authenticated user, **When** the AI agent invokes `complete_task` with a non-existent task ID, **Then** the tool returns success=false with an error message explaining the task was not found

---

### User Story 4 - AI Agent Updates Task via Tool (Priority: P2)

**Why this priority**: Users often need to modify task details after creation. The AI agent must be able to update tasks on behalf of users.

**Independent Test**: An AI agent can invoke the `update_task` tool with a task ID and new title/description, and the system updates the task, but only if it belongs to the authenticated user.

**Acceptance Scenarios**:

1. **Given** an authenticated user with task ID "task-123" that belongs to them, **When** the AI agent invokes `update_task` with task_id="task-123" and new title "buy groceries and milk", **Then** the task title is updated in the database, and the tool returns success=true with the updated task object
2. **Given** an authenticated user with their own task, **When** the AI agent invokes `update_task` with only a new description (no title change), **Then** only the description field is updated while other fields remain unchanged
3. **Given** an authenticated user attempting to update another user's task, **When** the AI agent invokes `update_task`, **Then** the tool returns success=false without modifying the task and without revealing the other user's data

---

### User Story 5 - AI Agent Deletes Task via Tool (Priority: P2)

**Why this priority**: Users need to remove tasks they no longer want. The AI agent must be able to delete tasks on behalf of users, but only with proper ownership validation.

**Independent Test**: An AI agent can invoke the `delete_task` tool with a valid task ID, and the system removes that task permanently, but only if it belongs to the authenticated user.

**Acceptance Scenarios**:

1. **Given** an authenticated user with task ID "task-999" that belongs to them, **When** the AI agent invokes `delete_task` with task_id="task-999", **Then** the task is permanently removed from the database, and the tool returns success=true with a confirmation message
2. **Given** an authenticated user attempting to delete another user's task, **When** the AI agent invokes `delete_task`, **Then** the tool returns success=false, the task is not deleted, and no information about the other user is revealed
3. **Given** an authenticated user who previously deleted a task, **When** the AI agent attempts to `complete_task` or `update_task` with that deleted task ID, **Then** those operations return success=false with "task not found" error

---

### User Story 6 - Tool Handles Database Errors Graceacefully (Priority: P1)

**Why this priority**: Database operations can fail for various reasons (connection issues, constraints, etc.). Tools must handle these failures safely without exposing internal errors to users.

**Independent Test**: When a database operation fails (connection lost, constraint violation, etc.), the tool returns a user-friendly error message instead of exposing database internals or stack traces.

**Acceptance Scenarios**:

1. **Given** the database connection is temporarily unavailable, **When** the AI agent invokes any tool, **Then** the tool returns success=false with a message like "I'm having trouble connecting right now. Please try again" without exposing database connection strings or SQL errors
2. **Given** a concurrent modification conflict (two users updating same task), **When** the AI agent invokes `update_task`, **Then** the tool returns success=false with a message explaining the issue and suggesting the user try again
3. **Given** any database constraint violation (e.g., duplicate key), **When** a tool is invoked, **Then** the tool returns success=false with a user-friendly message that doesn't reveal database schema or constraint names

---

## Functional Requirements

### Requirement 1: Stateless Tool Design

**Description**: Each MCP tool MUST be stateless and perform operations atomically using only the database for persistence.

**Acceptance Criteria**:
- Tools MUST NOT store any state in memory between invocations
- Each tool invocation MUST be independent and self-contained
- Tools MUST retrieve current state from database on each call
- Tools MUST persist results to database before returning
- Tool behavior MUST be deterministic based on inputs and database state
- No global variables or singleton services maintain user or task state

**Priority**: MUST (Non-negotiable - constitution principle)

---

### Requirement 2: User Ownership Validation

**Description**: Every tool that modifies or accesses task data MUST validate that the task belongs to the authenticated user before performing any operation.

**Acceptance Criteria**:
- `add_task` creates tasks with user_id set to authenticated user's ID
- `list_tasks` returns only tasks belonging to authenticated user
- `complete_task` validates task ownership before marking complete
- `update_task` validates task ownership before modifying
- `delete_task` validates task ownership before deleting
- Ownership validation failures return "not found" error without revealing other users' data
- No tool allows cross-user data access under any circumstances

**Priority**: MUST (Non-negotiable - security requirement)

---

### Requirement 3: Schema Compliance

**Description**: Tool inputs and outputs MUST exactly match their defined schemas. No deviations or optional fields beyond the schema definition.

**Acceptance Criteria**:
- `add_task` accepts: title (string, required), description (string, optional)
- `list_tasks` accepts: include_completed (boolean, optional, default true)
- `complete_task` accepts: task_id (string, required)
- `update_task` accepts: task_id (string, required), title (string, optional), description (string, optional)
- `delete_task` accepts: task_id (string, required)
- All tools return: success (boolean) + message (string) + relevant data objects
- Output schemas are consistent across all invocations
- Invalid input types are rejected with clear error messages

**Priority**: MUST

---

### Requirement 4: Safe Error Handling

**Description**: Tools MUST handle all errors gracefully and return user-friendly error messages without exposing internal implementation details.

**Acceptance Criteria**:
- Database errors return generic user-friendly messages
- No stack traces exposed in tool outputs
- No database schema details exposed (table names, column names, constraints)
- No internal IDs or technical jargon in user-facing messages
- Network errors return "try again" messages
- Validation errors explain what was wrong and what's expected
- All errors include success=false flag

**Priority**: MUST

---

### Requirement 5: Atomic Operations

**Description**: Each tool operation MUST be atomic - either fully complete or fully roll back with no partial state changes.

**Acceptance Criteria**:
- `add_task` either creates complete task or creates nothing
- `complete_task` either marks task complete or leaves it unchanged
- `update_task` either applies all changes or applies none
- `delete_task` either removes task completely or leaves it untouched
- Database transactions wrap each operation
- Concurrent modifications are handled with retry or failure
- No partial updates or intermediate states visible to other operations

**Priority**: MUST

---

### Requirement 6: Input Validation

**Description**: Tools MUST validate all inputs before processing and return clear error messages for invalid inputs.

**Acceptance Criteria**:
- Required fields are checked for presence
- String fields are validated for minimum/maximum length
- Invalid data types are rejected with clear messages
- Empty strings for required fields are rejected
- Malformed or invalid task IDs are rejected
- Boolean flags accept only boolean values
- Validation happens before any database operations

**Priority**: MUST

---

### Requirement 7: Output Consistency

**Description**: Tools MUST return consistent output structure across all invocations, making responses predictable for AI agents.

**Acceptance Criteria**:
- Success responses always include success=true flag
- Error responses always include success=false flag
- All responses include a human-readable message field
- Data objects (when present) follow consistent structure
- Field names match schema exactly (no variations)
- Timestamps use consistent format (ISO 8601)
- No null values in required fields of success responses

**Priority**: MUST

---

## Non-Functional Requirements

### Performance
- Tool invocations complete within 2 seconds for 95% of requests
- Database queries are optimized with proper indexing
- No N+1 query patterns in tool implementations

### Security
- Every database operation validates user ownership
- SQL injection prevention through parameterized queries
- No task data leakage between users
- Error messages don't reveal sensitive information

### Reliability
- Tools handle database connection failures gracefully
- Automatic retry for transient database errors
- Proper transaction rollback on operation failures

---

## Tool Contracts

### Tool: add_task

**Description**: Creates a new task for the authenticated user

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "title": {
      "type": "string",
      "description": "Task title (1-200 characters)",
      "minLength": 1,
      "maxLength": 200
    },
    "description": {
      "type": "string",
      "description": "Optional task description (max 1000 characters)",
      "maxLength": 1000
    }
  },
  "required": ["title"]
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "success": {
      "type": "boolean",
      "description": "True if task was created successfully"
    },
    "message": {
      "type": "string",
      "description": "Human-readable result message"
    },
    "task": {
      "type": "object",
      "description": "Created task object (present on success)",
      "properties": {
        "id": {"type": "string"},
        "title": {"type": "string"},
        "description": {"type": "string"},
        "completed": {"type": "boolean"},
        "created_at": {"type": "string", "format": "date-time"}
      }
    }
  }
}
```

**Errors**:
- Missing title: "Task title is required"
- Title too long: "Task title must be less than 200 characters"
- Description too long: "Task description must be less than 1000 characters"
- Database error: "I'm having trouble saving your task right now. Please try again"

---

### Tool: list_tasks

**Description**: Lists tasks belonging to the authenticated user

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "include_completed": {
      "type": "boolean",
      "description": "Whether to include completed tasks (default: true)",
      "default": true
    }
  }
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "success": {
      "type": "boolean",
      "description": "True if tasks were retrieved successfully"
    },
    "message": {
      "type": "string",
      "description": "Human-readable result message"
    },
    "tasks": {
      "type": "array",
      "description": "Array of task objects",
      "items": {
        "type": "object",
        "properties": {
          "id": {"type": "string"},
          "title": {"type": "string"},
          "description": {"type": "string"},
          "completed": {"type": "boolean"},
          "created_at": {"type": "string", "format": "date-time"}
        }
      }
    },
    "count": {
      "type": "integer",
      "description": "Total number of tasks returned"
    }
  }
}
```

**Errors**:
- Database error: "I'm having trouble loading your tasks right now. Please try again"

---

### Tool: complete_task

**Description**: Marks a task as completed

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "task_id": {
      "type": "string",
      "description": "ID of task to complete"
    }
  },
  "required": ["task_id"]
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "success": {
      "type": "boolean",
      "description": "True if task was marked complete"
    },
    "message": {
      "type": "string",
      "description": "Human-readable result message"
    },
    "task": {
      "type": "object",
      "description": "Updated task object (present on success)",
      "properties": {
        "id": {"type": "string"},
        "title": {"type": "string"},
        "completed": {"type": "boolean"}
      }
    }
  }
}
```

**Errors**:
- Missing task_id: "Task ID is required"
- Task not found: "I couldn't find that task"
- Already completed: "That task is already complete"
- Database error: "I'm having trouble updating your task right now. Please try again"

---

### Tool: update_task

**Description**: Updates an existing task's title or description

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "task_id": {
      "type": "string",
      "description": "ID of task to update"
    },
    "title": {
      "type": "string",
      "description": "New task title (1-200 characters)",
      "minLength": 1,
      "maxLength": 200
    },
    "description": {
      "type": "string",
      "description": "New task description (max 1000 characters)",
      "maxLength": 1000
    }
  },
  "required": ["task_id"]
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "success": {
      "type": "boolean",
      "description": "True if task was updated"
    },
    "message": {
      "type": "string",
      "description": "Human-readable result message"
    },
    "task": {
      "type": "object",
      "description": "Updated task object (present on success)",
      "properties": {
        "id": {"type": "string"},
        "title": {"type": "string"},
        "description": {"type": "string"},
        "completed": {"type": "boolean"}
      }
    }
  }
}
```

**Errors**:
- Missing task_id: "Task ID is required"
- No changes provided: "Please provide a new title or description"
- Task not found: "I couldn't find that task"
- Database error: "I'm having trouble updating your task right now. Please try again"

---

### Tool: delete_task

**Description**: Deletes a task permanently

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "task_id": {
      "type": "string",
      "description": "ID of task to delete"
    }
  },
  "required": ["task_id"]
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "success": {
      "type": "boolean",
      "description": "True if task was deleted"
    },
    "message": {
      "type": "string",
      "description": "Human-readable result message"
    }
  }
}
```

**Errors**:
- Missing task_id: "Task ID is required"
- Task not found: "I couldn't find that task"
- Database error: "I'm having trouble deleting your task right now. Please try again"

---

## Out of Scope

The following are explicitly OUT OF SCOPE for this feature:

- Business logic inside AI agent (agent only invokes tools, doesn't implement CRUD)
- In-memory task storage or caching
- Cross-user task sharing or collaboration
- Bulk operations (create multiple tasks at once)
- Task search or full-text filtering
- Task categories, tags, or priorities
- Task scheduling or due dates
- Task reminders or notifications
- File attachments or rich media in tasks
- Non-task-related MCP tools (e.g., user management, authentication)
- Real-time task updates or webhooks

---

## Assumptions

1. **User authentication**: User identity is validated by the backend before tool invocation
2. **Database availability**: PostgreSQL database is accessible and properly configured
3. **User context**: Each tool invocation includes authenticated user context (user ID)
4. **Task ownership**: Tasks have a user_id foreign key linking them to users
5. **Simple task model**: Tasks have only id, user_id, title, description, completed, created_at fields
6. **Unique task IDs**: Task IDs are globally unique across all users
7. **Synchronous operations**: Tools execute synchronously (no background jobs)

---

## Success Criteria

The feature is successful when:

1. **Tool Availability**: All 5 CRUD tools (add, list, complete, update, delete) are accessible and functional
2. **Ownership Enforcement**: 100% of tool operations respect user ownership (zero cross-user data leakage)
3. **Stateless Operation**: Tools maintain zero in-memory state across invocations (verified through restart tests)
4. **Schema Compliance**: 100% of tool inputs/outputs match defined schemas exactly
5. **Error Safety**: 100% of errors return user-friendly messages with no internal details exposed
6. **Atomic Operations**: 100% of operations are atomic (no partial updates or intermediate states)
7. **Performance**: 95% of tool invocations complete within 2 seconds

---

## Dependencies

### Internal Dependencies
- User authentication system (provides user context)
- Database schema (users table, tasks table with foreign keys)
- MCP server framework (provides tool registration and invocation)

### External Dependencies
- Official MCP SDK for tool implementation
- PostgreSQL database for persistence

---

## Notes

This specification defines the MCP tools that the backend exposes to AI agents. The tools are:

1. **Stateless**: Each operation is independent with no in-memory state
2. **Secure**: User ownership is validated on every operation
3. **Deterministic**: Same inputs + database state always produces same outputs
4. **Safe**: Errors are handled gracefully without exposing internals

The AI agent (specified in feature 001-agent-behavior) will invoke these tools. The agent has no direct database access and implements no business logic - it only interprets user intent and invokes the appropriate tool.

This separation of concerns ensures:
- **Testability**: Each tool can be tested independently
- **Security**: All database access goes through validated tools
- **Traceability**: Every state change is logged via tool invocation
- **Scalability**: Stateless tools can be load-balanced horizontally
