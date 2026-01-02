# PHR-01: Add Task Feature

**Date:** 2026-01-02
**Status:** Implemented
**Feature ID:** FR-01
**Author:** Claude Code

---

## Specification

### Overview
Users must be able to add new tasks to their todo list with a title and optional description.

### Requirements

#### FR-01.1: Command Interface
- Primary command: `add`
- Short command: `a`
- Case-insensitive matching

#### FR-01.2: Input Collection
1. **Title** (Required)
   - Prompt: "Title: "
   - Validation: Cannot be empty or whitespace only
   - Max length: 200 characters

2. **Description** (Optional)
   - Prompt: "Description (press Enter to skip): "
   - Default: Empty string if user presses Enter
   - Max length: 500 characters

#### FR-01.3: Task Generation
- Auto-generate unique sequential task ID starting from 1
- Initial status: Incomplete (completed = False)
- Store task in memory

#### FR-01.4: Output
- Success message format:
  ```
  Task added successfully!
  ID: 1
  Title: [task title]
  Status: Incomplete
  ```

#### FR-01.5: Error Handling
- Empty title error: "Error: Title cannot be empty. Please try again."
- Return to command prompt after error

---

## Implementation Plan

1. Create `Task` dataclass with fields: id, title, description, completed
2. Create `TodoApp` class with task list and next_id counter
3. Implement `add_task()` method:
   - Collect title with validation
   - Collect optional description
   - Create Task object
   - Add to task list
   - Increment next_id
4. Create CLI handler for add command
5. Test with various inputs

---

## Implementation

### Code Changes (src/main.py)

```python
from dataclasses import dataclass

@dataclass
class Task:
    """Represents a single todo task."""
    id: int
    title: str
    description: str
    completed: bool

class TodoApp:
    def __init__(self) -> None:
        self.tasks: list[Task] = []
        self.next_id: int = 1

    def add_task(self, title: str, description: str = "") -> Task:
        """Add a new task to the todo list."""
        task = Task(
            id=self.next_id,
            title=title.strip(),
            description=description.strip(),
            completed=False
        )
        self.tasks.append(task)
        self.next_id += 1
        return task

def handle_add(app: TodoApp) -> None:
    """Handle the add task command."""
    print("\n--- Add New Task ---")

    while True:
        title = input("Title: ").strip()
        if title:
            break
        print("Error: Title cannot be empty. Please try again.")

    description = input("Description (press Enter to skip): ").strip()

    task = app.add_task(title, description)

    print(f"\nTask added successfully!")
    print(f"ID: {task.id}")
    print(f"Title: {task.title}")
    print(f"Status: {'Incomplete' if not task.completed else 'Complete'}")
```

---

## Testing

### Test Case 1: Add Task with Title Only
**Input:**
```
> add
Title: Buy groceries
Description (press Enter to skip): [Enter]
```
**Expected Output:**
```
Task added successfully!
ID: 1
Title: Buy groceries
Status: Incomplete
```

### Test Case 2: Add Task with Title and Description
**Input:**
```
> add
Title: Complete Python project
Description (press Enter to skip): Finish todo-cli app for hackathon
```
**Expected Output:**
```
Task added successfully!
ID: 2
Title: Complete Python project
Status: Incomplete
```

### Test Case 3: Empty Title Validation
**Input:**
```
> add
Title: [Enter]
Error: Title cannot be empty. Please try again.
Title: Valid task
Description (press Enter to skip): [Enter]
```
**Expected Output:**
```
Task added successfully!
ID: 3
Title: Valid task
Status: Incomplete
```

### Test Case 4: Multiple Tasks
**Input:**
```
> add
Title: Task 1
Description: [Enter]

> add
Title: Task 2
Description: [Enter]

> list
```
**Expected Output:**
```
1. [ ] Task 1
2. [ ] Task 2
```

---

## Notes

- Task IDs are sequential and never reused (even after deletion)
- Title and description are trimmed of leading/trailing whitespace
- Description defaults to empty string, not None
- Feature serves as foundation for all other task operations

---

**PHR Version:** 1.0
**Last Updated:** 2026-01-02
