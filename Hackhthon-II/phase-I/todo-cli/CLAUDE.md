# Claude Code Instructions for Todo-CLI

## Project Overview

This is a **spec-driven development project** using Spec-Kit Plus methodology with an **interactive menu-driven UI**. Your primary role is to implement features based on Project History Records (PHRs) located in `specs/history/`.

**Key Architecture Changes (v2.0):**
- Interactive numbered menu system (not command-based)
- ANSI color codes for visual enhancement
- Selection-based task operations (not ID-based)
- Statistics dashboard with progress visualization
- Confirmation dialogs for safety

## Critical Rules

### ⚠️ DO NOT
- ❌ Write code without first reading the corresponding spec in `specs/history/`
- ❌ Implement features not documented in a PHR
- ❌ Add persistent storage (files, databases) - this is in-memory only
- ❌ Add external dependencies - use Python standard library only
- ❌ Modify the constitution without explicit user request
- ❌ Remove ANSI colors or UI enhancements - they're part of v2.0
- ❌ Change back to command-based interface - menu system is now standard

### ✅ DO
- ✅ Always read the relevant PHR file(s) before making code changes
- ✅ Follow the exact specification in the PHR
- ✅ Write clean, readable Python with type hints
- ✅ Use TodoWrite tool to track multi-step tasks
- ✅ Keep the implementation simple and focused
- ✅ Test features manually after implementation
- ✅ Update this file if project workflow changes
- ✅ Maintain consistency with existing UI patterns (Colors, UI functions)
- ✅ Add "Press Enter to continue" prompts after all operations
- ✅ Use existing UI helper functions (print_header, print_success, etc.)

## Development Workflow

### When User Asks to Implement a Feature

1. **Read the PHR**: Check `specs/history/` for the corresponding spec file
   - Example: User asks to "add task feature" → Read `specs/history/01_add_task.md`

2. **Create Todo List**: Use TodoWrite tool to break down the work
   ```
   - Read PHR file
   - Implement Task class (if not exists)
   - Implement add_task method
   - Test the feature
   - Update README if needed
   ```

3. **Implement Code**: Write code in `src/main.py` following the spec exactly

4. **Test**: Run the application and verify the feature works as specified

5. **Report**: Inform user of completion with relevant code locations

### When User Asks for a New Feature

1. **Check Constitution**: Verify the feature is in scope per `constitution.md`
2. **Create PHR**: If in scope, create a new PHR file in `specs/history/` first
3. **Then Implement**: Follow the standard implementation workflow

### When User Asks to Modify Existing Feature

1. **Read Current PHR**: Understand the existing specification
2. **Ask for Clarification**: If changes would deviate from the PHR
3. **Update PHR**: Modify the spec if user confirms the changes
4. **Update Code**: Implement the changes per updated PHR

## Project Structure

```
todo-cli/
├── src/
│   └── main.py              # ALL code goes here (single-file implementation)
├── specs/
│   └── history/             # Project History Records (PHRs)
│       ├── 01_add_task.md
│       ├── 02_view_tasks.md
│       ├── 03_update_task.md
│       ├── 04_delete_task.md
│       └── 05_mark_complete.md
├── constitution.md          # Project governance and rules
├── CLAUDE.md                # This file - your instructions
├── README.md                # User-facing documentation
└── pyproject.toml           # Python project config
```

## Code Implementation Guidelines

### Architecture

**Single File Pattern**: All code in `src/main.py` with these core components:

```python
# 1. Colors Class - ANSI Color Management
class Colors:
    """ANSI color codes for terminal output."""
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_CYAN = "\033[96m"
    # ... more colors

# 2. Task Data Class
@dataclass
class Task:
    id: int
    title: str
    description: str
    completed: bool

# 3. Main Application Class
class TodoApp:
    def __init__(self):
        self.tasks: list[Task] = []
        self.next_id: int = 1

    # Business logic methods: add_task, delete_task, toggle_complete, etc.
    # Helper methods: _get_task_by_id, get_stats

# 4. UI Helper Functions
def clear_screen() -> None:
    """Clear the terminal screen."""

def print_header(text: str) -> None:
    """Print a formatted header."""

def print_success(message: str) -> None:
    """Print a success message in green."""

def print_error(message: str) -> None:
    """Print an error message in red."""

# 5. Display Functions
def display_tasks(app: TodoApp) -> None:
    """Display all tasks with formatting."""

def display_tasks_mini(app: TodoApp) -> None:
    """Display compact list for selection."""

def select_task(app: TodoApp, prompt: str) -> Task | None:
    """Interactive task selection."""

# 6. Handler Functions (One per menu option)
def handle_add(app: TodoApp) -> None:
    """Handle menu option 1."""

def handle_view(app: TodoApp) -> None:
    """Handle menu option 2."""

# ... more handlers

# 7. Main Loop
def main():
    app = TodoApp()
    while True:
        print_main_menu(app)
        choice = get_menu_choice()
        # Execute handler based on choice
```

### Code Style

