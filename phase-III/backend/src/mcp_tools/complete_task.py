"""
Complete Task MCP Tool for Todo AI Chatbot.

Provides task completion functionality through natural language interface.
Validates task ownership and marks tasks as completed with proper
user isolation.
"""

import logging
from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, select
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
# Custom Exceptions for Complete Task Validation
# ============================================================================

class TaskOwnershipError(MCPToolError):
    """
    Exception raised when task ownership validation fails.

    Raised when:
    - Task doesn't exist
    - Task belongs to a different user
    """

    def __init__(self, message: str):
        super().__init__(message, code="TASK_OWNERSHIP_ERROR")


class TaskNotFoundError(MCPToolError):
    """
    Exception raised when task is not found in database.

    Raised when:
    - task_id doesn't exist
    - Generic "not found" to prevent task enumeration
    """

    def __init__(self, message: str = "Task not found"):
        super().__init__(message, code="TASK_NOT_FOUND")


# ============================================================================
# Complete Task Tool
# ============================================================================

class CompleteTaskTool(BaseMCPTool):
    """
    MCP tool for marking tasks as completed.

    Validates task ownership and updates task completion status.
    Provides clear error messages for AI agent understanding.

    Usage:
        >>> tool = CompleteTaskTool()
        >>> result = await tool.execute(
        ...     session=session,
        ...     user_id="550e8400-e29b-41d4-a716-446655440000",
        ...     task_id=1
        ... )
        >>> print(result)
        {
            "success": True,
            "message": "Task marked as completed",
            "data": {
                "id": 1,
                "title": "Buy groceries",
                "completed": True,
                "updated_at": "2025-01-19T15:30:00"
            }
        }
    """

    tool_name = "complete_task"
    tool_description = """
    Mark a task as completed for the user.

    Use this tool when the user wants to mark a task as done or completed.
    Validates that the task belongs to the user before updating.

    Parameters:
        user_id (str): Required - User's unique identifier (UUID format)
        task_id (int): Required - Task's unique identifier (integer)

    Returns:
        dict: Task object with id, title, completed status, and updated_at timestamp

    Example:
        User says: "Mark task 3 as done"
        → complete_task(user_id="uuid", task_id=3)

        User says: "I finished buying groceries"
        → Agent identifies task by title, then complete_task(user_id="uuid", task_id=1)
    """

    @handle_tool_errors
    async def execute(
        self,
        session: AsyncSession,
        user_id: str,
        task_id: int
    ) -> dict:
        """
        Execute the complete_task tool.

        Args:
            session: Async SQLAlchemy session
            user_id: User's UUID string
            task_id: Task's integer ID

        Returns:
            dict with success status, message, and task data

        Raises:
            UserValidationError: If user_id is invalid UUID
            TaskOwnershipError: If task doesn't belong to user
            TaskNotFoundError: If task doesn't exist (generic error)
            DatabaseOperationError: If database operation fails
        """
        # Validate user_id
        validated_user_id = self.validate_user_id(user_id)

        # Validate task_id
        if not isinstance(task_id, int) or task_id <= 0:
            logger.warning(f"Invalid task_id format: {task_id}")
            raise TaskNotFoundError("Invalid task ID")

        logger.info(f"Completing task {task_id} for user {validated_user_id}")

        try:
            # Fetch task with ownership validation (T046)
            task = await self._fetch_task_with_ownership(
                session, validated_user_id, task_id
            )

            # Check if already completed (idempotent)
            if task.completed:
                logger.info(f"Task {task_id} is already completed")
                return self.format_success_response({
                    "message": "Task is already completed",
                    "task": {
                        "id": task.id,
                        "title": task.title,
                        "completed": True,
                        "updated_at": task.updated_at.isoformat()
                    }
                })

            # Update task completion status (T045)
            task.completed = True
            task.updated_at = datetime.utcnow()

            await session.commit()
            await session.refresh(task)

            logger.info(f"Task {task_id} marked as completed successfully")

            return self.format_success_response({
                "message": "Task marked as completed",
                "task": {
                    "id": task.id,
                    "title": task.title,
                    "completed": task.completed,
                    "updated_at": task.updated_at.isoformat()
                }
            })

        except TaskNotFoundError:
            # Re-raise task not found errors
            raise
        except TaskOwnershipError:
            # Re-raise ownership errors
            raise
        except SQLAlchemyError as e:
            logger.error(f"Database error completing task {task_id}: {e}")
            await session.rollback()
            raise DatabaseOperationError(
                f"Failed to complete task: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error completing task {task_id}: {e}")
            await session.rollback()
            raise DatabaseOperationError(
                f"An unexpected error occurred: {str(e)}"
            )

    async def _fetch_task_with_ownership(
        self,
        session: AsyncSession,
        user_id: UUID,
        task_id: int
    ) -> Task:
        """
        Fetch task with ownership validation (T046).

        Verifies that:
        1. Task exists
        2. Task belongs to the specified user

        Args:
            session: Async SQLAlchemy session
            user_id: Validated user UUID
            task_id: Task ID to fetch

        Returns:
            Task object if found and owned by user

        Raises:
            TaskNotFoundError: If task doesn't exist (generic error)
            TaskOwnershipError: If task belongs to different user
        """
        try:
            # Query task by ID and user_id (ownership check)
            statement = select(Task).where(
                and_(
                    Task.id == task_id,
                    Task.user_id == user_id
                )
            )

            result = await session.execute(statement)
            task = result.scalar_one_or_none()

            # Check if task exists
            if task is None:
                # Generic error to prevent task enumeration
                logger.warning(f"Task {task_id} not found for user {user_id}")
                raise TaskNotFoundError("Task not found")

            logger.info(f"Task {task_id} ownership validated for user {user_id}")
            return task

        except TaskNotFoundError:
            # Re-raise task not found
            raise
        except Exception as e:
            logger.error(f"Error fetching task {task_id}: {e}")
            raise TaskNotFoundError("Error accessing task")


# ============================================================================
# Entry Point Function for MCP Registration
# ============================================================================

async def complete_task(
    session: AsyncSession,
    user_id: str,
    task_id: int
) -> dict:
    """
    Entry point for complete_task MCP tool.

    This function is registered with the MCP server and called by
    the OpenAI agent through the tool adapter.

    Args:
        session: Async SQLAlchemy session
        user_id: User's UUID string
        task_id: Task's integer ID

    Returns:
        dict with success status and task data
    """
    tool = CompleteTaskTool()
    return await tool.execute(session, user_id, task_id)


# ============================================================================
# MCP Schema for Tool Registration
# ============================================================================

COMPLETE_TASK_SCHEMA = {
    "name": "complete_task",
    "description": CompleteTaskTool.tool_description,
    "inputSchema": {
        "type": "object",
        "properties": {
            "user_id": {
                "type": "string",
                "format": "uuid",
                "description": "User's unique identifier"
            },
            "task_id": {
                "type": "integer",
                "minimum": 1,
                "description": "Task's unique identifier to mark as completed"
            }
        },
        "required": ["user_id", "task_id"]
    }
}


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "CompleteTaskTool",
    "complete_task",
    "COMPLETE_TASK_SCHEMA",
    "TaskOwnershipError",
    "TaskNotFoundError",
]
