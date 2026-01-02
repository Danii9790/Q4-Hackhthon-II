# PHR-02: View Tasks Feature

**Date:** 2026-01-02
**Status:** Implemented
**Feature ID:** FR-02
**Author:** Claude Code

---

## Specification

### Overview
Users must be able to view all tasks in their todo list with clear status indicators.

### Requirements

#### FR-02.1: Command Interface
- Primary command: `list`
- Short command: `l`
- Case-insensitive matching

#### FR-02.2: Display Format
For each task, display:
- Task ID (sequential number)
- Status indicator: `[✓]` for complete, `[ ]` for incomplete
- Task title
- Task description (if present)

#### FR-02.3: Output Format
```
--- Your Tasks (X total) ---

1. [ ] Task title 1
   Description: Optional description

2. [✓] Task title 2
   Description: Another description

3. [ ] Task title 3
```

#### FR-02.4: Empty State
When no tasks exist:
```
--- Your Tasks (0 total) ---

No tasks yet. Type 'add' to create your first task!
```

#### FR-02.5: Task Display Rules
- Show description indented under title if not empty
- Use `[✓]` for completed tasks
- Use `[ ]` for incomplete tasks
- Number tasks sequentially starting from 1
- Display total count in header

---

## Implementation Plan

1. Implement `list_tasks()` method in `TodoApp` class
2. Create formatting method for individual tasks
3. Handle empty list case
4. Create CLI handler for list command
5. Test with various task states

---

## Implementation

### Code Changes (src/main.py)

```python
class TodoApp:
    # ... existing methods ...

    def list_tasks(self) -> None:
        """Display all tasks with status indicators."""
        if not self.tasks:
            print("\n--- Your Tasks (0 total) ---")
            print("\nNo tasks yet. Type 'add' to create your first task!")
            return

        print(f"\n--- Your Tasks ({len(self.tasks)} total) ---")

        for task in self.tasks:
            status = "[✓]" if task.completed else "[ ]"
            print(f"\n{task.id}. {status} {task.title}")

            if task.description:
                print(f"   Description: {task.description}")

        print()  # Empty line at end

def handle_list(app: TodoApp) -> None:
    """Handle the list tasks command."""
    app.list_tasks()
```

---

## Testing

### Test Case 1: Empty Task List
**State:** No tasks
**Input:**
```
> list
```
**Expected Output:**
```
--- Your Tasks (0 total) ---

No tasks yet. Type 'add' to create your first task!
```

### Test Case 2: Single Incomplete Task
**State:** One task: ID=1, "Buy groceries", incomplete
**Input:**
```
> list
```
**Expected Output:**
```
--- Your Tasks (1 total) ---

1. [ ] Buy groceries
```

### Test Case 3: Single Complete Task
**State:** One task: ID=1, "Write code", completed
**Input:**
```
> list
```
**Expected Output:**
```
--- Your Tasks (1 total) ---

1. [✓] Write code
```

### Test Case 4: Mixed Tasks with Descriptions
**State:**
- Task 1: "Task 1", incomplete, no description
- Task 2: "Task 2", complete, with description
- Task 3: "Task 3", incomplete, with description

**Input:**
```
> list
```
**Expected Output:**
```
--- Your Tasks (3 total) ---

1. [ ] Task 1

2. [✓] Task 2
   Description: This task is complete

3. [ ] Task 3
   Description: This task needs work
```

### Test Case 5: Long Title Handling
**State:** Task with very long title (200 chars)
**Input:**
```
> list
```
**Expected Output:** Title displays on single line (no wrapping)

---

## Notes

- Task IDs displayed are the actual task.id values, not array indices
- Empty string descriptions are not displayed
- Status indicators use Unicode checkmark (✓)
- Total count reflects all tasks regardless of completion status
- Tasks maintain insertion order (not sorted by ID or status)

---

**PHR Version:** 1.0
**Last Updated:** 2026-01-02
