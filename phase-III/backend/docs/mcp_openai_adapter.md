# OpenAI Adapter for MCP Tools - Implementation Guide

## Overview

The MCP to OpenAI adapter (`backend/src/services/mcp_openai_adapter.py`) provides a bridge between MCP (Model Context Protocol) tools and the OpenAI Agents SDK. This adapter enables seamless integration of task management tools with AI agents.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        OpenAI Agents SDK                        │
│                    (Agent + Function Tools)                     │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                     MCP to OpenAI Adapter                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  • MCPToolRegistry (tool registration)                   │  │
│  │  • convert_mcp_schema_to_openai() (schema conversion)    │  │
│  │  • convert_openai_response_to_mcp() (response handling)  │  │
│  │  • mcp_tool_error_handler() (error handling)             │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MCP Tools Layer                              │
│  • AddTaskTool (create tasks)                                   │
│  • ListTasksTool (list tasks - future)                          │
│  • CompleteTaskTool (mark complete - future)                    │
│  • UpdateTaskTool (update tasks - future)                       │
│  • DeleteTaskTool (delete tasks - future)                       │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Database Layer                            │
│                    (PostgreSQL + SQLModel)                      │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. MCPToolRegistry

Centralized registry for managing MCP tools.

```python
from src.services.mcp_openai_adapter import MCPToolRegistry

# Create registry
registry = MCPToolRegistry()

# Register a tool
registry.register_tool(
    tool_name="add_task",
    mcp_schema=ADD_TASK_SCHEMA,
    mcp_tool_instance=AddTaskTool()
)

# List all registered tools
tools = registry.list_tools()  # ["add_task", "list_tasks", ...]

# Retrieve a tool
tool_data = registry.get_tool("add_task")
schema = tool_data["schema"]
instance = tool_data["instance"]
```

**Features:**
- Prevents duplicate tool registration
- Thread-safe for concurrent access
- Type-safe with proper hints
- Easy to extend with new tools

### 2. Schema Conversion: MCP → OpenAI

Converts MCP JSON Schema format to OpenAI function calling format.

**Input (MCP Schema):**
```json
{
    "name": "add_task",
    "description": "Create a new task for the user",
    "inputSchema": {
        "type": "object",
        "properties": {
            "user_id": {
                "type": "string",
                "format": "uuid"
            },
            "title": {
                "type": "string",
                "minLength": 1,
                "maxLength": 500
            },
            "description": {
                "type": "string",
                "maxLength": 5000
            }
        },
        "required": ["user_id", "title"]
    }
}
```

**Output (OpenAI Function):**
```json
{
    "type": "function",
    "function": {
        "name": "add_task",
        "description": "Create a new task for the user",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "format": "uuid"
                },
                "title": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 500
                },
                "description": {
                    "type": "string",
                    "maxLength": 5000
                }
            },
            "required": ["user_id", "title"]
        }
    }
}
```

**Usage:**
```python
from src.services.mcp_openai_adapter import convert_mcp_schema_to_openai

openai_schema = convert_mcp_schema_to_openai(ADD_TASK_SCHEMA)
```

### 3. Response Conversion: OpenAI → MCP

Converts OpenAI tool responses to standardized MCP format.

```python
from src.services.mcp_openai_adapter import convert_openai_response_to_mcp

# String success response
response = "Task created successfully"
mcp_response = convert_openai_response_to_mcp(response)
# Returns: {"success": True, "message": "Task created successfully", "data": {...}}

# String error response
response = "Error: Invalid input"
mcp_response = convert_openai_response_to_mcp(response)
# Returns: {"success": False, "message": "Error: Invalid input", "data": None}

# Already formatted MCP dict
mcp_dict = {"success": True, "message": "...", "data": {...}}
mcp_response = convert_openai_response_to_mcp(mcp_dict)
# Returns: same dict (pass-through)
```

### 4. Error Handling

Custom error handler for graceful tool failure handling.

```python
from src.services.mcp_openai_adapter import mcp_tool_error_handler

@function_tool(failure_error_function=mcp_tool_error_handler)
async def my_tool(param: str) -> str:
    # Tool implementation
    pass
```

**Error Types Handled:**
- `TaskValidationError`: "Task validation failed: {details}"
- `ValidationError`: "Input validation error: Please check your parameters"
- `PermissionError`: "Permission denied. You don't have access..."
- `ConnectionError`: "Connection error. Please check your network..."
- `Generic Exception`: "An error occurred while processing your request..."

### 5. OpenAI Function Tool Wrapper

The `add_task_openai` function wraps the MCP `AddTaskTool` for use with OpenAI agents.

```python
from src.services.mcp_openai_adapter import add_task_openai

# Automatically decorated with @function_tool
# Used by OpenAI agents via function calling
result = await add_task_openai(
    user_id="550e8400-e29b-41d4-a716-446655440000",
    title="Buy groceries",
    description="Milk, eggs, bread"
)
```

## Usage Example

### Basic Usage

```python
from src.services.mcp_openai_adapter import (
    MCPToolRegistry,
    convert_mcp_schema_to_openai,
    add_task_openai,
    tool_registry  # Global registry with add_task pre-registered
)

# Method 1: Use global registry (add_task already registered)
tools = tool_registry.list_tools()  # ["add_task"]

# Method 2: Create custom registry
custom_registry = MCPToolRegistry()
custom_registry.register_tool("add_task", ADD_TASK_SCHEMA, AddTaskTool())

# Convert schema for OpenAI
tool_data = tool_registry.get_tool("add_task")
openai_schema = convert_mcp_schema_to_openai(tool_data["schema"])

# Use with OpenAI Agent
from agents import Agent

agent = Agent(
    name="TodoAssistant",
    instructions="You help users manage tasks",
    tools=[add_task_openai]  # Function tools automatically registered
)
```

