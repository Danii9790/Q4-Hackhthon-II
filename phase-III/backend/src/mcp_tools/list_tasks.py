"""
List Tasks MCP Tool for Todo AI Chatbot.

Provides task listing and filtering functionality through natural language interface.
Validates input parameters and queries tasks from the database with proper
user isolation and flexible filtering options.
"""

import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
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
# Custom Exceptions for List Tasks Validation
# ============================================================================

class TaskFilterValidationError(MCPToolError):
    """
    Exception raised when task filter validation fails.

    Raised when:
    - status parameter is invalid (not one of: all, pending, completed)
    - Input format is invalid
    """

    def __init__(self, message: str):
        super().__init__(message, code="TASK_FILTER_VALIDATION_ERROR")


# ============================================================================
# List Tasks Tool
# ============================================================================

class ListTasksTool(BaseMCPTool):
    """
    MCP tool for listing user tasks with optional status filtering.

    Validates status parameter and queries tasks with proper user isolation.
    Provides clear error messages for AI agent understanding.

    Usage:
        >>> tool = ListTasksTool()
        >>> result = await tool.execute(
        ...     user_id="550e8400-e29b-41d4-a716-446655440000",
        ...     status="pending"
        ... )
        >>> print(result)
        {
            "success": True,
            "message": "Found 2 pending tasks",
            "data": [
                {
                    "id": 1,
                    "title": "Buy groceries",
                    "description": "Milk, eggs, bread",
                    "completed": False,
                    "created_at": "2024-01-15T10:30:00"
                },
                {
                    "id": 2,
                    "title": "Call dentist",
                    "description": "Schedule appointment",
                    "completed": False,
                    "created_at": "2024-01-15T11:00:00"
                }
            ]
        }
    """

    tool_name = "list_tasks"
    tool_description = """
    List and filter tasks for the user.

    Use this tool when the user wants to see their tasks. Supports filtering
    by completion status (all, pending, completed). Tasks are ordered by
    creation date (newest first). Returns empty list if no tasks found.

    Parameters:
        user_id (str): Required - User's unique identifier (UUID format)
        status (str): Optional - Filter by completion status
                      - "all": Return all tasks (default)
                      - "pending": Return only incomplete tasks
                      - "completed": Return only completed tasks

    Returns:
        dict: List of tasks with id, title, description, completed status, and created_at

    Example:
        User says: "Show me my tasks"
        Agent calls: list_tasks(user_id="...", status="all")

        User says: "What tasks do I have left?"
        Agent calls: list_tasks(user_id="...", status="pending")

        User says: "Show me completed tasks"
        Agent calls: list_tasks(user_id="...", status="completed")
    """

    # Valid status values
    VALID_STATUS_VALUES = ["all", "pending", "completed"]

    def __init__(self):
        """Initialize the list tasks tool."""
        super().__init__()
        self.logger.info("ListTasksTool initialized")

    def validate_status(self, status: Optional[str]) -> str:
        """
        Validate status filter parameter.

        Ensures status is one of the valid values: all, pending, completed.

        Args:
            status: The status filter to validate

        Returns:
            str: Validated status (lowercase)

        Raises:
            TaskFilterValidationError: If status validation fails

        Examples:
            >>> self.validate_status("all")
            'all'

            >>> self.validate_status("PENDING")
            'pending'

            >>> self.validate_status(None)
            'all'

            >>> self.validate_status("invalid")  # Raises TaskFilterValidationError
            TaskFilterValidationError: Invalid status filter: 'invalid'. Must be one of: all, pending, completed
        """
        # Default to "all" if not provided
        if status is None:
            self.logger.info("No status filter provided, defaulting to 'all'")
            return "all"

        # Must be a string if provided
        if not isinstance(status, str):
            self.logger.warning(
                f"Status validation failed: status is not a string (got {type(status)})"
            )
            raise TaskFilterValidationError(
                f"Status filter must be a string, got {type(status).__name__}"
            )

        # Convert to lowercase and strip whitespace
        normalized_status = status.strip().lower()

        # Check if empty after stripping
        if not normalized_status:
            self.logger.info("Status filter is empty, defaulting to 'all'")
            return "all"

        # Validate against allowed values
        if normalized_status not in self.VALID_STATUS_VALUES:
            self.logger.warning(
                f"Status validation failed: '{normalized_status}' is not a valid status"
            )
            raise TaskFilterValidationError(
                f"Invalid status filter: '{status}'. Must be one of: {', '.join(self.VALID_STATUS_VALUES)}"
            )

        self.logger.info(f"Status validated successfully: '{normalized_status}'")
        return normalized_status

    def build_task_query(
        self,
        user_id: UUID,
        status: str
    ) -> select:
        """
        Build SQLAlchemy query for fetching tasks with filters.

        Constructs efficient database query with proper filtering and ordering.
        Uses indexed columns for optimal performance.

        Args:
            user_id: Validated user UUID (for data isolation)
            status: Validated status filter (all, pending, or completed)

        Returns:
            select: SQLAlchemy select query object

        Examples:
            >>> query = self.build_task_query(user_uuid, "pending")
            >>> # Returns query filtering by user_id and completed=False, ordered by created_at DESC
        """
        # Start with base query selecting Task
        query = select(Task).where(Task.user_id == user_id)

        # Apply status filter if not "all"
        if status == "pending":
            query = query.where(Task.completed == False)
            self.logger.debug(f"Query filtered for pending tasks (user_id={user_id})")
        elif status == "completed":
            query = query.where(Task.completed == True)
            self.logger.debug(f"Query filtered for completed tasks (user_id={user_id})")
        else:  # status == "all"
            self.logger.debug(f"Query includes all tasks (user_id={user_id})")

        # Order by created_at DESC (newest first)
        query = query.order_by(Task.created_at.desc())
        self.logger.debug("Query ordered by created_at DESC")

        return query

    def format_task_dict(self, task: Task) -> dict:
        """
        Format a Task model instance as a dictionary.

        Converts Task object to JSON-serializable dictionary with
        ISO-formatted timestamps.

        Args:
            task: Task model instance

        Returns:
            dict: Task data as dictionary

        Example:
            >>> task = Task(id=1, title="Buy groceries", completed=False)
            >>> self.format_task_dict(task)
            {
                "id": 1,
                "title": "Buy groceries",
                "description": None,
                "completed": False,
                "created_at": "2025-01-15T10:30:00",
                "updated_at": "2025-01-15T10:30:00"
            }
        """
        return {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "completed": task.completed,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,
        }

    @handle_tool_errors
    async def execute(
        self,
        user_id: str,
        status: Optional[str] = None
    ) -> dict:
        """
        Execute the list_tasks tool.

        Validates input parameters, queries tasks from database, and returns result.

        Args:
            user_id: User's unique identifier (UUID string from JWT token)
            status: Optional status filter (all, pending, or completed; defaults to "all")

        Returns:
            dict: Standardized response with list of tasks
            {
                "success": True,
                "message": "Retrieved 2 pending tasks",
                "data": {
                    "tasks": [...],
                    "count": 2
                }
            }

        Raises:
            UserValidationError: If user_id is invalid
            TaskFilterValidationError: If status validation fails
            DatabaseOperationError: If database operation fails

        Examples:
            >>> result = await tool.execute(
            ...     user_id="550e8400-e29b-41d4-a716-446655440000",
            ...     status="pending"
            ... )
            >>> print(result["success"])
            True

            >>> result = await tool.execute(
            ...     user_id="550e8400-e29b-41d4-a716-446655440000",
            ...     status="invalid"
            ... )
            # Raises TaskFilterValidationError
        """
        self.logger.info(f"Executing list_tasks for user_id: {user_id}, status: {status}")

        # Step 1: Validate user_id (inherited from BaseMCPTool)
        try:
            validated_user_id = await self.validate_user_id(user_id)
        except UserValidationError as e:
            self.logger.error(f"User validation failed: {e.message}")
            raise

        # Step 2: Validate status filter
        try:
            validated_status = self.validate_status(status)
        except TaskFilterValidationError as e:
            self.logger.error(f"Status validation failed: {e.message}")
            raise

        # Step 3: Query tasks from database
        try:
            async with self.get_db_session() as session:
                # Build query with filters
                query = self.build_task_query(validated_user_id, validated_status)

                # Execute query
                result = await session.execute(query)
                tasks = result.scalars().all()

                # Format tasks as dictionaries
                task_list = [self.format_task_dict(task) for task in tasks]

                # Generate descriptive message
                task_count = len(task_list)
                if task_count == 0:
                    message = f"No {validated_status} tasks found"
                elif task_count == 1:
                    message = f"Retrieved 1 {validated_status} task"
                else:
                    message = f"Retrieved {task_count} {validated_status} tasks"

                self.logger.info(
                    f"Successfully retrieved {task_count} tasks "
                    f"(user_id={user_id}, status={validated_status})"
                )

                # Format success response
                return self.format_success_response(
                    data={
                        "tasks": task_list,
                        "count": task_count
                    },
                    message=message
                )

        except SQLAlchemyError as e:
            self.logger.error(f"Database error while listing tasks: {str(e)}")
            await self.handle_database_error(e)
            raise  # Should not reach here due to re-raise in handle_database_error

        except Exception as e:
            self.logger.error(f"Unexpected error while listing tasks: {str(e)}")
            raise MCPToolError(
                message=f"An unexpected error occurred while listing tasks: {str(e)}",
                code="INTERNAL_ERROR"
            )


