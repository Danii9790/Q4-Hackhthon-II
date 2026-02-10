# MCP Tools Schema - Phase V

**Feature**: Advanced Cloud Deployment
**Last Updated**: 2026-02-10
**MCP SDK Version**: Official Python MCP SDK

---

## Overview

Phase V extends the existing MCP tools with 9 new tools for advanced task management. All tools maintain the stateless architecture principle and publish events to Kafka after successful operations.

---

## Tool Catalog

### Existing Tools (Extended)

#### 1. add_task
**Status**: ✅ Existing - **Extended for Phase V**

**Description**: Create a new task with optional due date, priority, and tags.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "title": {
      "type": "string",
      "description": "Task title (required)"
    },
    "description": {
      "type": "string",
      "description": "Task description (optional)"
    },
    "due_date": {
      "type": "string",
      "format": "date-time",
      "description": "Due date in ISO 8601 format (UTC, optional)"
    },
    "priority": {
      "type": "string",
      "enum": ["LOW", "MEDIUM", "HIGH"],
      "description": "Task priority level (default: MEDIUM)"
    },
    "tags": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "maxItems": 10,
      "description": "List of tags (e.g., ['work', 'urgent'])"
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
      "type": "boolean"
    },
    "task": {
      "type": "object",
      "properties": {
        "id": {"type": "string"},
        "title": {"type": "string"},
        "description": {"type": "string"},
        "due_date": {"type": "string", "format": "date-time"},
        "priority": {"type": "string"},
        "tags": {"type": "array", "items": {"type": "string"}},
        "completed": {"type": "boolean"},
        "created_at": {"type": "string", "format": "date-time"}
      }
    },
    "message": {
      "type": "string"
    }
  }
}
```

**Side Effects**:
- Creates Task record in database
- Creates TaskEvent (event_type='created') in audit trail
- Publishes event to Kafka topic `task-events`

**Example Usage**:
```
User: "Add a high priority task called 'Finish presentation' due tomorrow with tags 'work' and 'urgent'"

Agent calls:
add_task(
  title="Finish presentation",
  priority="HIGH",
  due_date="2026-02-11T17:00:00Z",
  tags=["work", "urgent"]
)
```

---

#### 2. update_task
**Status**: ✅ Existing - **Extended for Phase V**

**Description**: Update an existing task's title, description, due date, priority, or tags.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "task_id": {
      "type": "string",
      "description": "Task ID (UUID)"
    },
    "title": {
      "type": "string",
      "description": "New task title (optional)"
    },
    "description": {
      "type": "string",
      "description": "New task description (optional)"
    },
    "due_date": {
      "type": "string",
      "format": "date-time",
      "description": "New due date in ISO 8601 format (UTC, optional)"
    },
    "priority": {
      "type": "string",
      "enum": ["LOW", "MEDIUM", "HIGH"],
      "description": "New priority level (optional)"
    },
    "tags": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "maxItems": 10,
      "description": "New list of tags (replaces existing tags, optional)"
    }
  },
  "required": ["task_id"]
}
```

**Output Schema**: Same as `add_task`

**Side Effects**:
- Updates Task record in database
- Creates TaskEvent (event_type='updated') with before/after state
- Publishes event to Kafka topic `task-events`
- Publishes event to Kafka topic `task-updates` (real-time sync)

**Example Usage**:
```
User: "Change task 123 priority to high"

Agent calls:
update_task(task_id="123", priority="HIGH")
```

---

#### 3. complete_task
**Status**: ✅ Existing - **Extended for Phase V**

**Description**: Mark a task as complete.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "task_id": {
      "type": "string",
      "description": "Task ID (UUID)"
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
      "type": "boolean"
    },
    "task": {
      "type": "object",
      "properties": {
        "id": {"type": "string"},
        "completed": {"type": "boolean"},
        "completed_at": {"type": "string", "format": "date-time"}
      }
    },
    "message": {
      "type": "string"
    },
    "next_occurrence": {
      "type": "object",
      "description": "If task is recurring, contains next occurrence details",
      "properties": {
        "id": {"type": "string"},
        "title": {"type": "string"},
        "due_date": {"type": "string", "format": "date-time"}
      }
    }
  }
}
```

**Side Effects**:
- Updates Task.completed=true, Task.completed_at=NOW()
- Creates TaskEvent (event_type='completed')
- Publishes event to Kafka topic `task-events`
- **NEW**: If task has recurring_task_id, Recurring Task Service creates next occurrence

**Example Usage**:
```
User: "Complete my daily standup task"

