# Todo CLI

An **interactive** command-line todo application built with spec-driven development using Claude Code and Spec-Kit Plus methodology.

## ✨ Features

- 🎨 **Beautiful Interactive UI** - Modern menu-driven interface with colors
- ✅ **Add Tasks** - Create tasks with titles and optional descriptions
- 👀 **View Tasks** - List all tasks with colored status indicators
- ✏️ **Update Tasks** - Modify task titles and descriptions
- 🗑️ **Delete Tasks** - Remove tasks with confirmation dialogs
- ✅ **Mark Complete** - Toggle task completion with celebration feedback
- 📊 **Statistics Dashboard** - Visual progress tracking with progress bars

## Requirements

- Python 3.12 or higher
- No external dependencies (uses standard library only)
- Terminal with ANSI color support (most modern terminals)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd todo-cli
```

2. Verify Python version:
```bash
python --version
# Should show Python 3.12+
```

3. Run the application:
```bash
python src/main.py
```

## Usage

### Interactive Menu System

The application launches with a beautiful interactive menu:

```
╔═══════════════════════════════════════════════════════╗
║          TODO CLI - Task Manager                      ║
╚═══════════════════════════════════════════════════════╝

  Tasks: 0 | Done: 0 | Todo: 0

  Main Menu:

  1. Add Task
  2. View All Tasks
  3. Update Task
  4. Delete Task
  5. Toggle Complete
  6. View Statistics

  0. Exit

─────────────────────────────────────────────────────

Select option (0-6):
```

Simply type the number of your choice and press Enter!

### Examples

#### 1. Add a Task
```
Select option (0-6): 1

============================================================
                     Add New Task
============================================================

Enter task details:

Title: Buy groceries
Description (press Enter to skip): Get milk, eggs, and bread

[Task added successfully with green checkmark]
Press Enter to continue...
```

#### 2. View All Tasks
```
Select option (0-6): 2

============================================================
                      Your Tasks
============================================================

Total: 2 | Completed: 1 | Pending: 1

  1. ○ Buy groceries
     Description: Get milk, eggs, and bread
     Status: Incomplete
     ID: 1

  2. ✓ Complete Python project
     Description: Finish todo-cli app for hackathon
     Status: Complete
     ID: 2

Press Enter to continue...
```

#### 3. Update a Task
```
Select option (0-6): 3

============================================================
                     Update Task
============================================================

Your Tasks:

  1. ○ Buy groceries
  2. ✓ Complete Python project

Select task to update (0 to cancel): 1

Current title: Buy groceries
New title (press Enter to keep): Buy groceries and cook dinner

Current description: Get milk, eggs, and bread
New description (press Enter to keep): Weekly shopping

[Task updated successfully]
Press Enter to continue...
```

#### 4. Mark Task as Complete
```
Select option (0-6): 5

Your Tasks:

  1. ○ Buy groceries and cook dinner
  2. ✓ Complete Python project

Select task to toggle (0 to cancel): 1

============================================================
                   Task Completed! 🎉
============================================================

✓ Great job! Task marked as complete!

  1. ✓ Buy groceries and cook dinner
     Status: Complete

Press Enter to continue...
```

#### 5. View Statistics
```
Select option (0-6): 6

============================================================
                   Task Statistics
============================================================

Overview:

  Total Tasks:       5
  Completed:         3
  Pending:           2

  Completion Rate:   60.0%

  ████████████████░░░░░░░░░░░░░░░░ 60%

Press Enter to continue...
```

#### 6. Delete a Task
```
Select option (0-6): 4

Your Tasks:

  1. ✓ Buy groceries
  2. ✓ Complete Python project
  3. ○ Old task

Select task to delete (0 to cancel): 3

Delete 'Old task'? (y/n): y

============================================================
                     Task Deleted!
============================================================

Deleted:
  Old task

✓ Task deleted successfully!
Press Enter to continue...
```

## Project Structure

```
todo-cli/
├── src/
│   └── main.py              # Main application entry point
├── specs/
│   └── history/             # Project History Records (PHRs)
│       ├── 01_add_task.md
│       ├── 02_view_tasks.md
│       ├── 03_update_task.md
│       ├── 04_delete_task.md
│       └── 05_mark_complete.md
├── constitution.md          # Project governance and rules
├── CLAUDE.md                # Instructions for Claude Code
├── README.md                # This file
└── pyproject.toml           # Python project configuration
```

## Development

### Spec-Driven Development

This project follows the Spec-Kit Plus methodology:

1. **No code without a spec** - Every feature has a corresponding PHR in `specs/history/`
2. **One feature = one spec** - Each PHR documents one complete feature
3. **Implementation follows spec** - Code matches the approved specification exactly

### Project Constitution

See `constitution.md` for:
- Development principles
- Feature requirements
- Code quality standards
- Success criteria

### Claude Code Integration

See `CLAUDE.md` for:
- Development workflow
- Code implementation guidelines
- PHR file structure
- Testing instructions

## Architecture

### Task Model

```python
@dataclass
class Task:
    id: int
    title: str
    description: str
    completed: bool
