# add_task MCP Tool - Usage Documentation

## Overview

The `add_task` MCP tool enables AI agents to create new tasks for users through natural language interactions. This tool is part of the Todo AI Chatbot's MCP (Model Context Protocol) toolkit and integrates seamlessly with the OpenAI Agents SDK.

## File Location

```
backend/src/mcp_tools/add_task.py
```

## Architecture

### Class: AddTaskTool

Inherits from `BaseMCPTool` and provides:
- User ID validation (UUID format)
- Input validation (title and description)
- Database operations with error handling
- Structured JSON responses

### Entry Point: add_task()

Async function that creates an `AddTaskTool` instance and executes it.
This is the function registered with the MCP server.

## MCP Schema

```json
{
  "name": "add_task",
  "description": "Create a new task for the user...",
  "inputSchema": {
    "type": "object",
    "properties": {
      "user_id": {
        "type": "string",
        "format": "uuid",
        "description": "User's unique identifier (UUID from JWT token)"
      },
      "title": {
        "type": "string",
        "minLength": 1,
        "maxLength": 500,
        "description": "Task title (required, max 500 characters)"
      },
      "description": {
        "type": "string",
        "maxLength": 5000,
        "description": "Optional detailed task description (max 5000 characters)"
      }
    },
    "required": ["user_id", "title"]
  }
}
```

## Usage Examples

### Basic Usage

```python
from src.mcp_tools.add_task import add_task

# Create a task with just a title
result = await add_task(
    user_id="550e8400-e29b-41d4-a716-446655440000",
    title="Buy groceries"
)

# Response:
# {
#     "success": True,
#     "message": "Task created successfully",
#     "data": {
#         "id": 1,
#         "title": "Buy groceries",
#         "description": None,
#         "completed": False
#     }
# }
```

### With Description

```python
result = await add_task(
    user_id="550e8400-e29b-41d4-a716-446655440000",
    title="Call dentist",
    description="Schedule appointment for next Tuesday at 3pm"
)

# Response:
# {
#     "success": True,
#     "message": "Task created successfully",
#     "data": {
#         "id": 2,
#         "title": "Call dentist",
#         "description": "Schedule appointment for next Tuesday at 3pm",
#         "completed": False
#     }
# }
```

### Using the Class Directly

```python
from src.mcp_tools.add_task import AddTaskTool

tool = AddTaskTool()
result = await tool.execute(
    user_id="550e8400-e29b-41d4-a716-446655440000",
    title="Review project proposal",
    description="Check budget and timeline estimates"
)
```

## Input Validation

### Title Validation

- **Required**: Must be provided
- **Type**: String
- **Max Length**: 500 characters
- **Constraints**:
  - Cannot be None
  - Cannot be empty or only whitespace
  - Will be stripped of leading/trailing whitespace

**Example Errors:**

```python
# Empty title
await add_task(user_id="...", title="")
# Raises: TaskValidationError("Task title is required and cannot be empty or only whitespace")

# Title too long
await add_task(user_id="...", title="x" * 501)
# Raises: TaskValidationError("Task title cannot exceed 500 characters (got 501)")
```

### Description Validation

- **Optional**: Can be None or omitted
- **Type**: String (if provided)
- **Max Length**: 5000 characters
- **Constraints**:
  - Empty strings are treated as None
  - Will be stripped of leading/trailing whitespace

**Examples:**

```python
# Valid - no description
await add_task(user_id="...", title="Task")

# Valid - with description
await add_task(user_id="...", title="Task", description="Details")

# Valid - empty string becomes None
await add_task(user_id="...", title="Task", description="  ")
# description will be None
```

### User ID Validation

- **Required**: Must be provided
- **Type**: String (UUID format)
- **Validated** by BaseMCPTool.validate_user_id()

**Example Errors:**

```python
# Invalid UUID format
await add_task(user_id="not-a-uuid", title="Task")
# Raises: UserValidationError("Invalid user ID format")
```

## Error Handling

The tool implements comprehensive error handling:

### Exception Types

1. **UserValidationError** (from BaseMCPTool)
   - Invalid user ID format
   - Missing user ID

2. **TaskValidationError** (custom)
   - Invalid title
   - Invalid description
   - Type mismatches

3. **DatabaseOperationError** (from BaseMCPTool)
   - Database connection failures
   - Constraint violations
   - SQL errors

