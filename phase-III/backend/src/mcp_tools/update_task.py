"""
Update Task MCP Tool for Todo AI Chatbot.

Provides task modification functionality through natural language interface.
Validates task ownership and updates task details with proper user isolation.
"""

import logging
from datetime import datetime
from typing import Optional
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
# Custom Exceptions for Update Task Validation
# ============================================================================

class TaskUpdateValidationError(MCPToolError):
    """
    Exception raised when task update validation fails.

    Raised when:
    - Neither title nor description is provided
    - Both title and description are None
    - Title exceeds maximum length
    """

    def __init__(self, message: str):
        super().__init__(message, code="TASK_UPDATE_VALIDATION_ERROR")


class TaskOwnershipError(MCPToolError):
    """
    Exception raised when task ownership validation fails.

    Raised when:
    - Task doesn't exist
    - Task belongs to a different user
    """

    def __init__(self, message: str):
        super().__init__(message, code="TASK_OWNERSHIP_ERROR")


# ============================================================================
# Update Task Tool
# ============================================================================

class UpdateTaskTool(BaseMCPTool):
    """
    MCP tool for updating task details.

    Validates task ownership and updates task title and/or description.
    Provides clear error messages for AI agent understanding.

    Usage:
        >>> tool = UpdateTaskTool()
        >>> result = await tool.execute(
        ...     session=session,
        ...     user_id="550e8400-e29b-41d4-a716-446655440000",
        ...     task_id=1,
        ...     title="Updated title",
        ...     description="New description"
        ... )
        >>> print(result)
        {
            "success": True,
            "message": "Task updated successfully",
            "data": {
                "id": 1,
                "title": "Updated title",
                "description": "New description",
                "completed": False,
                "updated_at": "2025-01-19T16:00:00"
            }
        }
    """

    tool_name = "update_task"
    tool_description = """
    Update a task's title and/or description for the user.

    Use this tool when the user wants to modify, change, or update an existing task.
    At least one of title or description must be provided. Validates that the task
    belongs to the user before updating.

    Parameters:
        user_id (str): Required - User's unique identifier (UUID format)
        task_id (int): Required - Task's unique identifier (integer)
        title (str): Optional - New task title (max 500 characters)
        description (str): Optional - New task description (max 5000 characters)

    Returns:
        dict: Updated task object with id, title, description, completed status, and updated_at timestamp

    Example:
        User says: "Change the dentist task to Tuesday"
        → update_task(user_id="uuid", task_id=2, description="Tuesday")

        User says: "Update task 3 title to Buy groceries"
        → update_task(user_id="uuid", task_id=3, title="Buy groceries")
    """

    @handle_tool_errors
    async def execute(
        self,
        session: AsyncSession,
        user_id: str,
        task_id: int,
        title: Optional[str] = None,
        description: Optional[str] = None
    ) -> dict:
        """
        Execute the update_task tool.

        Args:
            session: Async SQLAlchemy session
            user_id: User's UUID string
            task_id: Task's integer ID
            title: Optional new title
            description: Optional new description

        Returns:
            dict with success status, message, and updated task data

        Raises:
            UserValidationError: If user_id is invalid UUID
            TaskUpdateValidationError: If validation fails (no fields provided)
            TaskOwnershipError: If task doesn't belong to user
            DatabaseOperationError: If database operation fails
        """
        # Validate user_id
        validated_user_id = self.validate_user_id(user_id)

        # Validate task_id
        if not isinstance(task_id, int) or task_id <= 0:
            logger.warning(f"Invalid task_id format: {task_id}")
            raise TaskOwnershipError("Invalid task ID")

        # Validate at least one field is provided (T053)
        if title is None and description is None:
            logger.warning("Update task called with no fields to update")
            raise TaskUpdateValidationError(
                "At least one of title or description must be provided"
            )

        # Validate title if provided
        if title is not None:
            title = title.strip()
            if not title:
                raise TaskUpdateValidationError("Title cannot be empty")
            if len(title) > 500:
                raise TaskUpdateValidationError("Title cannot exceed 500 characters")

        # Validate description if provided
        if description is not None:
            description = description.strip()
            if len(description) > 5000:
                raise TaskUpdateValidationError("Description cannot exceed 5000 characters")

        logger.info(
            f"Updating task {task_id} for user {validated_user_id}: "
            f"title={title is not None}, description={description is not None}"
        )

        try:
            # Fetch task with ownership validation
            task = await self._fetch_task_with_ownership(
                session, validated_user_id, task_id
            )

            # Track changes for confirmation response (T057)
            changes = []
            if title is not None and task.title != title:
                old_title = task.title
                task.title = title
                changes.append(f"title from '{old_title}' to '{title}'")

            if description is not None and task.description != description:
                old_desc = task.description or "none"
                task.description = description
                changes.append(f"description to '{description}'")

            # If no actual changes, return early
            if not changes:
                logger.info(f"No changes needed for task {task_id}")
                return self.format_success_response({
                    "message": "No changes needed",
                    "task": {
                        "id": task.id,
                        "title": task.title,
                        "description": task.description,
                        "completed": task.completed,
                        "updated_at": task.updated_at.isoformat()
                    }
                })

            # Update timestamp (T052)
            task.updated_at = datetime.utcnow()

            await session.commit()
            await session.refresh(task)

            logger.info(f"Task {task_id} updated successfully")

            return self.format_success_response({
                "message": f"Task updated: {', '.join(changes)}",
                "task": {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "completed": task.completed,
                    "updated_at": task.updated_at.isoformat()
                }
            })

        except TaskOwnershipError:
            # Re-raise ownership errors
            raise
        except SQLAlchemyError as e:
            logger.error(f"Database error updating task {task_id}: {e}")
            await session.rollback()
            raise DatabaseOperationError(
                f"Failed to update task: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error updating task {task_id}: {e}")
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
        Fetch task with ownership validation.

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
            TaskOwnershipError: If task doesn't exist or belongs to different user
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
                raise TaskOwnershipError("Task not found")

            logger.info(f"Task {task_id} ownership validated for user {user_id}")
            return task

        except TaskOwnershipError:
            # Re-raise task not found
            raise
        except Exception as e:
            logger.error(f"Error fetching task {task_id}: {e}")
            raise TaskOwnershipError("Error accessing task")


# ============================================================================
# Entry Point Function for MCP Registration
# ============================================================================

async def update_task(
    session: AsyncSession,
    user_id: str,
    task_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None
) -> dict:
    """
    Entry point for update_task MCP tool.

    This function is registered with the MCP server and called by
    the OpenAI agent through the tool adapter.

    Args:
        session: Async SQLAlchemy session
        user_id: User's UUID string
        task_id: Task's integer ID
        title: Optional new title
        description: Optional new description

    Returns:
        dict with success status and updated task data
    """
    tool = UpdateTaskTool()
    return await tool.execute(session, user_id, task_id, title, description)


# ============================================================================
# MCP Schema for Tool Registration
# ============================================================================

UPDATE_TASK_SCHEMA = {
    "name": "update_task",
    "description": UpdateTaskTool.tool_description,
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
                "description": "Task's unique identifier to update"
            },
            "title": {
                "type": "string",
                "minLength": 1,
                "maxLength": 500,
                "description": "New task title (optional)"
            },
            "description": {
                "type": "string",
                "maxLength": 5000,
                "description": "New task description (optional)"
            }
        },
        "required": ["user_id", "task_id"]
    }
}


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "UpdateTaskTool",
    "update_task",
    "UPDATE_TASK_SCHEMA",
    "TaskUpdateValidationError",
    "TaskOwnershipError",
]
