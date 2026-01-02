# PHR-06: Interactive UI Enhancements

**Date:** 2026-01-02
**Status:** Implemented
**Feature ID:** FR-06, FR-07
**Author:** Claude Code

---

## Specification

### Overview
Transform the command-based CLI into a modern, interactive menu-driven interface with visual enhancements.

### Requirements

#### FR-06.1: Interactive Menu System
- **Main Menu Display**: Show all options as numbered list (1-6)
- **Real-time Statistics**: Display task counts in menu header
- **Visual Design**: Use box-drawing characters for professional look
- **Clear Screen**: Auto-clear between menu transitions
- **Choice Validation**: Accept only valid numbers (0-6)
- **Auto-return**: Always return to menu after actions

#### FR-06.2: ANSI Color Implementation
- **No External Dependencies**: Use standard library only
- **Color Class**: Centralized color code management
- **Disable Fallback**: Turn off colors when not in terminal
- **Color Scheme**:
  - Green: Success, completed tasks
  - Red: Errors, delete actions
  - Yellow: Warnings, incomplete tasks
  - Blue: Headers
  - Cyan: Info, prompts
  - Magenta: Accents

#### FR-06.3: UI Helper Functions
- `print_header()` - Format headers with borders
- `print_success()` - Green messages with ✓ icon
- `print_error()` - Red messages with ✗ icon
- `print_warning()` - Yellow messages with ⚠ icon
- `print_info()` - Cyan messages with ℹ icon
- `clear_screen()` - Cross-platform screen clearing

#### FR-06.4: Enhanced Task Operations
- **Selection-Based**: Pick from numbered list instead of typing IDs
- **Cancel Option**: Press 0 to cancel any selection
- **Compact Lists**: Show mini task lists for selection
- **Confirmation Dialogs**: y/n prompts for destructive actions
- **Wait Prompts**: "Press Enter to continue" after all operations

#### FR-07.1: Statistics Dashboard
- **Menu Option**: Add as option 6 in main menu
- **Display Metrics**: Total, completed, pending counts
- **Progress Bar**: Visual representation with █ and ░ characters
- **Completion Rate**: Show percentage with one decimal place

#### FR-07.2: Visual Enhancements
- **Status Icons**: Use Unicode (✓, ○) instead of [X] and [ ]
- **Celebration Messages**: Show 🎉 when marking tasks complete
- **Colored Status**: Green for complete, yellow for incomplete
- **Task Formatting**: Indented descriptions and metadata

---

## Implementation Plan

1. Create Colors class with ANSI codes
2. Implement UI helper functions
3. Add display functions (full and mini)
4. Create select_task() for interactive selection
5. Add confirm_action() for y/n prompts
6. Implement handle_stats() for dashboard
7. Refactor all handlers to use new UI patterns
8. Update main loop for menu system
9. Test all color outputs
10. Verify cross-platform compatibility

---

## Implementation

### Code Changes (src/main.py)

#### 1. Colors Class
```python
class Colors:
    """ANSI color codes for terminal output."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_CYAN = "\033[96m"

    # Disable colors if not a terminal
    if not os.getenv("TERM") or not os.isatty(1):
        # Reset all to empty strings
        RESET = BOLD = ""
        BRIGHT_GREEN = BRIGHT_RED = ""
        # ... etc
```

#### 2. UI Helper Functions
```python
def clear_screen() -> None:
    """Clear the terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")

def print_header(text: str, width: int = 60) -> None:
    """Print a formatted header."""
    padding = (width - len(text) - 2) // 2
    print(f"\n{Colors.BRIGHT_BLUE}{'=' * width}{Colors.RESET}")
    print(f"{Colors.BRIGHT_BLUE}{' ' * padding}{Colors.BOLD}{text}...")
```

#### 3. Selection System
```python
def select_task(app: TodoApp, prompt: str = "Select task") -> Task | None:
    """Interactive task selection with cancel option."""
    while True:
        try:
            response = input(f"{Colors.CYAN}{prompt} (0 to cancel): {Colors.RESET}")
            choice = int(response)

            if choice == 0:
                return None
            if 1 <= choice <= len(app.tasks):
                return app.tasks[choice - 1]

            print_error(f"Please enter 0-{len(app.tasks)}")
        except ValueError:
            print_error("Please enter a valid number")
```

#### 4. Statistics Dashboard
```python
def handle_stats(app: TodoApp) -> None:
    """Display task statistics with progress bar."""
    clear_screen()
    print_header("Task Statistics")

    stats = app.get_stats()
    print(f"\n  Total Tasks: {stats['total']}")
    print(f"  Completed: {stats['completed']}")
    print(f"  Pending: {stats['incomplete']}")

    if stats['total'] > 0:
        completion_rate = (stats['completed'] / stats['total']) * 100
        bar_width = 30
        filled = int((stats['completed'] / stats['total']) * bar_width)
        bar = f"{Colors.BRIGHT_GREEN}{'█' * filled}{Colors.RESET}"
        bar += f"{Colors.DIM}{'░' * (bar_width - filled)}{Colors.RESET}"
        print(f"\n  {bar} {completion_rate:.0f}%")

    input("\nPress Enter to continue...")
```