Agent calls:
complete_task(task_id="456")

Response includes:
{
  "success": true,
  "message": "Task completed! Next occurrence created for tomorrow at 9:00 AM",
  "next_occurrence": {
    "id": "789",
    "title": "Daily standup",
    "due_date": "2026-02-11T09:00:00Z"
  }
}
```

---

#### 4. delete_task
**Status**: ✅ Existing - **Extended for Phase V**

**Description**: Delete a task permanently.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "task_id": {
      "type": "string",
      "description": "Task ID (UUID)"
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
      "type": "boolean"
    },
    "message": {
      "type": "string"
    }
  }
}
```

**Side Effects**:
- Deletes Task record from database (soft delete or hard delete)
- Creates TaskEvent (event_type='deleted') with full task data in event_data
- Publishes event to Kafka topic `task-events`
- Publishes event to Kafka topic `task-updates` (real-time sync)
- **NEW**: Deletes associated Reminders

---

#### 5. list_tasks
**Status**: ✅ Existing - **Extended for Phase V**

**Description**: List all tasks for the current user with optional filtering and sorting.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "priority": {
      "type": "string",
      "enum": ["LOW", "MEDIUM", "HIGH"],
      "description": "Filter by priority level (optional)"
    },
    "tags": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "Filter by tags (e.g., ['work', 'urgent'])"
    },
    "due_before": {
      "type": "string",
      "format": "date-time",
      "description": "Filter tasks due before this date (ISO 8601, optional)"
    },
    "due_after": {
      "type": "string",
      "format": "date-time",
      "description": "Filter tasks due after this date (ISO 8601, optional)"
    },
    "completed": {
      "type": "boolean",
      "description": "Filter by completion status (optional)"
    },
    "sort_by": {
      "type": "string",
      "enum": ["due_date", "priority", "created_at", "completed_at"],
      "description": "Sort field (default: created_at)"
    },
    "sort_order": {
      "type": "string",
      "enum": ["asc", "desc"],
      "description": "Sort order (default: desc)"
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100,
      "default": 10,
      "description": "Number of tasks to return"
    }
  }
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "tasks": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {"type": "string"},
          "title": {"type": "string"},
          "description": {"type": "string"},
          "due_date": {"type": "string", "format": "date-time"},
          "priority": {"type": "string"},
          "tags": {"type": "array", "items": {"type": "string"}},
          "completed": {"type": "boolean"},
          "created_at": {"type": "string", "format": "date-time"}
        }
      }
    },
    "total": {
      "type": "integer",
      "description": "Total number of tasks matching filters"
    }
  }
}
```

**Example Usage**:
```
User: "Show me all high priority work tasks due this week"

Agent calls:
list_tasks(
  priority="HIGH",
  tags=["work"],
  due_after="2026-02-10T00:00:00Z",
  due_before="2026-02-16T23:59:59Z",
  sort_by="due_date",
  sort_order="asc"
)
```

---

### New Tools (Phase V)

#### 6. set_task_priority 🆕
**Status**: NEW for Phase V

**Description**: Update the priority level of a specific task.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "task_id": {
      "type": "string",
      "description": "Task ID (UUID)"
    },
    "priority": {
      "type": "string",
      "enum": ["LOW", "MEDIUM", "HIGH"],
      "description": "New priority level"
    }
  },
  "required": ["task_id", "priority"]
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "success": {
      "type": "boolean"
    },
    "task": {
      "type": "object",
      "properties": {
        "id": {"type": "string"},
        "title": {"type": "string"},
        "priority": {"type": "string"}
      }
    },
    "message": {
      "type": "string"
    }
  }
}
```

**Side Effects**:
- Updates Task.priority in database
- Creates TaskEvent (event_type='updated')
- Publishes events to Kafka (`task-events`, `task-updates`)

**Example Usage**:
```
User: "Mark task 123 as high priority"

Agent calls:
set_task_priority(task_id="123", priority="HIGH")
```

---

#### 7. set_task_due_date 🆕
**Status**: NEW for Phase V

