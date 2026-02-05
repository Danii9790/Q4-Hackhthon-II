"""
Unit tests for add_task validation logic.

Tests the input validation methods of AddTaskTool without database interaction.
"""

import pytest
from src.mcp_tools.add_task import AddTaskTool, TaskValidationError


class TestAddTaskValidation:
    """Test suite for AddTaskTool validation methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = AddTaskTool()

    # ============================================================================
    # Title Validation Tests
    # ============================================================================

    def test_validate_title_valid(self):
        """Test that a valid title passes validation."""
        valid_title = "Buy groceries"
        result = self.tool.validate_title(valid_title)
        assert result == valid_title

    def test_validate_title_with_whitespace(self):
        """Test that leading/trailing whitespace is stripped."""
        title_with_spaces = "  Call dentist  "
        result = self.tool.validate_title(title_with_spaces)
        assert result == "Call dentist"

    def test_validate_title_none_raises_error(self):
        """Test that None title raises TaskValidationError."""
        with pytest.raises(TaskValidationError) as exc_info:
            self.tool.validate_title(None)
        assert "required and cannot be empty" in str(exc_info.value)

    def test_validate_title_empty_string_raises_error(self):
        """Test that empty string raises TaskValidationError."""
        with pytest.raises(TaskValidationError) as exc_info:
            self.tool.validate_title("")
        assert "required and cannot be empty" in str(exc_info.value)

    def test_validate_title_only_whitespace_raises_error(self):
        """Test that whitespace-only title raises TaskValidationError."""
        with pytest.raises(TaskValidationError) as exc_info:
            self.tool.validate_title("   ")
        assert "empty or only whitespace" in str(exc_info.value)

    def test_validate_title_exceeds_max_length_raises_error(self):
        """Test that title exceeding 500 characters raises TaskValidationError."""
        long_title = "a" * 501
        with pytest.raises(TaskValidationError) as exc_info:
            self.tool.validate_title(long_title)
        assert "cannot exceed 500 characters" in str(exc_info.value)
        assert "got 501 characters" in str(exc_info.value)

    def test_validate_title_exactly_max_length_succeeds(self):
        """Test that title exactly 500 characters passes validation."""
        max_title = "a" * 500
        result = self.tool.validate_title(max_title)
        assert len(result) == 500

    def test_validate_title_non_string_raises_error(self):
        """Test that non-string title raises TaskValidationError."""
        with pytest.raises(TaskValidationError) as exc_info:
            self.tool.validate_title(123)
        assert "must be a string" in str(exc_info.value)

    # ============================================================================
    # Description Validation Tests
    # ============================================================================

    def test_validate_description_valid(self):
        """Test that a valid description passes validation."""
        valid_desc = "Milk, eggs, and bread"
        result = self.tool.validate_description(valid_desc)
        assert result == valid_desc

    def test_validate_description_none_returns_none(self):
        """Test that None description returns None (optional field)."""
        result = self.tool.validate_description(None)
        assert result is None

    def test_validate_description_empty_string_returns_none(self):
        """Test that empty string description returns None."""
        result = self.tool.validate_description("")
        assert result is None

    def test_validate_description_whitespace_returns_none(self):
        """Test that whitespace-only description returns None."""
        result = self.tool.validate_description("   ")
        assert result is None

    def test_validate_description_with_whitespace_strips(self):
        """Test that leading/trailing whitespace is stripped from description."""
        desc_with_spaces = "  Detailed notes  "
        result = self.tool.validate_description(desc_with_spaces)
        assert result == "Detailed notes"

    def test_validate_description_exceeds_max_length_raises_error(self):
        """Test that description exceeding 5000 characters raises TaskValidationError."""
        long_desc = "a" * 5001
        with pytest.raises(TaskValidationError) as exc_info:
            self.tool.validate_description(long_desc)
        assert "cannot exceed 5000 characters" in str(exc_info.value)
        assert "got 5001 characters" in str(exc_info.value)

    def test_validate_description_exactly_max_length_succeeds(self):
        """Test that description exactly 5000 characters passes validation."""
        max_desc = "a" * 5000
        result = self.tool.validate_description(max_desc)
        assert len(result) == 5000

    def test_validate_description_non_string_raises_error(self):
        """Test that non-string description raises TaskValidationError."""
        with pytest.raises(TaskValidationError) as exc_info:
            self.tool.validate_description(12345)
        assert "must be a string" in str(exc_info.value)
