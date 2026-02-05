"""
Unit tests for task list formatting functionality (T042 & T043).

Tests the format_task_list_for_display function which handles:
- Conversational formatting of task lists
- Empty list detection with context-aware messages
- Different status filters (all, pending, completed)
"""

import pytest
from backend.src.services.agent import format_task_list_for_display


class TestFormatTaskListForDisplay:
    """Test suite for format_task_list_for_display function."""

    def test_empty_all_tasks(self):
        """Test empty task list with 'all' status filter."""
        result = format_task_list_for_display([], "all")

        assert "don't have any tasks" in result.lower()
        assert "create one" in result.lower()
        # Should be encouraging
        assert "would you like" in result.lower()

    def test_empty_pending_tasks(self):
        """Test empty task list with 'pending' status filter."""
        result = format_task_list_for_display([], "pending")

        # Should celebrate that all tasks are complete
        assert "completed all" in result.lower() or "great job" in result.lower()
        # Should be positive and encouraging
        assert len(result) > 20  # Not just a brief "no tasks"

    def test_empty_completed_tasks(self):
        """Test empty task list with 'completed' status filter."""
        result = format_task_list_for_display([], "completed")

        # Should be encouraging for first completion
        assert "haven't completed" in result.lower() or "keep going" in result.lower()
        # Should motivate user
        assert len(result) > 20  # Not just a brief "no tasks"

    def test_empty_unknown_status(self):
        """Test empty task list with unknown status filter."""
        result = format_task_list_for_display([], "unknown")

        # Should have a fallback message
        assert "don't have any tasks" in result.lower()

    def test_single_pending_task_no_description(self):
        """Test formatting single pending task without description."""
        tasks = [
            {
                "id": 1,
                "title": "Buy groceries",
                "description": None,
                "completed": False
            }
        ]
        result = format_task_list_for_display(tasks, "pending")

        # Should contain preamble
        assert "pending" in result.lower()
        # Should show task title
        assert "Buy groceries" in result
        # Should show task ID
        assert "(ID: 1)" in result
        # Should show uncompleted indicator
        assert "○" in result

    def test_single_pending_task_with_description(self):
        """Test formatting single pending task with description."""
        tasks = [
            {
                "id": 2,
                "title": "Call dentist",
                "description": "Tomorrow at 3pm",
                "completed": False
            }
        ]
        result = format_task_list_for_display(tasks, "pending")

        # Should contain task title
        assert "Call dentist" in result
        # Should contain description
        assert "Tomorrow at 3pm" in result
        # Should show task ID
        assert "(ID: 2)" in result

    def test_single_completed_task(self):
        """Test formatting single completed task."""
        tasks = [
            {
                "id": 3,
                "title": "Finish report",
                "description": "Due Friday",
                "completed": True
            }
        ]
        result = format_task_list_for_display(tasks, "completed")

        # Should contain task title
        assert "Finish report" in result
        # Should show completed indicator
        assert "✓" in result
        # Should NOT show uncompleted indicator
        assert "○" not in result

    def test_multiple_tasks_mixed_status(self):
        """Test formatting multiple tasks with mixed status."""
        tasks = [
            {
                "id": 1,
                "title": "Buy groceries",
                "description": None,
                "completed": False
            },
            {
                "id": 2,
                "title": "Call dentist",
                "description": "Tomorrow at 3pm",
                "completed": True
            },
            {
                "id": 3,
                "title": "Finish report",
                "description": None,
                "completed": False
            }
        ]
        result = format_task_list_for_display(tasks, "all")

        # Should contain all task titles
        assert "Buy groceries" in result
        assert "Call dentist" in result
        assert "Finish report" in result
        # Should show all task IDs
        assert "(ID: 1)" in result
        assert "(ID: 2)" in result
        assert "(ID: 3)" in result
        # Should number the tasks
        assert "1." in result
        assert "2." in result
        assert "3." in result

    def test_all_tasks_preamble(self):
        """Test preamble for 'all' status filter."""
        tasks = [
            {"id": 1, "title": "Task 1", "description": None, "completed": False}
        ]
        result = format_task_list_for_display(tasks, "all")

        # Should indicate it's showing all tasks
        assert "all your tasks" in result.lower() or "here are" in result.lower()

    def test_pending_tasks_preamble(self):
        """Test preamble for 'pending' status filter."""
        tasks = [
            {"id": 1, "title": "Task 1", "description": None, "completed": False}
        ]
        result = format_task_list_for_display(tasks, "pending")

        # Should indicate it's showing pending tasks
        assert "pending" in result.lower()

    def test_completed_tasks_preamble(self):
        """Test preamble for 'completed' status filter."""
        tasks = [
            {"id": 1, "title": "Task 1", "description": None, "completed": True}
        ]
        result = format_task_list_for_display(tasks, "completed")

        # Should indicate it's showing completed tasks
        assert "completed" in result.lower()

    def test_long_title_truncation(self):
        """Test handling of long task titles."""
        long_title = "This is a very long task title that might be difficult to display but should still be shown"
        tasks = [
            {
                "id": 1,
                "title": long_title,
                "description": None,
                "completed": False
            }
        ]
        result = format_task_list_for_display(tasks, "pending")

        # Should include the full title
        assert long_title in result

    def test_multiline_description(self):
        """Test handling of multiline descriptions."""
        tasks = [
            {
                "id": 1,
                "title": "Complex task",
                "description": "Line 1\nLine 2\nLine 3",
                "completed": False
            }
        ]
        result = format_task_list_for_display(tasks, "pending")

        # Should include description
        assert "Line 1" in result
        # Should show task on separate line from description
        assert "Complex task" in result
