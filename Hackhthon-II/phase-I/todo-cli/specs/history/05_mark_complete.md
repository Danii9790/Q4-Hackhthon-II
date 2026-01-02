# PHR-05: Mark Complete Feature

**Date:** 2026-01-02
**Status:** Implemented
**Feature ID:** FR-05
**Author:** Claude Code

---

## Specification

### Overview
Users must be able to toggle task completion status between complete and incomplete.

### Requirements

#### FR-05.1: Command Interface
- Primary command: `complete`
- Short command: `c`
- Case-insensitive matching

#### FR-05.2: Input Collection
1. **Task ID** (Required)
   - Prompt: "Task ID: "
   - Validation: Must match an existing task ID
   - Error: "Error: Task with ID X not found. Type 'list' to see all tasks."

#### FR-05.3: Toggle Behavior
- If task is incomplete → mark as complete
- If task is complete → mark as incomplete (toggle back)
- Toggle is immediate (no confirmation prompt)

#### FR-05.4: Output

**When marking incomplete → complete:**
```
Task marked as complete!
ID: 1
Title: [task title]
Status: Complete ✓
```

**When marking complete → incomplete:**
```
Task marked as incomplete!
ID: 1
Title: [task title]
Status: Incomplete
```

#### FR-05.5: Error Handling
- Invalid task ID: Clear error message with suggestion to use list command
- Non-numeric input: "Error: Invalid task ID. Please enter a number."

---

## Implementation Plan

1. Implement `toggle_complete()` method in `TodoApp` class
2. Toggle the `completed` boolean field
3. Return the task for confirmation display
4. Create CLI handler with input validation
5. Test toggle behavior in both directions

---

## Implementation

### Code Changes (src/main.py)

```python
class TodoApp:
    # ... existing methods ...

    def toggle_complete(self, task_id: int) -> Task:
        """Toggle a task's completion status."""
        task = self._get_task_by_id(task_id)

        if task is None:
            raise ValueError(f"Task with ID {task_id} not found")

        task.completed = not task.completed
        return task

def handle_complete(app: TodoApp) -> None:
    """Handle the toggle complete command."""
    print("\n--- Toggle Task Complete ---")

    # Get task ID
    try:
        task_id_input = input("Task ID: ").strip()
        task_id = int(task_id_input)
    except ValueError:
        print("Error: Invalid task ID. Please enter a number.")
        return

    # Toggle completion status
    try:
        updated_task = app.toggle_complete(task_id)

        if updated_task.completed:
            print(f"\nTask marked as complete!")
            print(f"ID: {updated_task.id}")
            print(f"Title: {updated_task.title}")
            print(f"Status: Complete ✓")
        else:
            print(f"\nTask marked as incomplete!")
            print(f"ID: {updated_task.id}")
            print(f"Title: {updated_task.title}")
            print(f"Status: Incomplete")

    except ValueError as e:
        print(f"Error: {e}")
        print("Type 'list' to see all tasks.")
```

---

## Testing

### Test Case 1: Mark Incomplete Task as Complete
**State:**
- Task 1: "Buy groceries", incomplete

**Input:**
```
> complete
Task ID: 1
```
**Expected Output:**
```
Task marked as complete!
ID: 1
Title: Buy groceries
Status: Complete ✓
```

**Verify with list:**
```
> list
```
**Expected:**
```
--- Your Tasks (1 total) ---

1. [✓] Buy groceries
```

### Test Case 2: Toggle Complete Task Back to Incomplete
**State:**
- Task 1: "Write code", completed

**Input:**
```
> complete
Task ID: 1
```
**Expected Output:**
```
Task marked as incomplete!
ID: 1
Title: Write code
Status: Incomplete
```

**Verify with list:**
```
> list
```
**Expected:**
```
--- Your Tasks (1 total) ---

1. [ ] Write code
```

### Test Case 3: Invalid Task ID
**State:**
- Task 1: "Only task", incomplete

**Input:**
```
> complete
Task ID: 99
```
**Expected Output:**
```
Error: Task with ID 99 not found
Type 'list' to see all tasks.
```

### Test Case 4: Multiple Toggles on Same Task
**State:**
- Task 1: "Toggle test", incomplete

**Actions:**
```
> complete
Task ID: 1
```
**Output:** "Task marked as complete!"

```
> complete
Task ID: 1
```
**Output:** "Task marked as incomplete!"

```
> complete
Task ID: 1
```
**Output:** "Task marked as complete!"

**Verify final state:**
```
> list
```
**Expected:** Task 1 shows `[✓]` (complete)

### Test Case 5: Toggle Task with Description
**State:**
- Task 1: "Important task", "This needs to be done", incomplete

**Input:**
```
> complete
Task ID: 1
```
**Expected Output:**
```
Task marked as complete!
ID: 1
Title: Important task
Status: Complete ✓
```

**Verify description preserved:**
```
> list
```
**Expected:**
```
--- Your Tasks (1 total) ---

1. [✓] Important task
   Description: This needs to be done
```

### Test Case 6: Non-Numeric Task ID
**Input:**
```
> complete
Task ID: abc
```
**Expected Output:**
```
Error: Invalid task ID. Please enter a number.
```

### Test Case 7: Toggle Multiple Tasks
**State:**
- Task 1: "Task 1", incomplete
- Task 2: "Task 2", incomplete
- Task 3: "Task 3", incomplete

**Actions:**
```
> complete
Task ID: 1
> complete
Task ID: 3
```

**Verify:**
```
> list
```
**Expected:**
```
--- Your Tasks (3 total) ---

1. [✓] Task 1

2. [ ] Task 2

3. [✓] Task 3
```

---

## Integration Testing

### Complete Workflow Test
**Scenario:** Full task lifecycle

1. Add task
```
> add
Title: Complete hackathon project
Description: Build todo-cli app
```
**Result:** Task 1 created, incomplete

2. View tasks
```
> list
```
**Result:** Shows Task 1 with [ ]

3. Mark complete
```
> complete
Task ID: 1
```
**Result:** Task 1 marked as complete

4. View again
```
> list
```
**Result:** Shows Task 1 with [✓]

5. Toggle back
```
> complete
Task ID: 1
```
**Result:** Task 1 marked as incomplete

6. View final state
```
> list
```
**Result:** Shows Task 1 with [ ]

---

## Notes

- Toggle behavior allows correcting accidental completions
- Task title and description are never modified by toggle operation
- Status indicator in list command updates immediately after toggle
- The complete command works on tasks regardless of their current state
- No confirmation prompt (quick workflow for power users)
- Status is a boolean field internally (True = complete, False = incomplete)

---

**PHR Version:** 1.0
**Last Updated:** 2026-01-02
