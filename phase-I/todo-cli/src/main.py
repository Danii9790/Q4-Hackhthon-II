#!/usr/bin/env python3
"""Todo CLI - An interactive command-line todo application.

Built with spec-driven development using Claude Code and Spec-Kit Plus.
"""

import os
from dataclasses import dataclass


# ANSI Color Codes
class Colors:
    """ANSI color codes for terminal output."""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # Colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # Bright colors
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    # Backgrounds
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"

    # Disable colors if not a terminal
    if not os.getenv("TERM") or not os.isatty(1):
        RESET = BOLD = DIM = ""
        BLACK = RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = ""
        BRIGHT_RED = BRIGHT_GREEN = BRIGHT_YELLOW = BRIGHT_BLUE = ""
        BRIGHT_MAGENTA = BRIGHT_CYAN = BRIGHT_WHITE = ""
        BG_RED = BG_GREEN = BG_YELLOW = BG_BLUE = ""


@dataclass
class Task:
    """Represents a single todo task."""

    id: int
    title: str
    description: str
    completed: bool


class TodoApp:
    """Main application class for managing todo tasks."""

    def __init__(self) -> None:
        """Initialize the todo application with an empty task list."""
        self.tasks: list[Task] = []
        self.next_id: int = 1

    def add_task(self, title: str, description: str = "") -> Task:
        """Add a new task to the todo list."""
        task = Task(
            id=self.next_id,
            title=title.strip(),
            description=description.strip(),
            completed=False,
        )
        self.tasks.append(task)
        self.next_id += 1
        return task

    def _get_task_by_id(self, task_id: int) -> Task | None:
        """Find a task by its ID."""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def update_task(
        self,
        task_id: int,
        new_title: str | None = None,
        new_description: str | None = None,
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

    def delete_task(self, task_id: int) -> Task:
        """Delete a task by ID."""
        for i, task in enumerate(self.tasks):
            if task.id == task_id:
                deleted_task = self.tasks.pop(i)
                return deleted_task
        raise ValueError(f"Task with ID {task_id} not found")

    def toggle_complete(self, task_id: int) -> Task:
        """Toggle a task's completion status."""
        task = self._get_task_by_id(task_id)

        if task is None:
            raise ValueError(f"Task with ID {task_id} not found")

        task.completed = not task.completed
        return task

    def get_stats(self) -> dict[str, int]:
        """Get task statistics."""
        return {
            "total": len(self.tasks),
            "completed": sum(1 for t in self.tasks if t.completed),
            "incomplete": sum(1 for t in self.tasks if not t.completed),
        }


# UI Functions
def clear_screen() -> None:
    """Clear the terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")


def print_header(text: str, width: int = 60) -> None:
    """Print a formatted header."""
    padding = (width - len(text) - 2) // 2
    print(f"\n{Colors.BRIGHT_BLUE}{'=' * width}{Colors.RESET}")
    print(
        f"{Colors.BRIGHT_BLUE}{' ' * padding}{Colors.BOLD}{text}{Colors.RESET}{Colors.BRIGHT_BLUE}{' ' * padding}{Colors.RESET}"
    )
    print(f"{Colors.BRIGHT_BLUE}{'=' * width}{Colors.RESET}\n")


def print_success(message: str) -> None:
    """Print a success message."""
    print(f"{Colors.BRIGHT_GREEN}✓ {message}{Colors.RESET}")


def print_error(message: str) -> None:
    """Print an error message."""
    print(f"{Colors.BRIGHT_RED}✗ {message}{Colors.RESET}")


def print_warning(message: str) -> None:
    """Print a warning message."""
    print(f"{Colors.BRIGHT_YELLOW}⚠ {message}{Colors.RESET}")


def print_info(message: str) -> None:
    """Print an info message."""
    print(f"{Colors.BRIGHT_CYAN}ℹ {message}{Colors.RESET}")


def print_task(task: Task, index: int = 0) -> None:
    """Print a single task with formatting."""
    status_icon = f"{Colors.BRIGHT_GREEN}✓{Colors.RESET}" if task.completed else f"{Colors.DIM}○{Colors.RESET}"
    status_color = Colors.BRIGHT_GREEN if task.completed else Colors.BRIGHT_YELLOW

    print(f"\n  {Colors.BOLD}{index}. {status_icon}{Colors.RESET} {Colors.CYAN}{task.title}{Colors.RESET}")

    if task.description:
        print(f"     {Colors.DIM}Description: {task.description}{Colors.RESET}")

    print(f"     {status_color}Status: {'Complete' if task.completed else 'Incomplete'}{Colors.RESET}")
    print(f"     {Colors.DIM}ID: {task.id}{Colors.RESET}")


def display_tasks(app: TodoApp) -> None:
    """Display all tasks in a formatted list."""
    clear_screen()
    print_header("Your Tasks")

    if not app.tasks:
        print(f"\n{Colors.DIM}No tasks yet. Create your first task!{Colors.RESET}")
        input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.RESET}")
        return

    stats = app.get_stats()
    print(
        f"{Colors.BRIGHT_BLUE}Total: {stats['total']} | "
        f"{Colors.BRIGHT_GREEN}Completed: {stats['completed']} | "
        f"{Colors.BRIGHT_YELLOW}Pending: {stats['incomplete']}{Colors.RESET}\n"
    )

    for index, task in enumerate(app.tasks, 1):
        print_task(task, index)

    print()
    input(f"{Colors.CYAN}Press Enter to continue...{Colors.RESET}")


def confirm_action(message: str) -> bool:
    """Ask for user confirmation."""
    while True:
        response = input(f"\n{Colors.YELLOW}{message} (y/n): {Colors.RESET}").strip().lower()
        if response in ("y", "yes"):
            return True
        if response in ("n", "no"):
            return False
        print_warning("Please enter 'y' or 'n'")


def select_task(app: TodoApp, prompt: str = "Select task number") -> Task | None:
    """Interactive task selection."""
    while True:
        try:
            response = input(f"\n{Colors.CYAN}{prompt} (0 to cancel): {Colors.RESET}").strip()
            if not response:
                continue

            choice = int(response)

            if choice == 0:
                return None

            if 1 <= choice <= len(app.tasks):
                return app.tasks[choice - 1]

            print_error(f"Please enter a number between 0 and {len(app.tasks)}")

        except ValueError:
            print_error("Please enter a valid number")
        except KeyboardInterrupt:
            return None


# Menu Handlers
def handle_add(app: TodoApp) -> None:
    """Handle adding a new task."""
    clear_screen()
    print_header("Add New Task")

    print(f"{Colors.CYAN}Enter task details:{Colors.RESET}\n")

    while True:
        title = input(f"{Colors.YELLOW}Title: {Colors.RESET}").strip()
        if title:
            break
        print_error("Title cannot be empty. Please try again.")

    description = input(f"{Colors.YELLOW}Description (press Enter to skip): {Colors.RESET}").strip()

    task = app.add_task(title, description)

    clear_screen()
    print_header("Task Added!")
    print_task(task, 1)
    print_success("Task created successfully!")
    input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.RESET}")


def handle_view(app: TodoApp) -> None:
    """Handle viewing all tasks."""
    display_tasks(app)


def handle_update(app: TodoApp) -> None:
    """Handle updating a task."""
    if not app.tasks:
        clear_screen()
        print_header("Update Task")
        print_error("No tasks available. Add a task first!")
        input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.RESET}")
        return

    clear_screen()
    print_header("Update Task")

    display_tasks_mini(app)

    task = select_task(app, "Select task to update")
    if task is None:
        return

    print(f"\n{Colors.CYAN}Current title: {Colors.WHITE}{task.title}{Colors.RESET}")
    new_title = input(f"{Colors.YELLOW}New title (press Enter to keep): {Colors.RESET}").strip()
    if not new_title:
        new_title = task.title

    print(f"\n{Colors.CYAN}Current description: {Colors.WHITE}{task.description or 'None'}{Colors.RESET}")
    new_description = input(
        f"{Colors.YELLOW}New description (press Enter to keep): {Colors.RESET}"
    ).strip()
    if not new_description:
        new_description = task.description

    try:
        updated_task = app.update_task(task.id, new_title, new_description)

        clear_screen()
        print_header("Task Updated!")
        print_task(updated_task, 1)
        print_success("Task updated successfully!")
        input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.RESET}")

    except ValueError as e:
        print_error(str(e))
        input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.RESET}")


def display_tasks_mini(app: TodoApp) -> None:
    """Display a compact list of tasks for selection."""
    print(f"\n{Colors.BOLD}Your Tasks:{Colors.RESET}\n")
    for index, task in enumerate(app.tasks, 1):
        status = f"{Colors.BRIGHT_GREEN}✓{Colors.RESET}" if task.completed else f"{Colors.DIM}○{Colors.RESET}"
        print(f"  {index}. {status} {Colors.CYAN}{task.title}{Colors.RESET}")
    print()


def handle_delete(app: TodoApp) -> None:
    """Handle deleting a task."""
    if not app.tasks:
        clear_screen()
        print_header("Delete Task")
        print_error("No tasks available. Add a task first!")
        input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.RESET}")
        return

    clear_screen()
    print_header("Delete Task")

    display_tasks_mini(app)

    task = select_task(app, "Select task to delete")
    if task is None:
        return

    if not confirm_action(f"Delete '{task.title}'?"):
        print_info("Deletion cancelled")
        input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.RESET}")
        return

    try:
        deleted_task = app.delete_task(task.id)

        clear_screen()
        print_header("Task Deleted!")
        print(f"\n{Colors.BRIGHT_RED}Deleted:{Colors.RESET}")
        print(f"  {Colors.CYAN}{deleted_task.title}{Colors.RESET}")
        print_success("Task deleted successfully!")
        input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.RESET}")

    except ValueError as e:
        print_error(str(e))
        input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.RESET}")


def handle_complete(app: TodoApp) -> None:
    """Handle toggling task completion."""
    if not app.tasks:
        clear_screen()
        print_header("Toggle Complete")
        print_error("No tasks available. Add a task first!")
        input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.RESET}")
        return

    clear_screen()
    print_header("Toggle Task Complete")

    display_tasks_mini(app)

    task = select_task(app, "Select task to toggle")
    if task is None:
        return

    try:
        updated_task = app.toggle_complete(task.id)

        clear_screen()
        if updated_task.completed:
            print_header("Task Completed! 🎉")
            print_success("Great job! Task marked as complete!")
        else:
            print_header("Task Incomplete")
            print_info("Task marked as incomplete")

        print_task(updated_task, 1)
        input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.RESET}")

    except ValueError as e:
        print_error(str(e))
        input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.RESET}")


def handle_stats(app: TodoApp) -> None:
    """Display task statistics."""
    clear_screen()
    print_header("Task Statistics")

    stats = app.get_stats()

    print(f"\n{Colors.BOLD}Overview:{Colors.RESET}\n")

    print(f"  {Colors.CYAN}Total Tasks:{Colors.RESET}       {Colors.BOLD}{stats['total']}{Colors.RESET}")

    print(
        f"  {Colors.BRIGHT_GREEN}Completed:{Colors.RESET}         {Colors.BOLD}{stats['completed']}{Colors.RESET}"
    )

    print(
        f"  {Colors.BRIGHT_YELLOW}Pending:{Colors.RESET}           {Colors.BOLD}{stats['incomplete']}{Colors.RESET}"
    )

    if stats['total'] > 0:
        completion_rate = (stats['completed'] / stats['total']) * 100
        print(f"\n  {Colors.CYAN}Completion Rate:{Colors.RESET}   {Colors.BOLD}{completion_rate:.1f}%{Colors.RESET}")

        # Progress bar
        bar_width = 30
        filled = int((stats['completed'] / stats['total']) * bar_width)
        bar = f"{Colors.BRIGHT_GREEN}{'█' * filled}{Colors.RESET}{Colors.DIM}{'░' * (bar_width - filled)}{Colors.RESET}"
        print(f"\n  {bar} {completion_rate:.0f}%")

    input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.RESET}")


def print_main_menu(app: TodoApp) -> None:
    """Print the main menu."""
    clear_screen()
    stats = app.get_stats()

    # Header with app name
    print(f"\n{Colors.BRIGHT_BLUE}╔═══════════════════════════════════════════════════════╗{Colors.RESET}")
    print(f"{Colors.BRIGHT_BLUE}║{Colors.RESET}          {Colors.BOLD}{Colors.BRIGHT_WHITE}TODO CLI - Task Manager{Colors.RESET}              {Colors.BRIGHT_BLUE}║{Colors.RESET}")
    print(f"{Colors.BRIGHT_BLUE}╚═══════════════════════════════════════════════════════╝{Colors.RESET}")

    # Stats bar
    print(f"\n  {Colors.DIM}Tasks: {stats['total']} | "
          f"{Colors.BRIGHT_GREEN}Done: {stats['completed']}{Colors.DIM} | "
          f"{Colors.BRIGHT_YELLOW}Todo: {stats['incomplete']}{Colors.RESET}")

    # Menu options
    print(f"\n{Colors.BOLD}  Main Menu:{Colors.RESET}\n")
    print(f"  {Colors.GREEN}1.{Colors.RESET} {Colors.CYAN}Add Task{Colors.RESET}")
    print(f"  {Colors.GREEN}2.{Colors.RESET} {Colors.CYAN}View All Tasks{Colors.RESET}")
    print(f"  {Colors.GREEN}3.{Colors.RESET} {Colors.CYAN}Update Task{Colors.RESET}")
    print(f"  {Colors.GREEN}4.{Colors.RESET} {Colors.CYAN}Delete Task{Colors.RESET}")
    print(f"  {Colors.GREEN}5.{Colors.RESET} {Colors.CYAN}Toggle Complete{Colors.RESET}")
    print(f"  {Colors.GREEN}6.{Colors.RESET} {Colors.CYAN}View Statistics{Colors.RESET}")
    print(f"\n  {Colors.RED}0.{Colors.RESET} {Colors.RED}Exit{Colors.RESET}")

    print(f"\n{Colors.DIM}{'─' * 53}{Colors.RESET}\n")


def get_menu_choice(max_choice: int = 6) -> int:
    """Get and validate menu choice."""
    while True:
        try:
            choice = input(f"{Colors.BRIGHT_CYAN}Select option (0-{max_choice}): {Colors.RESET}").strip()
            if not choice:
                continue

            choice_num = int(choice)
            if 0 <= choice_num <= max_choice:
                return choice_num

            print_error(f"Please enter a number between 0 and {max_choice}")

        except ValueError:
            print_error("Please enter a valid number")


def main() -> None:
    """Main application loop with interactive menu."""
    app = TodoApp()

    while True:
        try:
            print_main_menu(app)
            choice = get_menu_choice()

            if choice == 0:
                clear_screen()
                print_header("Goodbye! 👋")
                print(f"\n{Colors.BRIGHT_GREEN}Thanks for using Todo CLI!{Colors.RESET}")
                print(f"{Colors.DIM}Have a productive day!{Colors.RESET}\n")
                break
            elif choice == 1:
                handle_add(app)
            elif choice == 2:
                handle_view(app)
            elif choice == 3:
                handle_update(app)
            elif choice == 4:
                handle_delete(app)
            elif choice == 5:
                handle_complete(app)
            elif choice == 6:
                handle_stats(app)

        except KeyboardInterrupt:
            clear_screen()
            print_header("Goodbye! 👋")
            print(f"\n{Colors.BRIGHT_GREEN}Thanks for using Todo CLI!{Colors.RESET}")
            print(f"{Colors.DIM}Have a productive day!{Colors.RESET}\n")
            break
        except Exception as e:
            print_error(f"Unexpected error: {e}")
            input(f"\n{Colors.CYAN}Press Enter to continue...{Colors.RESET}")


if __name__ == "__main__":
    main()
