"""
Base MCP tool class for Todo AI Chatbot.

Provides common error handling, user_id validation, and database session management
for all MCP tools. Individual tools inherit from this base class to ensure
consistent behavior across the system.
"""

import logging
from typing import Any, Optional
from uuid import UUID

from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_session


# ============================================================================
# Logging Configuration
# ============================================================================

logger = logging.getLogger(__name__)


# ============================================================================
# Exceptions
# ============================================================================

class MCPToolError(Exception):
    """
    Base exception for MCP tool errors.

    All custom tool exceptions should inherit from this class.
    """

    def __init__(self, message: str, code: str = "TOOL_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class UserValidationError(MCPToolError):
    """
    Exception raised when user_id validation fails.

    Raised when:
    - user_id is missing
    - user_id format is invalid (not a UUID)
    - user_id doesn't match authenticated user
    """

    def __init__(self, message: str = "Invalid user ID"):
        super().__init__(message, code="USER_VALIDATION_ERROR")


class DatabaseOperationError(MCPToolError):
    """
    Exception raised when database operation fails.

    Wraps SQLAlchemy errors and provides user-friendly messages.
    """

    def __init__(self, message: str = "Database operation failed"):
        super().__init__(message, code="DATABASE_ERROR")


class ResourceNotFoundError(MCPToolError):
    """
    Exception raised when requested resource is not found.

    Used when a task or conversation doesn't exist or doesn't belong to the user.
    """

    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, code="NOT_FOUND")


# ============================================================================
# Base MCP Tool Class
# ============================================================================