### Adding New Tools

```python
# 1. Create MCP tool (in src/mcp_tools/list_tasks.py)
class ListTasksTool(BaseMCPTool):
    tool_name = "list_tasks"
    # ... implementation ...

LIST_TASKS_SCHEMA = {
    "name": "list_tasks",
    "description": "List all tasks",
    "inputSchema": {...}
}

# 2. Create OpenAI function tool wrapper
@function_tool(
    name_override="list_tasks",
    failure_error_function=mcp_tool_error_handler
)
async def list_tasks_openai(user_id: str, status: str = "all") -> str:
    """List all tasks for the user."""
    tool = ListTasksTool()
    result = await tool.execute(user_id=user_id, status=status)
    return format_response(result)

# 3. Register with global registry
from src.services.mcp_openai_adapter import tool_registry
tool_registry.register_tool("list_tasks", LIST_TASKS_SCHEMA, ListTasksTool())

# 4. Add to agent
agent = Agent(
    name="TodoAssistant",
    tools=[add_task_openai, list_tasks_openai]
)
```

## File Structure

```
backend/
├── src/
│   ├── services/
│   │   ├── agent.py                    # T029: Basic OpenAI SDK setup
│   │   └── mcp_openai_adapter.py       # T032: MCP → OpenAI adapter
│   └── mcp_tools/
│       ├── base.py                     # BaseMCPTool with common utilities
│       └── add_task.py                 # AddTaskTool implementation
├── tests/
│   └── unit/
│       └── test_mcp_openai_adapter.py  # Unit tests for adapter
└── docs/
    └── mcp_openai_adapter.md           # This file
```

## Testing

### Unit Tests

Located in `tests/unit/test_mcp_openai_adapter.py`:

```bash
cd backend
python -m pytest tests/unit/test_mcp_openai_adapter.py -v
```

**Test Coverage:**
- Schema conversion (MCP → OpenAI)
- Response conversion (OpenAI → MCP)
- Tool registry operations
- Error handler functionality
- Integration scenarios

### Manual Testing

```python
# Quick verification script
import sys
sys.path.insert(0, 'backend')

from src.services.mcp_openai_adapter import (
    MCPToolRegistry,
    convert_mcp_schema_to_openai,
    convert_openai_response_to_mcp
)
from src.mcp_tools.add_task import ADD_TASK_SCHEMA

# Test schema conversion
openai_schema = convert_mcp_schema_to_openai(ADD_TASK_SCHEMA)
print(f"Converted schema: {openai_schema['function']['name']}")

# Test response conversion
response = convert_openai_response_to_mcp("Task created")
print(f"Response success: {response['success']}")

# Test registry
registry = MCPToolRegistry()
from src.mcp_tools.add_task import AddTaskTool
registry.register_tool("add_task", ADD_TASK_SCHEMA, AddTaskTool())
print(f"Registry tools: {registry.list_tools()}")
```

## API Reference

### MCPToolRegistry

**Methods:**
- `__init__()`: Initialize empty registry
- `register_tool(tool_name, mcp_schema, mcp_tool_instance)`: Register a tool
- `get_tool(tool_name)`: Retrieve tool by name
- `list_tools()`: Get list of registered tool names

### convert_mcp_schema_to_openai

**Parameters:**
- `mcp_schema` (dict): MCP tool schema

**Returns:**
- `dict`: OpenAI function format schema

### convert_openai_response_to_mcp

**Parameters:**
- `openai_response` (Any): Response from OpenAI function tool

**Returns:**
- `dict`: MCP-formatted response with `success`, `message`, `data` keys

### mcp_tool_error_handler

**Parameters:**
- `context` (RunContextWrapper): Run context (unused)
- `error` (Exception): Exception that occurred

**Returns:**
- `str`: User-friendly error message

### add_task_openai

**Parameters:**
- `user_id` (str): User UUID
- `title` (str): Task title
- `description` (str, optional): Task description

**Returns:**
- `str`: Formatted success/error message

## Future Enhancements

1. **Additional MCP Tools:**
   - `list_tasks`: List tasks with filtering
   - `complete_task`: Mark task as complete
   - `update_task`: Modify task details
   - `delete_task`: Remove a task

2. **Advanced Features:**
   - Tool versioning support
   - Schema validation on conversion
   - Caching for converted schemas
   - Async tool discovery and registration

3. **Monitoring & Observability:**
   - Tool execution metrics
   - Conversion performance tracking
   - Error rate monitoring

## Troubleshooting

### Issue: Tool not found in registry

**Solution:** Ensure tool is registered before use:
```python
tool_registry.register_tool("add_task", ADD_TASK_SCHEMA, AddTaskTool())
```

### Issue: Schema conversion fails

**Solution:** Verify MCP schema has required fields:
```python
assert "name" in mcp_schema
assert "inputSchema" in mcp_schema
assert "properties" in mcp_schema["inputSchema"]
```

### Issue: Tool execution errors

**Solution:** Check error handler is properly configured:
```python
@function_tool(failure_error_function=mcp_tool_error_handler)
async def my_tool(...):
    ...
```

## References

- [OpenAI Agents SDK Documentation](https://openai.github.io/openai-agents-python/)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [Function Calling Guide](https://platform.openai.com/docs/guides/function-calling)

---

**Task:** T032 - Create OpenAI adapter in backend/src/services/
**Status:** ✅ Complete
**Files:**
- `/home/xdev/Hackhthon-II/phase-III/backend/src/services/mcp_openai_adapter.py`
- `/home/xdev/Hackhthon-II/phase-III/backend/tests/unit/test_mcp_openai_adapter.py`
- `/home/xdev/Hackhthon-II/phase-III/backend/docs/mcp_openai_adapter.md`