**Description**: Set or update the due date for a task.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "task_id": {
      "type": "string",
      "description": "Task ID (UUID)"
    },
    "due_date": {
      "type": "string",
      "format": "date-time",
      "description": "Due date in ISO 8601 format (UTC)"
    }
  },
  "required": ["task_id", "due_date"]
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "success": {
      "type": "boolean"
    },
    "task": {
      "type": "object",
      "properties": {
        "id": {"type": "string"},
        "title": {"type": "string"},
        "due_date": {"type": "string", "format": "date-time"}
      }
    },
    "message": {
      "type": "string"
    }
  }
}
```

**Side Effects**:
- Updates Task.due_date in database
- Creates TaskEvent (event_type='updated')
- Publishes events to Kafka

**Example Usage**:
```
User: "Set the due date for task 123 to tomorrow at 5 PM"

Agent calls:
set_task_due_date(task_id="123", due_date="2026-02-11T17:00:00Z")
```

---

#### 8. add_task_tags 🆕
**Status**: NEW for Phase V

**Description**: Add tags to an existing task (tags are appended, not replaced).

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "task_id": {
      "type": "string",
      "description": "Task ID (UUID)"
    },
    "tags": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "maxItems": 10,
      "description": "Tags to add (appended to existing tags)"
    }
  },
  "required": ["task_id", "tags"]
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "success": {
      "type": "boolean"
    },
    "task": {
      "type": "object",
      "properties": {
        "id": {"type": "string"},
        "title": {"type": "string"},
        "tags": {
          "type": "array",
          "items": {"type": "string"}
        }
      }
    },
    "message": {
      "type": "string"
    }
  }
}
```

**Side Effects**:
- Appends tags to Task.tags array in database
- Creates TaskEvent (event_type='updated')
- Publishes events to Kafka

**Example Usage**:
```
User: "Add tags 'urgent' and 'bug' to task 123"

Agent calls:
add_task_tags(task_id="123", tags=["urgent", "bug"])
```

---

#### 9. search_tasks 🆕
**Status**: NEW for Phase V

**Description**: Full-text search across task titles and descriptions.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "description": "Search query (searches title and description)"
    },
    "limit": {
      "type": "integer",
      "minimum": 1,
      "maximum": 100,
      "default": 10
    }
  },
  "required": ["query"]
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "tasks": {
      "type": "array",
      "items": {
        "type": "object"
      }
    },
    "total": {
      "type": "integer"
    }
  }
}
```

**Example Usage**:
```
User: "Search for tasks containing 'meeting'"

Agent calls:
search_tasks(query="meeting")
```

---

#### 10. filter_tasks 🆕
**Status**: NEW for Phase V

**Description**: Advanced filtering with multiple criteria (priority, tags, due date range, completion status).

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "priority": {
      "type": "string",
      "enum": ["LOW", "MEDIUM", "HIGH"],
      "description": "Filter by priority"
    },
    "tags": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "Filter by tags (must have ALL specified tags)"
    },
    "due_before": {
      "type": "string",
      "format": "date-time",
      "description": "Filter tasks due before this date"
    },
    "due_after": {
      "type": "string",
      "format": "date-time",
      "description": "Filter tasks due after this date"
    },
    "completed": {
      "type": "boolean",
      "description": "Filter by completion status"
    },
    "sort_by": {
      "type": "string",
      "enum": ["due_date", "priority", "created_at"]
    },
    "sort_order": {
      "type": "string",
      "enum": ["asc", "desc"]
    },
    "limit": {
      "type": "integer",
      "default": 10
    }
  }
}
```

**Output Schema**: Same as `list_tasks`

**Example Usage**:
```
User: "Show me incomplete high priority tasks tagged 'work' due this week"

Agent calls:
filter_tasks(
  priority="HIGH",
  tags=["work"],
  due_after="2026-02-10T00:00:00Z",
  due_before="2026-02-16T23:59:59Z",
  completed=false,
  sort_by="due_date",
  sort_order="asc"
)
```

---

#### 11. sort_tasks 🆕
**Status**: NEW for Phase V

**Description**: Sort tasks by a specific field and return them.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "sort_by": {
      "type": "string",
      "enum": ["due_date", "priority", "created_at", "completed_at"],
      "description": "Field to sort by"
    },
    "sort_order": {
      "type": "string",
      "enum": ["asc", "desc"],
      "description": "Sort order"
    },
    "limit": {
      "type": "integer",
      "default": 10
    }
  },
  "required": ["sort_by"]
}
```

**Output Schema**: Same as `list_tasks`

**Example Usage**:
```
User: "Show my tasks sorted by due date, nearest first"