class BaseMCPTool:
    """
    Base class for all MCP tools in the Todo AI Chatbot.

    Provides common functionality:
    - User ID validation (UUID format and authenticity)
    - Database session management with automatic cleanup
    - Error handling with logging and user-friendly messages
    - Standardized response format

    Usage:
        class AddTaskTool(BaseMCPTool):
            async def execute(self, user_id: str, title: str, description: str = None) -> dict:
                # Validate user_id and get database session
                validated_user_id = await self.validate_user_id(user_id)

                async with self.get_db_session() as session:
                    # Perform database operations
                    task = Task(user_id=validated_user_id, title=title, description=description)
                    session.add(task)
                    await session.commit()
                    await session.refresh(task)

                    return {"id": task.id, "title": task.title, "completed": task.completed}
    """

    # Tool metadata (override in subclasses)
    tool_name: str = "base_tool"
    tool_description: str = "Base MCP tool with common functionality"

    def __init__(self):
        """
        Initialize the base tool.
        """
        self.logger = logger

    async def validate_user_id(self, user_id: str) -> UUID:
        """
        Validate and convert user_id from JWT token.

        Ensures user_id is a valid UUID format before performing database operations.
        This prevents injection attacks and ensures data isolation.

        Args:
            user_id: User ID string from JWT token (must be UUID format)

        Returns:
            UUID: Validated user UUID

        Raises:
            UserValidationError: If user_id is invalid or missing

        Example:
            >>> tool = BaseMCPTool()
            >>> user_uuid = await tool.validate_user_id("550e8400-e29b-41d4-a716-446655440000")
            >>> print(user_uuid)
            UUID('550e8400-e29b-41d4-a716-446655440000')
        """
        if not user_id:
            raise UserValidationError("User ID is required")

        try:
            validated_uuid = UUID(user_id)
            self.logger.info(f"Validated user_id: {user_id}")
            return validated_uuid
        except ValueError as e:
            self.logger.warning(f"Invalid user_id format: {user_id}")
            raise UserValidationError(f"Invalid user ID format: {str(e)}")

    async def get_db_session(self) -> AsyncSession:
        """
        Get a database session for tool operations.

        Sessions are created per request and automatically closed after use.
        Use with async context manager for proper cleanup.

        Yields:
            AsyncSession: Database session

        Example:
            >>> async with self.get_db_session() as session:
            ...     result = await session.execute(query)
            ...     return result.scalars().all()

        Note:
            Always use async context manager to ensure session cleanup:
            `async with self.get_db_session() as session:`
        """
        async for session in get_session():
            yield session
            break

    async def handle_database_error(self, error: Exception) -> None:
        """
        Handle database errors with logging and user-friendly messages.

        Wraps SQLAlchemy errors and converts them to MCPToolError.

        Args:
            error: The exception that occurred

        Raises:
            DatabaseOperationError: Always raised with user-friendly message

        Example:
            >>> try:
            ...     await session.commit()
            ... except Exception as e:
            ...     await self.handle_database_error(e)
        """
        if isinstance(error, SQLAlchemyError):
            self.logger.error(f"Database error: {str(error)}")
            raise DatabaseOperationError(
                "Database operation failed. Please try again later"
            )
        else:
            self.logger.error(f"Unexpected error: {str(error)}")
            raise DatabaseOperationError(
                f"An error occurred: {str(error)}"
            )

    def format_success_response(
        self,
        data: Any,
        message: str = "Operation completed successfully"
    ) -> dict:
        """
        Format a successful tool execution response.

        Provides consistent response format across all tools.

        Args:
            data: The result data (task, conversation, etc.)
            message: Success message describing what was done

        Returns:
            Dict with standardized success response format

        Example:
            >>> task = Task(id=1, title="Buy groceries", completed=False)
            >>> self.format_success_response(task, "Task created successfully")
            {
                "success": True,
                "message": "Task created successfully",
                "data": {"id": 1, "title": "Buy groceries", "completed": False}
            }
        """
        return {
            "success": True,
            "message": message,
            "data": data if isinstance(data, dict) else self._serialize_model(data),
        }

    def format_error_response(
        self,
        error: str,
        code: str = "TOOL_ERROR"
    ) -> dict:
        """
        Format an error response for tool execution.

        Provides consistent error format across all tools.

        Args:
            error: Error message describing what went wrong
            code: Error code for categorization

        Returns:
            Dict with standardized error response format

        Example:
            >>> self.format_error_response("Task not found", "NOT_FOUND")
            {
                "success": False,
                "error": "Task not found",
                "code": "NOT_FOUND"
            }
        """
        return {
            "success": False,
            "error": error,
            "code": code,
        }

    def _serialize_model(self, obj: Any) -> dict:
        """
        Serialize a SQLAlchemy model to dictionary.

        Converts model objects to JSON-serializable dictionaries.

        Args:
            obj: SQLAlchemy model instance

        Returns:
            Dict representation of the model

        Example:
            >>> task = Task(id=1, title="Buy groceries")
            >>> self._serialize_model(task)
            {"id": 1, "title": "Buy groceries", "completed": False}
        """
        if hasattr(obj, "__dict__"):
            return {
                key: value
                for key, value in obj.__dict__.items()
                if not key.startswith("_")
            }
        return {}


# ============================================================================
# Tool Decorator for Error Handling
# ============================================================================

def handle_tool_errors(func):
    """
    Decorator to automatically handle common tool errors.

    Catches exceptions and converts them to standardized error responses.
    This ensures consistent error handling across all tools.

    Usage:
        @handle_tool_errors
        async def my_tool(user_id: str, param: str) -> dict:
            # Tool implementation
            # Errors are automatically caught and formatted
            pass

    Args:
        func: The tool function to wrap

    Returns:
        Wrapped function with error handling

    Example:
        >>> @handle_tool_errors
        ... async def get_task(user_id: str, task_id: int) -> dict:
        ...     # If UserValidationError raised, automatically formatted
        ...     validated_user_id = await self.validate_user_id(user_id)
        ...     return {"task": task_data}
    """
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except MCPToolError as e:
            # Re-raise MCP tool errors as-is (already formatted)
            raise
        except HTTPException:
            # Re-raise HTTP exceptions directly
            raise
        except Exception as e:
            # Catch unexpected errors and log them
            logger.exception(f"Unexpected error in {func.__name__}: {str(e)}")
            raise MCPToolError(
                message=f"An unexpected error occurred: {str(e)}",
                code="INTERNAL_ERROR"
            )

    return wrapper


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "BaseMCPTool",
    "MCPToolError",
    "UserValidationError",
    "DatabaseOperationError",
    "ResourceNotFoundError",
    "handle_tool_errors",
]
