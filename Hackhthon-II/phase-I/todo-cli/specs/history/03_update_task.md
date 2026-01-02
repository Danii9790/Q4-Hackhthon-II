# PHR-03: Update Task Feature

**Date:** 2026-01-02
**Status:** Implemented
**Feature ID:** FR-03
**Author:** Claude Code

---

## Specification

### Overview
Users must be able to update the title and/or description of existing tasks.

### Requirements

#### FR-03.1: Command Interface
- Primary command: `update`
- Short command: `u`
- Case-insensitive matching

#### FR-03.2: Input Collection
1. **Task ID** (Required)
   - Prompt: "Task ID: "
   - Validation: Must match an existing task ID
   - Error: "Error: Task with ID X not found. Type 'list' to see all tasks."

2. **New Title** (Required)
   - Prompt: "New title: "
   - Validation: Cannot be empty or whitespace only
   - Error: "Error: Title cannot be empty. Please try again."

3. **New Description** (Optional)
   - Prompt: "New description (press Enter to keep current): "
   - Behavior: Keep existing description if user presses Enter
   - Empty input: Clears description if user enters spaces then Enter

#### FR-03.3: Update Logic
- Update title only (keep description)
- Update description only (keep title)
- Update both title and description
- Preserve task completion status

#### FR-03.4: Output
**Success message format:**
```
Task updated successfully!
ID: 1
Title: [new title]
Description: [new description or "None"]
Status: [current status]
```

#### FR-03.5: Error Handling
- Invalid task ID: Clear error message with suggestion to use list command
- Empty title: Prompt again until valid input received

---

## Implementation Plan

1. Implement `_get_task_by_id()` helper method for ID lookup
2. Implement `update_task()` method in `TodoApp` class
3. Handle title and description updates separately
4. Create CLI handler with input validation
5. Test with various update scenarios

---

## Implementation

### Code Changes (src/main.py)

```python
class TodoApp:
    # ... existing methods ...

    def _get_task_by_id(self, task_id: int) -> Task | None:
        """Find a task by its ID. Returns None if not found."""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def update_task(
        self,
        task_id: int,
        new_title: str | None = None,
        new_description: str | None = None
    ) -> Task:
        """Update an existing task's title and/or description."""
        task = self._get_task_by_id(task_id)

        if task is None:
            raise ValueError(f"Task with ID {task_id} not found")

        if new_title is not None:
            task.title = new_title.strip()

        if new_description is not None:
            task.description = new_description.strip()

        return task

def handle_update(app: TodoApp) -> None:
    """Handle the update task command."""
    print("\n--- Update Task ---")

    # Get task ID
    try:
        task_id_input = input("Task ID: ").strip()
        task_id = int(task_id_input)
    except ValueError:
        print("Error: Invalid task ID. Please enter a number.")
        return

    # Get new title
    while True:
        new_title = input("New title: ").strip()
        if new_title:
            break
        print("Error: Title cannot be empty. Please try again.")

    # Get new description (optional)
    new_description = input("New description (press Enter to keep current): ").strip()

    # Check if user wants to keep current description
    task = app._get_task_by_id(task_id)
    if task is None:
        print(f"Error: Task with ID {task_id} not found. Type 'list' to see all tasks.")
        return

    if not new_description:
        new_description = task.description  # Keep current

    # Update the task
    try:
        updated_task = app.update_task(task_id, new_title, new_description)

        print(f"\nTask updated successfully!")
        print(f"ID: {updated_task.id}")
        print(f"Title: {updated_task.title}")
        print(f"Description: {updated_task.description if updated_task.description else 'None'}")
        print(f"Status: {'Complete' if updated_task.completed else 'Incomplete'}")

    except ValueError as e:
        print(f"Error: {e}")
```

---

## Testing

### Test Case 1: Update Title Only
**State:**
- Task 1: "Old title", "Original description", incomplete

**Input:**
```
> update
Task ID: 1
New title: New title
New description (press Enter to keep current): [Enter]
```
**Expected Output:**
```
Task updated successfully!
ID: 1
Title: New title
Description: Original description
Status: Incomplete
```

### Test Case 2: Update Both Title and Description
**State:**
- Task 1: "Old title", "Old description", incomplete

**Input:**
```
> update
Task ID: 1
New title: Completely new title
New description (press Enter to keep current): Completely new description
```
**Expected Output:**
```
Task updated successfully!
ID: 1
Title: Completely new title
Description: Completely new description
Status: Incomplete
```

### Test Case 3: Update Description Only
**State:**
- Task 1: "Keep this title", "Old description", incomplete

**Input:**
```
> update
Task ID: 1
New title: Keep this title
New description (press Enter to keep current): New description only
```
**Expected Output:**
```
Task updated successfully!
ID: 1
Title: Keep this title
Description: New description only
Status: Incomplete
```

### Test Case 4: Invalid Task ID
**State:** No tasks
**Input:**
```
> update
Task ID: 999
```
**Expected Output:**
```
Error: Task with ID 999 not found. Type 'list' to see all tasks.
```

### Test Case 5: Empty Title Validation
**State:**
- Task 1: "Original title", "Description", incomplete

**Input:**
```
> update
Task ID: 1
New title: [Enter]
Error: Title cannot be empty. Please try again.
New title: Valid new title
New description (press Enter to keep current): [Enter]
```
**Expected Output:**
```
Task updated successfully!
ID: 1
Title: Valid new title
Description: Description
Status: Incomplete
```

### Test Case 6: Non-Numeric Task ID
**Input:**
```
> update
Task ID: abc
```
**Expected Output:**
```
Error: Invalid task ID. Please enter a number.
```

---

## Notes

- Original task ID is preserved (no renumbering)
- Task completion status is never changed by update operation
- Empty description input (just Enter) preserves existing description
- Whitespace-only inputs are trimmed to empty strings
- Updates are immediate (no confirmation step)

---

**PHR Version:** 1.0
**Last Updated:** 2026-01-02
