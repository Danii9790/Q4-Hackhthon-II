"""
Add Task MCP Tool for Todo AI Chatbot.

Provides task creation functionality through natural language interface.
Validates input parameters and creates tasks in the database with proper
user isolation.
"""

import logging
from typing import Optional
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.task import Task
from src.mcp_tools.base import (
    BaseMCPTool,
    DatabaseOperationError,
    MCPToolError,
    UserValidationError,
    handle_tool_errors,
)


# ============================================================================
# Logging Configuration
# ============================================================================

logger = logging.getLogger(__name__)


# ============================================================================
# Custom Exceptions for Add Task Validation
# ============================================================================

class TaskValidationError(MCPToolError):
    """
    Exception raised when task input validation fails.

    Raised when:
    - title is missing or empty
    - title exceeds maximum length
    - description exceeds maximum length
    - Input format is invalid
    """

    def __init__(self, message: str):
        super().__init__(message, code="TASK_VALIDATION_ERROR")


# ============================================================================
# Add Task Tool
# ============================================================================

class AddTaskTool(BaseMCPTool):
    """
    MCP tool for adding new tasks to the todo list.

    Validates input parameters and creates tasks with proper user isolation.
    Provides clear error messages for AI agent understanding.

    Usage:
        >>> tool = AddTaskTool()
        >>> result = await tool.execute(
        ...     user_id="550e8400-e29b-41d4-a716-446655440000",
        ...     title="Buy groceries",
        ...     description="Milk, eggs, bread"
        ... )
        >>> print(result)
        {
            "success": True,
            "message": "Task created successfully",
            "data": {
                "id": 1,
                "title": "Buy groceries",
                "description": "Milk, eggs, bread",
                "completed": False
            }
        }
    """

    tool_name = "add_task"
    tool_description = """
    Create a new task for the user.

    Use this tool when the user wants to add a new task to their todo list.
    The task will be associated with the user and can be managed through
    natural language commands.

    Parameters:
        user_id (str): Required - User's unique identifier (UUID format)
        title (str): Required - Task title (max 500 characters, must not be empty)
        description (str): Optional - Detailed task description (max 5000 characters)

    Returns:
        dict: Task object with id, title, description, and completed status

    Example:
        User says: "Add a task to buy groceries"
        Agent calls: add_task(user_id="...", title="Buy groceries")

        User says: "Remind me to call the dentist tomorrow at 3pm"
        Agent calls: add_task(user_id="...", title="Call dentist", description="Tomorrow at 3pm")
    """

    # Validation constraints
    MAX_TITLE_LENGTH = 500
    MAX_DESCRIPTION_LENGTH = 5000

    def __init__(self):
        """Initialize the add task tool."""
        super().__init__()
        self.logger.info("AddTaskTool initialized")

    def validate_title(self, title: str) -> str:
        """
        Validate task title.

        Ensures title is:
        - Present (not None or empty after stripping)
        - Not exceeding maximum length
        - Meaningful content

        Args:
            title: The task title to validate

        Returns:
            str: Validated title (stripped of leading/trailing whitespace)

        Raises:
            TaskValidationError: If title validation fails

        Examples:
            >>> self.validate_title("Buy groceries")
            'Buy groceries'

            >>> self.validate_title("  Call dentist  ")
            'Call dentist'

            >>> self.validate_title("")  # Raises TaskValidationError
            TaskValidationError: Task title is required and cannot be empty

            >>> self.validate_title("a" * 501)  # Raises TaskValidationError
            TaskValidationError: Task title cannot exceed 500 characters (got 501)
        """
        if title is None:
            self.logger.warning("Title validation failed: title is None")
            raise TaskValidationError(
                "Task title is required and cannot be empty"
            )

        # Convert to string if not already
        if not isinstance(title, str):
            self.logger.warning(f"Title validation failed: title is not a string (got {type(title)})")
            raise TaskValidationError(
                f"Task title must be a string, got {type(title).__name__}"
            )

        # Strip whitespace
        stripped_title = title.strip()

        # Check if empty after stripping
        if not stripped_title:
            self.logger.warning("Title validation failed: title is empty after stripping")
            raise TaskValidationError(
                "Task title is required and cannot be empty or only whitespace"
            )

        # Check length
        if len(stripped_title) > self.MAX_TITLE_LENGTH:
            actual_length = len(stripped_title)
            self.logger.warning(
                f"Title validation failed: title exceeds maximum length "
                f"({actual_length} > {self.MAX_TITLE_LENGTH})"
            )
            raise TaskValidationError(
                f"Task title cannot exceed {self.MAX_TITLE_LENGTH} characters "
                f"(got {actual_length} characters)"
            )

        self.logger.info(f"Title validated successfully: '{stripped_title[:50]}...'")
        return stripped_title

    def validate_description(self, description: Optional[str]) -> Optional[str]:
        """
        Validate optional task description.

        Ensures description:
        - Is None or a string
        - Does not exceed maximum length (if provided)

        Args:
            description: The task description to validate (optional)

        Returns:
            Optional[str]: Validated description (stripped if provided, None otherwise)

        Raises:
            TaskValidationError: If description validation fails

        Examples:
            >>> self.validate_description("Detailed notes here")
            'Detailed notes here'

            >>> self.validate_description(None)
            None

            >>> self.validate_description("  Notes with spaces  ")
            'Notes with spaces'

            >>> self.validate_description("a" * 5001)  # Raises TaskValidationError
            TaskValidationError: Task description cannot exceed 5000 characters (got 5001)
        """
        # None is allowed (description is optional)
        if description is None:
            return None

        # Must be a string if provided
        if not isinstance(description, str):
            self.logger.warning(
                f"Description validation failed: description is not a string "
                f"(got {type(description)})"
            )
            raise TaskValidationError(
                f"Task description must be a string, got {type(description).__name__}"
            )

        # Strip whitespace
        stripped_description = description.strip()

        # Empty string is treated as None
        if not stripped_description:
            return None

        # Check length
        if len(stripped_description) > self.MAX_DESCRIPTION_LENGTH:
            actual_length = len(stripped_description)
            self.logger.warning(
                f"Description validation failed: description exceeds maximum length "
                f"({actual_length} > {self.MAX_DESCRIPTION_LENGTH})"
            )
            raise TaskValidationError(
                f"Task description cannot exceed {self.MAX_DESCRIPTION_LENGTH} characters "
                f"(got {actual_length} characters)"
            )

        self.logger.info(f"Description validated successfully (length: {len(stripped_description)})")
        return stripped_description

    @handle_tool_errors
    async def execute(
        self,
        user_id: str,
        title: str,
        description: Optional[str] = None
    ) -> dict:
        """
        Execute the add_task tool.

        Validates input parameters, creates task in database, and returns result.

        Args:
            user_id: User's unique identifier (UUID string from JWT token)
            title: Task title (required)
            description: Optional detailed description

        Returns:
            dict: Standardized response with created task data
            {
                "success": True,
                "message": "Task created successfully",
                "data": {
                    "id": 1,
                    "title": "Buy groceries",
                    "description": "Milk, eggs, bread",
                    "completed": False
                }
            }

        Raises:
            UserValidationError: If user_id is invalid
            TaskValidationError: If title or description validation fails
            DatabaseOperationError: If database operation fails

        Examples:
            >>> result = await tool.execute(
            ...     user_id="550e8400-e29b-41d4-a716-446655440000",
            ...     title="Buy groceries"
            ... )
            >>> print(result["success"])
            True

            >>> result = await tool.execute(
            ...     user_id="invalid-uuid",
            ...     title="Test"
            ... )
            # Raises UserValidationError
        """
        self.logger.info(f"Executing add_task for user_id: {user_id}")

        # Step 1: Validate user_id (inherited from BaseMCPTool)
        try:
            validated_user_id = await self.validate_user_id(user_id)
        except UserValidationError as e:
            self.logger.error(f"User validation failed: {e.message}")
            raise

        # Step 2: Validate title
        try:
            validated_title = self.validate_title(title)
        except TaskValidationError as e:
            self.logger.error(f"Title validation failed: {e.message}")
            raise

        # Step 3: Validate description (optional)
        try:
            validated_description = self.validate_description(description)
        except TaskValidationError as e:
            self.logger.error(f"Description validation failed: {e.message}")
            raise

        # Step 4: Create task in database
        try:
            async with self.get_db_session() as session:
                # Create task instance
                task = Task(
                    user_id=validated_user_id,
                    title=validated_title,
                    description=validated_description
                )

                # Add to database
                session.add(task)
                await session.commit()
                await session.refresh(task)

                self.logger.info(
                    f"Task created successfully: id={task.id}, "
                    f"title='{task.title[:50]}...', user_id={user_id}"
                )

                # Format success response
                return self.format_success_response(
                    data={
                        "id": task.id,
                        "title": task.title,
                        "description": task.description,
                        "completed": task.completed
                    },
                    message="Task created successfully"
                )

        except SQLAlchemyError as e:
            self.logger.error(f"Database error while creating task: {str(e)}")
            await self.handle_database_error(e)
            raise  # Should not reach here due to re-raise in handle_database_error

        except Exception as e:
            self.logger.error(f"Unexpected error while creating task: {str(e)}")
            raise MCPToolError(
                message=f"An unexpected error occurred while creating the task: {str(e)}",
                code="INTERNAL_ERROR"
            )


