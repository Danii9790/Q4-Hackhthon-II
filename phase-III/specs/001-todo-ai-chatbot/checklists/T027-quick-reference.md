# T027: Add Task Validation - Quick Reference

## File Location
`/home/xdev/Hackhthon-II/phase-III/backend/src/mcp_tools/add_task.py`

## Validation Rules

### Title (Required)
| Input | Result | Error Message |
|-------|--------|---------------|
| `"Buy groceries"` | ✅ Pass | - |
| `"  Task  "` | ✅ Pass (stripped to "Task") | - |
| `None` | ❌ Fail | "Task title is required and cannot be empty" |
| `""` | ❌ Fail | "Task title is required and cannot be empty or only whitespace" |
| `"   "` | ❌ Fail | "Task title is required and cannot be empty or only whitespace" |
| `"a" * 501` | ❌ Fail | "Task title cannot exceed 500 characters (got 501 characters)" |
| `"a" * 500` | ✅ Pass | - |
| `123` | ❌ Fail | "Task title must be a string, got int" |

### Description (Optional)
| Input | Result | Error Message |
|-------|--------|---------------|
| `"Details here"` | ✅ Pass | - |
| `None` | ✅ Pass | - |
| `""` | ✅ Pass (converted to None) | - |
| `"   "` | ✅ Pass (converted to None) | - |
| `"a" * 5001` | ❌ Fail | "Task description cannot exceed 5000 characters (got 5001 characters)" |
| `"a" * 5000` | ✅ Pass | - |
| `12345` | ❌ Fail | "Task description must be a string, got int" |

### User ID (Required, via BaseMCPTool)
| Input | Result | Error Message |
|-------|--------|---------------|
| `"550e8400-e29b-41d4-a716-446655440000"` | ✅ Pass | - |
| `None` | ❌ Fail | "User ID is required" |
| `""` | ❌ Fail | "User ID is required" |
| `"not-a-uuid"` | ❌ Fail | "Invalid user ID format: ..." |

## Validation Order

The `execute` method validates in this order:

1. **user_id** → UUID format check
2. **title** → Required, type, empty, length check
3. **description** → Optional, type, length check
4. **Database insertion** → Only if ALL validations pass

## Error Response Format

All validation errors return:

```python
{
    "success": False,
    "error": "<Human-readable message>",
    "code": "TASK_VALIDATION_ERROR" or "USER_VALIDATION_ERROR"
}
```

## Usage Example

```python
from src.mcp_tools.add_task import add_task

# Valid task
result = await add_task(
    user_id="550e8400-e29b-41d4-a716-446655440000",
    title="Buy groceries",
    description="Milk, eggs, bread"
)
# Returns: {"success": True, "message": "Task created successfully", "data": {...}}

# Invalid title (empty)
result = await add_task(
    user_id="550e8400-e29b-41d4-a716-446655440000",
    title=""
)
# Raises: TaskValidationError("Task title is required and cannot be empty or only whitespace")

# Title too long
result = await add_task(
    user_id="550e8400-e29b-41d4-a716-446655440000",
    title="a" * 501
)
# Raises: TaskValidationError("Task title cannot exceed 500 characters (got 501 characters)")

# Invalid user_id
result = await add_task(
    user_id="not-a-uuid",
    title="Test"
)
# Raises: UserValidationError("Invalid user ID format: ...")
```

## Key Features

✅ **Type Safety**: Explicit type checking for all inputs  
✅ **Whitespace Handling**: Automatic stripping of leading/trailing whitespace  
✅ **Clear Errors**: AI-friendly error messages with specific details  
✅ **Optional Fields**: Proper handling of optional description field  
✅ **Early Validation**: All validation BEFORE database operations  
✅ **Comprehensive Logging**: Warning/error logs for all validation failures  
✅ **Testable**: Separated validation methods for unit testing  

## Integration Notes

- Already exported in `src/mcp_tools/__init__.py`
- Ready for MCP server registration in T028
- Compatible with OpenAI Agents SDK tool format
- Inherits error handling from BaseMCPTool