Agent calls:
sort_tasks(sort_by="due_date", sort_order="asc", limit=20)
```

---

#### 12. create_recurring_task 🆕
**Status**: NEW for Phase V

**Description**: Create a recurring task template that generates task occurrences automatically.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "title": {
      "type": "string",
      "description": "Task title"
    },
    "description": {
      "type": "string",
      "description": "Task description (optional)"
    },
    "frequency": {
      "type": "string",
      "enum": ["DAILY", "WEEKLY", "MONTHLY"],
      "description": "How often the task repeats"
    },
    "start_date": {
      "type": "string",
      "format": "date-time",
      "description": "First occurrence date (ISO 8601, UTC)"
    },
    "end_date": {
      "type": "string",
      "format": "date-time",
      "description": "Optional last occurrence date"
    }
  },
  "required": ["title", "frequency", "start_date"]
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "success": {
      "type": "boolean"
    },
    "recurring_task": {
      "type": "object",
      "properties": {
        "id": {"type": "string"},
        "title": {"type": "string"},
        "frequency": {"type": "string"},
        "start_date": {"type": "string", "format": "date-time"},
        "end_date": {"type": "string", "format": "date-time"},
        "next_occurrence": {"type": "string", "format": "date-time"}
      }
    },
    "first_occurrence": {
      "type": "object",
      "description": "The first generated task occurrence",
      "properties": {
        "id": {"type": "string"},
        "title": {"type": "string"},
        "due_date": {"type": "string", "format": "date-time"}
      }
    },
    "message": {
      "type": "string"
    }
  }
}
```

**Side Effects**:
- Creates RecurringTask record in database
- Creates first Task occurrence with recurring_task_id set
- Creates TaskEvent (event_type='created')

**Example Usage**:
```
User: "Create a daily recurring task 'Check emails' starting tomorrow at 9 AM"

Agent calls:
create_recurring_task(
  title="Check emails",
  frequency="DAILY",
  start_date="2026-02-11T09:00:00Z"
)
```

---

#### 13. list_reminders 🆕
**Status**: NEW for Phase V

**Description**: List all upcoming reminders for the current user.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "upcoming": {
      "type": "boolean",
      "default": true,
      "description": "Only show unsent reminders due in the future"
    },
    "limit": {
      "type": "integer",
      "default": 10,
      "maximum": 100
    }
  }
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "reminders": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {"type": "string"},
          "task_id": {"type": "string"},
          "task_title": {"type": "string"},
          "remind_at": {"type": "string", "format": "date-time"},
          "sent": {"type": "boolean"}
        }
      }
    },
    "total": {
      "type": "integer"
    }
  }
}
```

**Example Usage**:
```
User: "Show my upcoming reminders"

Agent calls:
list_reminders(upcoming=true, limit=10)
```

---

## Tool Naming Convention

All tools follow the pattern: `<verb>_<noun>`

- **Verbs**: add, create, update, delete, complete, set, list, search, filter, sort
- **Nouns**: task, tasks, recurring_task, reminders

This ensures consistency and predictability for AI agent training.

---

## Error Handling

All tools return errors in the following format:

```json
{
  "success": false,
  "error": {
    "code": "TASK_NOT_FOUND",
    "message": "Task with ID '123' not found",
    "details": {
      "task_id": "123",
      "user_id": "abc-123"
    }
  }
}
```

**Common Error Codes**:
- `TASK_NOT_FOUND`: Task ID doesn't exist or belongs to another user
- `VALIDATION_ERROR`: Invalid input (e.g., due_date in the past)
- `DUPLICATE_TASK`: Task with same title and due date already exists
- `MAX_TAGS_EXCEEDED`: More than 10 tags provided
- `INVALID_FREQUENCY`: Invalid recurrence frequency

---

## Kafka Event Publishing

All tools that modify state publish events to Kafka after successful database operations:

### Event Structure
```json
{
  "event_type": "created|updated|completed|deleted",
  "task_id": "uuid",
  "user_id": "uuid",
  "timestamp": "2026-02-10T12:00:00Z",
  "event_data": {
    "before": { ... },
    "after": { ... },
    "changes": ["title", "priority"]
  }
}
```

### Topics
- `task-events`: All task CRUD operations (consumed by audit service, recurring task service)
- `task-updates`: All task updates (consumed by WebSocket gateway for real-time sync)
- `reminders`: Reminder triggers (consumed by notification service)

---

**END OF MCP TOOLS SCHEMA**