- **Type Hints**: All functions must have type annotations
- **Docstrings**: Public methods need docstrings
- **PEP 8**: Follow Python style guide (4-space indents, etc.)
- **Clear Names**: Use descriptive variable names (`task_list` not `tl`)
- **Error Messages**: User-friendly, actionable error messages
- **UI Consistency**: Always use Colors class for colored output
- **Screen Management**: Clear screen between major transitions
- **Wait Prompts**: Always add "Press Enter to continue" after operations

### UI/UX Patterns

**Always follow these patterns:**

1. **Menu Handler Pattern**:
```python
def handle_<action>(app: TodoApp) -> None:
    """Handle menu option X."""
    clear_screen()
    print_header("Action Name")

    # Check for empty list if needed
    if not app.tasks:
        print_error("No tasks available!")
        input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.RESET}")
        return

    # Show mini list for selection
    display_tasks_mini(app)

    # Get selection
    task = select_task(app, "Select task")
    if task is None:  # User cancelled
        return

    try:
        # Perform action
        result = app.<action>_task(task.id)

        # Show success
        clear_screen()
        print_header("Success!")
        print_success("Action completed!")
        input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.RESET}")

    except ValueError as e:
        print_error(str(e))
        input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.RESET}")
```

2. **Color Usage**:
- Success messages: `Colors.BRIGHT_GREEN` with ✓ icon
- Error messages: `Colors.BRIGHT_RED` with ✗ icon
- Warnings: `Colors.BRIGHT_YELLOW` with ⚠ icon
- Info: `Colors.BRIGHT_CYAN` with ℹ icon
- Headers: `Colors.BRIGHT_BLUE`
- Task titles: `Colors.CYAN`
- User input prompts: `Colors.YELLOW`

## Understanding PHR Files

Each PHR (Project History Record) follows this structure:

```markdown
# PHR-XX: [Feature Name]

**Date:** YYYY-MM-DD
**Status:** Proposed | Approved | Implemented
**Feature ID:** FR-XX

## Specification
[Detailed requirements]

## Implementation Plan
[Step-by-step approach]

## Implementation
[Code changes documented after implementation]

## Testing
[Verification steps]
```

## Running the Application

```bash
# From project root
python src/main.py

# Or using python module
python -m src.main
```

The application will launch with an interactive menu. No command-line arguments needed.

## Common Menu Interactions for Testing

```bash
# Main menu appears with options 1-6
# Select option by entering number

# Test add (Menu option 1)
Select option (0-6): 1
Title: Buy groceries
Description (press Enter to skip): Get milk, eggs, and bread
[Press Enter to continue]

# Test view (Menu option 2)
Select option (0-6): 2
[All tasks displayed with colors]
[Press Enter to continue]

# Test update (Menu option 3)
Select option (0-6): 3
[Compact task list shown]
Select task to update (0 to cancel): 1
New title (press Enter to keep): Buy groceries and cook dinner
New description (press Enter to keep): [Enter]
[Press Enter to continue]

# Test toggle complete (Menu option 5)
Select option (0-6): 5
[Compact task list shown]
Select task to toggle (0 to cancel): 1
[Task marked complete with celebration]
[Press Enter to continue]

# Test delete (Menu option 4)
Select option (0-6): 4
[Compact task list shown]
Select task to delete (0 to cancel): 1
Delete 'Buy groceries'? (y/n): y
[Task deleted]
[Press Enter to continue]

# Test statistics (Menu option 6)
Select option (0-6): 6
[Statistics dashboard with progress bar]
[Press Enter to continue]

# Exit (Menu option 0)
Select option (0-6): 0
[Goodbye message]
```

## Handling Errors

When you encounter errors:

1. **Read the error message carefully**
2. **Check the PHR** - does the implementation match the spec?
3. **Keep it simple** - don't over-engineer the solution
4. **Ask the user** if you're unsure about the approach

## Feature Requirements Summary

| Feature | Menu Option | Input | Output |
|---------|-------------|-------|--------|
| Interactive Menu | Auto-display | Number (1-6, 0 to exit) | Action execution |
| Add Task | `1` | Title (required), Description (optional) | Success screen with task details |
| View Tasks | `2` | None | All tasks with colored status icons |
| Update Task | `3` | Select from list, new title/description | Success screen with updated details |
| Delete Task | `4` | Select from list, confirm (y/n) | Deletion confirmation |
| Toggle Complete | `5` | Select from list | Status toggle with celebration if complete |
| Statistics | `6` | None | Dashboard with progress bar |

## Getting Help

If you're unsure:
1. Check `constitution.md` for project rules
2. Check the relevant PHR in `specs/history/`
3. Ask the user for clarification
4. Keep the solution simple and aligned with specs

---

**Remember**: Spec-driven development means the PHR is the source of truth. Read it first, implement exactly what it says, and keep the code simple.

**Project Constraints**:
- Python 3.12+
- Standard library only (no pip packages)
- In-memory storage (no files/databases)
- Single file implementation (`src/main.py`)
- Interactive menu-driven UI (not command-based)
- ANSI color codes for visual enhancement
- All operations must wait for "Press Enter to continue"

**UI Guidelines (v2.0)**:
- Always clear screen before showing new content
- Use colored output for visual hierarchy
- Show confirmation dialogs for destructive actions
- Display numbered lists for selection (0 to cancel)
- Add celebration messages for positive actions
- Use progress bars for statistics
- Handle all errors gracefully with clear messages
