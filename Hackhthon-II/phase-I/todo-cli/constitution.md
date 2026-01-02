# Todo-CLI Project Constitution

## Project Overview

**Project Name:** todo-cli
**Version:** 0.1.0
**Description:** An interactive command-line todo application built with spec-driven development using Claude Code and Spec-Kit Plus
**Development Philosophy:** Spec-first, clean code, in-memory storage, interactive menu-driven UI

## Core Development Principles

### 1. Spec-Driven Development
- **No code without a spec**: Every feature must have a corresponding specification file in `specs/history/`
- **One feature = one PHR**: Each Project History Record (PHR) documents one complete feature
- **PHR Structure**: Each spec file follows the Spec-Kit Plus template format
- **Implementation follows spec**: Code implementation must match the approved specification

### 2. Clean Code Standards
- **Single Responsibility**: Each function/module does one thing well
- **DRY Principle**: Don't Repeat Yourself - extract common logic
- **Clear Naming**: Use descriptive variable and function names
- **Type Hints**: All functions use Python type hints
- **Docstrings**: Public functions have clear docstrings
- **Error Handling**: Graceful error messages for users

### 3. Python Best Practices
- **PEP 8 Compliance**: Follow Python style guidelines
- **Modern Python**: Use Python 3.12+ features appropriately
- **No External Dependencies**: Keep it simple with standard library only
- **In-Memory Storage**: Tasks stored in RAM, no database or file I/O
- **Interactive Menu Interface**: Numbered menu system with clear navigation
- **ANSI Colors**: Visual enhancement using terminal color codes (no external deps)

### 4. Project Structure
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
├── constitution.md          # This file
├── CLAUDE.md                # Instructions for Claude Code
├── README.md                # User documentation
└── pyproject.toml           # Python project configuration
```

## Scope Definition

### In Scope
- Interactive menu-driven interface with numbered options
- Add tasks with title and description
- List all tasks with colored status indicators
- Update task details (title, description)
- Delete tasks with confirmation dialogs
- Mark tasks as complete/incomplete with visual feedback
- Task statistics dashboard with progress bars
- In-memory task storage
- ANSI color codes for visual enhancement
- Clean, maintainable code structure

### Out of Scope
- Persistent storage (files, databases)
- User authentication
- Task categories/tags
- Due dates or reminders
- Multi-user support
- Web interface
- External dependencies (colorama, rich, etc.)

## Feature Requirements

### FR-01: Interactive Menu System
- Main menu with numbered options (1-6)
- Real-time task statistics in header
- Clear screen between menu transitions
- Auto-return to menu after each action
- Visual indicators for all menu items

### FR-02: Add Task
- Menu option: `1`
- Input: Title (required), Description (optional)
- Output: Confirmation screen with formatted task display
- Validation: Title cannot be empty
- Visual: Success message in green with ✓ icon

### FR-03: View Tasks
- Menu option: `2`
- Output: All tasks with colored status indicators
- Format: Numbered list with status icons (✓ or ○)
- Statistics bar showing total, completed, pending
- Visual: Green for complete, yellow for incomplete

### FR-04: Update Task
- Menu option: `3`
- Input: Select from numbered task list (0 to cancel)
- Display current values before editing
- Preserve values on empty input
- Output: Confirmation with updated task display

### FR-05: Delete Task
- Menu option: `4`
- Input: Select from numbered task list (0 to cancel)
- Confirmation dialog: y/n prompt
- Output: Confirmation with deleted task title
- Visual: Red theme for deletion action

### FR-06: Toggle Complete
- Menu option: `5`
- Input: Select from numbered task list (0 to cancel)
- Toggle behavior: Complete ↔ Incomplete
- Visual: Celebration header (🎉) when marking complete
- Output: Status confirmation with task details

### FR-07: Statistics Dashboard
- Menu option: `6`
- Display: Total, completed, pending task counts
- Visual: Progress bar with █ and ░ characters
- Metrics: Completion rate percentage
- Real-time updates based on task state

### UI/UX Requirements
- ANSI color codes for visual hierarchy
- Confirmation dialogs for destructive actions
- Clear error messages with icons (✗, ⚠, ℹ)
- "Press Enter to continue" prompts
- Color scheme: Green (success), Red (error), Yellow (warning), Cyan (info)
- Unicode box-drawing characters for headers

## Code Quality Standards

### Architecture
- **Single File Implementation**: All code in `src/main.py` for simplicity
- **Task Dataclass**: Encapsulate task data with id, title, description, completed
- **TodoApp Class**: Core business logic and state management
- **Colors Class**: ANSI color code management
- **UI Functions**: Separate rendering functions (print_header, print_success, etc.)
- **Handler Functions**: One per menu option for clear separation
- **Main Loop**: Menu display and choice handling

### Error Handling
- Invalid menu choices: Clear error message with valid range
- Invalid task selection: Range validation with helpful message
- Empty input validation: Re-prompt with guidance
- Exception handling: Graceful fallback with "Press Enter to continue"
- Cancel option: Allow users to back out (0 to cancel)

### Testing Approach
- Manual testing through interactive menu navigation
- Test all 6 menu options with various inputs
- Verify color display in different terminals
- Test error conditions (empty lists, invalid selections)
- Ensure all "Press Enter" prompts work correctly
- Verify screen clearing between transitions

## Development Workflow

1. **Write Spec**: Create PHR in `specs/history/` directory
2. **Implement Code**: Write code matching the specification
3. **Test**: Verify feature works as specified
4. **Document**: Update README if user-facing changes
5. **Commit**: Git commit with descriptive message linking to PHR

## Success Criteria

- ✅ All 6 menu options working (Add, View, Update, Delete, Toggle, Stats)
- ✅ Interactive navigation with numbered selections
- ✅ ANSI color codes working across different terminals
- ✅ Clean, readable Python code with type hints
- ✅ Complete PHR documentation in specs/history/
- ✅ Working interactive CLI application
- ✅ Clear user instructions in README.md
- ✅ Claude Code can work with the project structure
- ✅ Hackathon deliverables met with enhanced UI
- ✅ Confirmation dialogs for destructive actions
- ✅ Statistics dashboard with progress visualization

## Maintenance Philosophy

- **Keep It Simple**: Avoid over-engineering
- **YAGNI**: You Aren't Gonna Need It - don't add features for "someday"
- **Refactor Mercilessly**: Improve code clarity when appropriate
- **Document Changes**: Keep specs and README in sync with code

---

**Constitution Version**: 2.0
**Last Updated**: 2026-01-02
**Project Status**: Enhanced with Interactive UI
**Major Changes**: Added interactive menu system, ANSI colors, statistics dashboard
