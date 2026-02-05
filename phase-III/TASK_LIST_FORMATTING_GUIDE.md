# Task List Formatting Guide

## Quick Reference

### Function: format_task_list_for_display()

**Purpose:** Transform raw task data into friendly, conversational output with context-aware empty list handling.

**Location:** `backend/src/services/agent.py` (lines 189-260)

## Usage

### Basic Usage

```python
from backend.src.services.agent import format_task_list_for_display

# Empty list - all tasks
tasks = []
result = format_task_list_for_display(tasks, status="all")
# Output: "You don't have any tasks yet. Would you like to create one?"

# Empty list - pending tasks
result = format_task_list_for_display(tasks, status="pending")
# Output: "Great job! You've completed all your tasks! 🎉"

# Empty list - completed tasks
result = format_task_list_for_display(tasks, status="completed")
# Output: "You haven't completed any tasks yet. Keep going!"

# Non-empty list
tasks = [
    {"id": 1, "title": "Buy groceries", "description": "Milk, eggs, bread", "completed": False},
    {"id": 2, "title": "Call dentist", "description": None, "completed": False}
]
result = format_task_list_for_display(tasks, status="pending")
# Output:
# Here's what you have pending:
#
# 1. ○ Buy groceries
#    Milk, eggs, bread (ID: 1)
# 2. ○ Call dentist (ID: 2)
```

## Input Format

### Tasks Array

Each task dictionary must contain:
- `id` (int): Task identifier
- `title` (str): Task title
- `description` (str|None): Optional description
- `completed` (bool): Completion status

### Status Parameter

- `"all"`: Show all tasks
- `"pending"`: Show only incomplete tasks
- `"completed"`: Show only completed tasks

## Output Format

### Empty Lists

| Status    | Message                                                              |
|-----------|----------------------------------------------------------------------|
| all       | You don't have any tasks yet. Would you like to create one?         |
| pending   | Great job! You've completed all your tasks! 🎉                       |
| completed | You haven't completed any tasks yet. Keep going!                     |
| unknown   | You don't have any tasks yet.                                        |

### Non-Empty Lists

Format:
```
{Preamble}

{number}. {indicator} {title}
   {description} (ID: {id})
```

- **Preamble**: Context-aware introduction
- **Indicator**: ○ for pending, ✓ for completed
- **Title**: Task title
- **Description**: Optional, shown on next line if present
- **ID**: Task identifier in parentheses

## Integration Points

### 1. Agent Tool Integration (T041)

The `list_tasks_tool` function automatically uses this formatter:

```python
async def list_tasks_tool(ctx, status: str = "all") -> str:
    result = await list_tasks(user_id, status)
    if result.get("success"):
        tasks_data = result.get("data", [])
        # T042 & T043: Format for conversational display
        formatted_list = format_task_list_for_display(tasks_data, status)
        return formatted_list
```

### 2. Agent Instructions (T040 & T043)

The agent instructions guide the AI on how to handle empty lists:

```python
"""
5. **Empty Task List Handling**: Provide encouraging, context-aware messages
   - When viewing ALL tasks and list is empty:
     → "You don't have any tasks yet. Would you like to create one?"
   - When viewing PENDING tasks and list is empty:
     → "Great job! You've completed all your tasks! 🎉"
   - When viewing COMPLETED tasks and list is empty:
     → "You haven't completed any tasks yet. Keep going!"
"""
```

## Design Principles

### 1. Context-Aware Messages
Different messages based on why the list is empty:
- **New user** (all empty): Guide toward first task
- **Productive user** (pending empty): Celebrate success
- **Inactive user** (completed empty): Encourage progress

### 2. Conversational Tone
- Natural language, not robotic
- Positive reinforcement
- Action-oriented suggestions
- Friendly and approachable

### 3. Readable Format
- Numbered lists for easy scanning
- Clear visual indicators (○ vs ✓)
- Task IDs for reference
- Descriptions on separate lines

### 4. User Guidance
- Suggest next steps
- Celebrate accomplishments
- Encourage progress
- Never just say "no tasks"

## Testing

### Unit Tests

Run the test suite:
```bash
cd backend
pytest tests/unit/test_task_list_formatting.py -v
```

### Manual Testing

Test with the agent:
```bash
# Empty all tasks
User: "Show my tasks"
Agent: "You don't have any tasks yet. Would you like to create one?"

# Empty pending (all tasks completed)
User: "What's pending?"
Agent: "Great job! You've completed all your tasks! 🎉"

# Empty completed (no tasks finished yet)
User: "What have I completed?"
Agent: "You haven't completed any tasks yet. Keep going!"
```

## Extension Points

### Adding New Status Filters

If you add a new status filter (e.g., "overdue"), update:

1. **Empty list handler** (line 210-221):
```python
elif status == "overdue":
    return "You don't have any overdue tasks. Good job staying on track!"
```

2. **Preamble generator** (line 233-241):
```python
elif status == "overdue":
    preamble = "Here are your overdue tasks:\n\n"
```

### Customizing Messages

To change a message, update the appropriate line in the empty list handler:

```python
if status == "all":
    # Customize this message
    return "Your customized message here"
```

## Related Documentation

- **T042 Implementation**: Conversational response formatting
- **T043 Implementation**: Empty task list handling
- **Agent Instructions**: backend/src/services/agent.py (lines 54-182)
- **Unit Tests**: backend/tests/unit/test_task_list_formatting.py

## Support

For issues or questions:
1. Check the unit tests for examples
2. Review the implementation summary: T043_IMPLEMENTATION_SUMMARY.md
3. Consult the task definition: specs/001-todo-ai-chatbot/tasks.md (line 143)