```

### Core Classes

- **`Task`**: Dataclass representing a single todo item
- **`TodoApp`**: Main application class with task management methods
- **`Colors`**: ANSI color code management for terminal colors
- **`UI Functions`**: Helper functions for formatted output
- **`Handler Functions`**: One per menu option (handle_add, handle_view, etc.)
- **`Main Loop`**: Interactive menu system with choice handling

### Key Design Decisions

- **Interactive Menu**: Numbered options instead of command typing
- **ANSI Colors**: Visual enhancement without external dependencies
- **In-Memory Storage**: Tasks are stored in RAM (no database or files)
- **Sequential IDs**: Task IDs start at 1 and increment (never reused)
- **Selection-Based**: Pick tasks from numbered lists instead of typing IDs
- **Single File**: All code in `src/main.py` for simplicity
- **No Dependencies**: Uses only Python standard library
- **Type Hints**: Full type annotations for better code clarity

## Testing

### Manual Testing Checklist

- [ ] Add task with title only
- [ ] Add task with title and description
- [ ] View empty task list
- [ ] View single task
- [ ] View multiple tasks with colored status
- [ ] Update task title
- [ ] Update task description
- [ ] Delete task with confirmation
- [ ] Cancel deletion with 'n'
- [ ] Mark task as complete (see celebration)
- [ ] Toggle task back to incomplete
- [ ] View statistics dashboard
- [ ] Test all color outputs
- [ ] Test navigation (0 to cancel)
- [ ] Test invalid menu choices
- [ ] Test empty title validation

### Test Session Example

```bash
$ python src/main.py

╔═══════════════════════════════════════════════════════╗
║          TODO CLI - Task Manager                      ║
╚═══════════════════════════════════════════════════════╝

  Tasks: 0 | Done: 0 | Todo: 0

  Main Menu:

  1. Add Task
  2. View All Tasks
  3. Update Task
  4. Delete Task
  5. Toggle Complete
  6. View Statistics

  0. Exit

Select option (0-6): 1
[Add task - Enter title and description]
Press Enter to continue...

Select option (0-6): 2
[View task with colored output]
Press Enter to continue...

Select option (0-6): 5
[Toggle task complete with celebration]
Press Enter to continue...

Select option (0-6): 6
[View statistics dashboard]
Press Enter to continue...

Select option (0-6): 0

============================================================
                        Goodbye! 👋
============================================================

Thanks for using Todo CLI!
Have a productive day!
```

## Limitations

- **No persistent storage** - Tasks are lost when application exits
- **No undo functionality** - Deleted tasks cannot be recovered
- **No task categories** - All tasks are in a single list
- **No due dates** - Tasks have no time-based attributes
- **No search** - Must manually find tasks in the list

These limitations are intentional per the project constitution.

## Future Enhancements (Out of Scope)

The following features are NOT in scope for this project:

- Persistent storage (files, database)
- Task categories or tags
- Due dates and reminders
- Task search and filtering
- Multi-user support
- Web interface
- External dependencies

## Contributing

This is a hackathon project demonstrating spec-driven development with an interactive UI. For modifications:

1. Read `constitution.md` to understand project rules
2. Check `specs/history/` for existing feature specifications
3. Follow the Spec-Kit Plus workflow
4. Maintain consistency with the interactive menu system
5. Keep changes simple and aligned with project scope
6. Use existing UI helper functions and color patterns

## License

MIT License - See LICENSE file for details

## Hackathon Deliverables

✅ GitHub repository with:
  - Constitution file (`constitution.md`) with v2.0 specs
  - Specs history folder (`specs/history/`)
  - `/src` folder with Python source code
  - README.md with setup instructions
  - CLAUDE.md with Claude Code instructions

✅ Working console application demonstrating:
  - Interactive menu-driven interface with 6 options
  - Adding tasks with title and description
  - Listing all tasks with colored status indicators
  - Updating task details via selection
  - Deleting tasks with confirmation dialogs
  - Marking tasks as complete/incomplete with celebration
  - Statistics dashboard with progress visualization
  - ANSI color codes for visual hierarchy

---

**Built with:** Python 3.12+, Claude Code, Spec-Kit Plus
**Development Philosophy:** Spec-first, clean code, interactive UI
**Version:** 2.0 - Enhanced with Interactive Menu System