#### 5. Main Menu System
```python
def print_main_menu(app: TodoApp) -> None:
    """Print the main menu."""
    clear_screen()
    stats = app.get_stats()

    # Box-drawing header
    print(f"\n{Colors.BRIGHT_BLUE}╔════════════════════╗{Colors.RESET}")
    print(f"{Colors.BRIGHT_BLUE}║  TODO CLI - Manager  ║{Colors.RESET}")
    print(f"{Colors.BRIGHT_BLUE}╚════════════════════╝{Colors.RESET}")

    # Stats bar
    print(f"\n  Tasks: {stats['total']} | "
          f"{Colors.BRIGHT_GREEN}Done: {stats['completed']}{Colors.RESET} | "
          f"{Colors.BRIGHT_YELLOW}Todo: {stats['incomplete']}{Colors.RESET}")

    # Menu options
    print("\n  Main Menu:\n")
    print("  1. Add Task")
    print("  2. View All Tasks")
    print("  3. Update Task")
    print("  4. Delete Task")
    print("  5. Toggle Complete")
    print("  6. View Statistics")
    print("\n  0. Exit")

def main() -> None:
    """Main application loop with menu system."""
    app = TodoApp()

    while True:
        print_main_menu(app)
        choice = get_menu_choice()

        if choice == 0:
            print("\nGoodbye! 👋\n")
            break
        elif choice == 1:
            handle_add(app)
        elif choice == 2:
            handle_view(app)
        # ... etc
```

---

## Testing

### Test Case 1: Menu Navigation
**Input:**
```
[Launch app]
7
[Error message: Please enter 0-6]
2
[View tasks]
[Press Enter]
0
[Exit]
```
**Expected:** Invalid choice rejected, valid choice executed

### Test Case 2: Task Selection
**Input:**
```
Select option: 3
[Compact list shown]
Select task: 5
[Error: Please enter 0-3]
Select task: 1
[Update task shown]
```
**Expected:** Range validation, correct task selected

### Test Case 3: Cancel Operations
**Input:**
```
Select option: 4
Select task: 0
[Returns to menu]
```
**Expected:** Clean cancellation, no action taken

### Test Case 4: Confirmation Dialog
**Input:**
```
Delete task?
maybe
[Error: Please enter y/n]
y
[Task deleted]
```
**Expected:** Validates y/n input, accepts both short and full

### Test Case 5: Statistics Display
**State:** 5 tasks, 3 complete
**Input:**
```
Select option: 6
```
**Expected Output:**
```
Total: 5
Completed: 3
Pending: 2

Completion Rate: 60.0%

███████████████████░░░░░░░░░░░░░░░░ 60%
```

### Test Case 6: Color Display
**Test in different terminals:**
- [x] Standard terminal (colors enabled)
- [x] Piped to file (colors disabled)
- [x] Redirected output (colors disabled)

### Test Case 7: Cross-Platform
- [x] Linux/macOS screen clearing
- [x] Windows screen clearing (cls command)

---

## Migration Notes

### Breaking Changes from v1.0
- **Command-based to menu-based**: No more typing `add`, `list`, etc.
- **Task IDs to Selection**: No more typing task IDs, select from list
- **Aliases removed**: `a`, `l`, `u`, `d`, `c` shortcuts no longer exist

### User Impact
- **More Intuitive**: Numbered options easier than remembering commands
- **Safer**: Confirmation dialogs prevent accidental deletions
- **Visual Feedback**: Colors and icons provide immediate status
- **Better UX**: Clear screens and formatted output

### Developer Impact
- **New UI Functions**: Use `print_success()`, `print_error()`, etc.
- **Handler Pattern**: One function per menu option
- **Color Usage**: Always use Colors class for consistency
- **Wait Prompts**: Must add `input()` after each operation

---

## Performance Considerations

- **Screen Clearing**: Minimal performance impact
- **Color Processing**: Negligible (simple string concatenation)
- **Menu Redraw**: Fast (only 6-7 lines of text)
- **No External Dependencies**: Zero installation overhead

---

## Accessibility

- **Color Blindness**: Status indicated by icons (✓, ○) not just colors
- **Terminal Compatibility**: Gracefully degrades without color support
- **Clear Labels**: All options have descriptive text
- **Keyboard Navigation**: Simple number input, no complex key combos

---

## Known Limitations

- **Fixed Menu Layout**: Cannot be customized by users
- **No Mouse Support**: Keyboard-only interaction
- **Terminal Required**: Won't work in environments without TTY
- **Color Dependency**: Best experience requires ANSI color support

---

**PHR Version:** 1.0
**Last Updated:** 2026-01-02
**Migration:** From v1.0 (command-based) to v2.0 (menu-based)