4. **MCPToolError**
   - Unexpected internal errors

### Error Response Format

```python
try:
    result = await add_task(user_id="...", title="Task")
except TaskValidationError as e:
    print(f"Validation error: {e.message}")  # e.message: "Task title is required"
    print(f"Error code: {e.code}")           # e.code: "TASK_VALIDATION_ERROR"
```

## Database Operations

### Transaction Flow

1. Validate user_id (UUID check)
2. Validate title (required, max 500 chars)
3. Validate description (optional, max 5000 chars)
4. Create Task instance with validated data
5. Add to database session
6. Commit transaction
7. Refresh task to get database-generated values (id, timestamps)
8. Format and return success response

### Database Model

```python
Task(
    user_id=UUID,              # From validated user_id
    title=str,                 # Validated and stripped
    description=Optional[str], # Validated and stripped, or None
    completed=False            # Default for new tasks
)
# Auto-generated by database: id, created_at, updated_at
```

## Response Format

### Success Response

```json
{
  "success": true,
  "message": "Task created successfully",
  "data": {
    "id": 1,
    "title": "Buy groceries",
    "description": "Milk, eggs, bread",
    "completed": false
  }
}
```

### Error Response

Errors are raised as exceptions, not returned as error responses.
The calling code should catch and handle these exceptions appropriately.

## Logging

The tool implements comprehensive logging:

```python
# Info level - Normal operations
logger.info("Executing add_task for user_id: {user_id}")
logger.info("Title validated successfully: '{title}...'")
logger.info(f"Task created successfully: id={task.id}, title='{title}'")

# Warning level - Validation failures
logger.warning("Title validation failed: title is empty after stripping")
logger.warning(f"Title validation failed: title exceeds maximum length ({len} > 500)")

# Error level - Errors
logger.error("User validation failed: {error}")
logger.error("Database error while creating task: {error}")
logger.error("Unexpected error while creating task: {error}")
```

## Testing

### Unit Tests

Test file: `backend/tests/test_add_task_structure.py`

Run tests:
```bash
cd backend
python tests/test_add_task_structure.py
```

### Manual Testing

```python
import asyncio
from src.mcp_tools.add_task import add_task

async def test():
    # Test 1: Basic task creation
    result = await add_task(
        user_id="550e8400-e29b-41d4-a716-446655440000",
        title="Test task"
    )
    print(result)

    # Test 2: Task with description
    result = await add_task(
        user_id="550e8400-e29b-41d4-a716-446655440000",
        title="Test task with description",
        description="This is a detailed description"
    )
    print(result)

asyncio.run(test())
```

## Integration with OpenAI Agents SDK

The tool is automatically registered with the MCP server and exposed to the AI agent:

```python
# In MCP server registration
from src.mcp_tools.add_task import ADD_TASK_SCHEMA, add_task

# Register tool with MCP server
mcp_server.register_tool(
    schema=ADD_TASK_SCHEMA,
    handler=add_task
)
```

The agent can then call the tool through natural language:

```
User: "Add a task to buy groceries"
Agent: (interprets and calls) add_task(user_id="...", title="Buy groceries")
Agent: "I've created a task called 'Buy groceries'"
```

## Constraints and Limits

- **Title**: 1-500 characters (required)
- **Description**: 0-5000 characters (optional)
- **User ID**: Must be valid UUID string
- **Database**: One task per operation
- **Concurrency**: Safe for concurrent use (database-level locking)

## Dependencies

- `src.models.task.Task` - Database model
- `src.mcp_tools.base.BaseMCPTool` - Base functionality
- `src.db.session.get_session` - Database session management
- `sqlalchemy.exc.SQLAlchemyError` - Database error handling

## Future Enhancements

Potential improvements:
1. Add task priority field
2. Add due date support
3. Add task categorization/tags
4. Add sub-task support
5. Batch task creation
6. Task templates

## Related Tools

- `list_tasks` - Query tasks by status
- `complete_task` - Mark task as completed
- `update_task` - Modify existing task
- `delete_task` - Remove task

## Support

For issues or questions:
1. Check logs for detailed error messages
2. Verify user_id is valid UUID format
3. Ensure database is accessible
4. Check title length and format
5. Review validation error messages

## Version History

- **v1.0** (2026-02-01): Initial implementation
  - Basic task creation
  - User validation
  - Input validation
  - Database integration
  - MCP schema registration