# ============================================================================
# Convenience Function (for easier MCP registration)
# ============================================================================

async def add_task(
    user_id: str,
    title: str,
    description: Optional[str] = None
) -> dict:
    """
    Convenience function for adding a task.

    This function provides a simple interface that can be easily
    registered with the MCP server.

    Args:
        user_id: User's unique identifier (UUID string)
        title: Task title (required, max 500 characters)
        description: Optional task description (max 5000 characters)

    Returns:
        dict: Created task data

    Example:
        >>> result = await add_task(
        ...     user_id="550e8400-e29b-41d4-a716-446655440000",
        ...     title="Buy groceries",
        ...     description="Milk, eggs, bread"
        ... )
        >>> print(result["data"]["title"])
        'Buy groceries'
    """
    tool = AddTaskTool()
    return await tool.execute(user_id=user_id, title=title, description=description)


# ============================================================================
# MCP Tool Registration Schema
# ============================================================================

# JSON Schema for MCP tool registration
# This schema is used by the MCP server to register the tool with AI agents
ADD_TASK_SCHEMA = {
    "name": "add_task",
    "description": AddTaskTool.tool_description.strip(),
    "inputSchema": {
        "type": "object",
        "properties": {
            "user_id": {
                "type": "string",
                "format": "uuid",
                "description": "User's unique identifier (UUID from JWT token)"
            },
            "title": {
                "type": "string",
                "minLength": 1,
                "maxLength": 500,
                "description": "Task title (required, max 500 characters)"
            },
            "description": {
                "type": "string",
                "maxLength": 5000,
                "description": "Optional detailed task description (max 5000 characters)"
            }
        },
        "required": ["user_id", "title"]
    }
}


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "AddTaskTool",
    "add_task",
    "TaskValidationError",
    "ADD_TASK_SCHEMA",
]