# ============================================================================
# Convenience Function (for easier MCP registration)
# ============================================================================

async def list_tasks(
    user_id: str,
    status: Optional[str] = None
) -> dict:
    """
    Convenience function for listing tasks.

    This function provides a simple interface that can be easily
    registered with the MCP server.

    Args:
        user_id: User's unique identifier (UUID string)
        status: Optional status filter (all, pending, or completed; defaults to "all")

    Returns:
        dict: List of tasks with count

    Example:
        >>> result = await list_tasks(
        ...     user_id="550e8400-e29b-41d4-a716-446655440000",
        ...     status="pending"
        ... )
        >>> print(result["data"]["count"])
        2
    """
    tool = ListTasksTool()
    return await tool.execute(user_id=user_id, status=status)


# ============================================================================
# MCP Tool Registration Schema
# ============================================================================

# JSON Schema for MCP tool registration
# This schema is used by the MCP server to register the tool with AI agents
LIST_TASKS_SCHEMA = {
    "name": "list_tasks",
    "description": ListTasksTool.tool_description.strip(),
    "inputSchema": {
        "type": "object",
        "properties": {
            "user_id": {
                "type": "string",
                "format": "uuid",
                "description": "User's unique identifier (UUID from JWT token)"
            },
            "status": {
                "type": "string",
                "enum": ["all", "pending", "completed"],
                "default": "all",
                "description": "Optional status filter (default: 'all')"
            }
        },
        "required": ["user_id"]
    }
}


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "ListTasksTool",
    "list_tasks",
    "TaskFilterValidationError",
    "LIST_TASKS_SCHEMA",
]
