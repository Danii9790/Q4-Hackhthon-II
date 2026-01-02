# PHR-04: Delete Task Feature

**Date:** 2026-01-02
**Status:** Implemented
**Feature ID:** FR-04
**Author:** Claude Code

---

## Specification

### Overview
Users must be able to delete tasks from their todo list by task ID.

### Requirements

#### FR-04.1: Command Interface
- Primary command: `delete`
- Short command: `d`
- Case-insensitive matching

#### FR-04.2: Input Collection
1. **Task ID** (Required)
   - Prompt: "Task ID: "
   - Validation: Must match an existing task ID
   - Error: "Error: Task with ID X not found. Type 'list' to see all tasks."

#### FR-04.3: Deletion Behavior
- Remove task from in-memory task list
- Task ID is not reused (gap in numbering is acceptable)
- No confirmation prompt (immediate deletion)
- Deleted task cannot be recovered

#### FR-04.4: Output
**Success message format:**
```
Task deleted successfully!
ID: 1
Title: [deleted task title]
```

#### FR-04.5: Error Handling
- Invalid task ID: Clear error message with suggestion to use list command
- Non-numeric input: "Error: Invalid task ID. Please enter a number."

---

## Implementation Plan

1. Implement `delete_task()` method in `TodoApp` class
2. Store deleted task info for confirmation message
3. Create CLI handler with input validation
4. Test deletion of single task and multiple tasks
5. Verify task IDs are not reused

---

## Implementation

### Code Changes (src/main.py)

```python
class TodoApp:
    # ... existing methods ...

    def delete_task(self, task_id: int) -> Task:
        """Delete a task by ID and return the deleted task."""
        for i, task in enumerate(self.tasks):
            if task.id == task_id:
                deleted_task = self.tasks.pop(i)
                return deleted_task
        raise ValueError(f"Task with ID {task_id} not found")

def handle_delete(app: TodoApp) -> None:
    """Handle the delete task command."""
    print("\n--- Delete Task ---")

    # Get task ID
    try:
        task_id_input = input("Task ID: ").strip()
        task_id = int(task_id_input)
    except ValueError:
        print("Error: Invalid task ID. Please enter a number.")
        return

    # Delete the task
    try:
        deleted_task = app.delete_task(task_id)

        print(f"\nTask deleted successfully!")
        print(f"ID: {deleted_task.id}")
        print(f"Title: {deleted_task.title}")

    except ValueError as e:
        print(f"Error: {e}")
        print("Type 'list' to see all tasks.")
```

---

## Testing

### Test Case 1: Delete Single Task
**State:**
- Task 1: "Task 1", "Description 1", incomplete
- Task 2: "Task 2", "Description 2", incomplete
- Task 3: "Task 3", "Description 3", incomplete

**Input:**
```
> delete
Task ID: 2
```
**Expected Output:**
```
Task deleted successfully!
ID: 2
Title: Task 2
```

**Verify:**
```
> list
```
**Expected:**
```
--- Your Tasks (2 total) ---

1. [ ] Task 1

3. [ ] Task 3
```

### Test Case 2: Delete Non-Existent Task
**State:**
- Task 1: "Task 1", incomplete

**Input:**
```
> delete
Task ID: 999
```
**Expected Output:**
```
Error: Task with ID 999 not found
Type 'list' to see all tasks.
```

### Test Case 3: Delete All Tasks One by One
**State:**
- Task 1: "First task", incomplete
- Task 2: "Second task", incomplete

**Input:**
```
> delete
Task ID: 1
> delete
Task ID: 2
> list
```
**Expected Output:**
```
--- Your Tasks (0 total) ---

No tasks yet. Type 'add' to create your first task!
```

### Test Case 4: Delete Task with Long Title and Description
**State:**
- Task 1: "This is a very long task title with lots of words", "This is also a very long description with many details", incomplete

**Input:**
```
> delete
Task ID: 1
```
**Expected Output:**
```
Task deleted successfully!
ID: 1
Title: This is a very long task title with lots of words
```

### Test Case 5: Delete Completed Task
**State:**
- Task 1: "Completed task", "Done", completed

**Input:**
```
> delete
Task ID: 1
```
**Expected Output:**
```
Task deleted successfully!
ID: 1
Title: Completed task
```

### Test Case 6: Non-Numeric Task ID
**Input:**
```
> delete
Task ID: abc
```
**Expected Output:**
```
Error: Invalid task ID. Please enter a number.
```

### Test Case 7: Verify ID Gaps Remain
**State:**
- Task 1: "Task 1", incomplete
- Task 2: "Task 2", incomplete
- Task 3: "Task 3", incomplete

**Actions:**
```
> delete
Task ID: 2

> add
Title: New Task
Description: [Enter]
```

**Verify:**
```
> list
```
**Expected:**
```
--- Your Tasks (3 total) ---

1. [ ] Task 1

3. [ ] Task 3

4. [ ] New Task
```

**Note:** New task gets ID 4, not 2 (gap remains)

---

## Notes

- Deletion is immediate (no undo/confirmation prompt)
- Task IDs are never reused, creating gaps in numbering
- Deleting a task shifts no other IDs (they retain their original IDs)
- Deleting from empty list shows error, not crash
- Completion status has no effect on deletion capability
- The `next_id` counter continues incrementing, never decreasing

---

**PHR Version:** 1.0
**Last Updated:** 2026-01-02
