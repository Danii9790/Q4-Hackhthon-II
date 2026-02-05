"""
Delete Task MCP Tool for Todo AI Chatbot.

Provides task deletion functionality through natural language interface.
Validates task ownership before performing deletion with proper user isolation.
"""

import logging
from uuid import UUID

from sqlalchemy import and_, delete, select
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


logger = logging.getLogger(__name__)


class TaskOwnershipError(MCPToolError):
    def __init__(self, message: str):
        super().__init__(message, code="TASK_OWNERSHIP_ERROR")


class DeleteTaskTool(BaseMCPTool):
    tool_name = "delete_task"
    tool_description = """
    Delete a task for the user.

    Use this tool when the user wants to permanently remove a task.
    Validates that the task belongs to the user before deletion.

    Parameters:
        user_id (str): Required - User's unique identifier (UUID format)
        task_id (int): Required - Task's unique identifier (integer)

    Returns:
        dict: Deletion confirmation with task details
    """

    @handle_tool_errors
    async def execute(
        self,
        session: AsyncSession,
        user_id: str,
        task_id: int
    ) -> dict:
        validated_user_id = self.validate_user_id(user_id)

        if not isinstance(task_id, int) or task_id <= 0:
            raise TaskOwnershipError("Invalid task ID")

        logger.info(f"Deleting task {task_id} for user {validated_user_id}")

        try:
            # Fetch task with ownership validation (T060)
            statement = select(Task).where(
                and_(
                    Task.id == task_id,
                    Task.user_id == validated_user_id
                )
            )
            result = await session.execute(statement)
            task = result.scalar_one_or_none()

            if task is None:
                logger.warning(f"Task {task_id} not found for user {validated_user_id}")
                raise TaskOwnershipError("Task not found")

            # Store task details for confirmation response
            task_details = {
                "id": task.id,
                "title": task.title,
                "completed": task.completed
            }

            # Delete task (T059)
            delete_stmt = delete(Task).where(Task.id == task_id)
            await session.execute(delete_stmt)
            await session.commit()

            logger.info(f"Task {task_id} deleted successfully")

            return self.format_success_response({
                "message": f"Task '{task_details['title']}' deleted successfully",
                "task": task_details
            })

        except TaskOwnershipError:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Database error deleting task {task_id}: {e}")
            await session.rollback()
            raise DatabaseOperationError(f"Failed to delete task: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error deleting task {task_id}: {e}")
            await session.rollback()
            raise DatabaseOperationError(f"An unexpected error occurred: {str(e)}")


async def delete_task(
    session: AsyncSession,
    user_id: str,
    task_id: int
) -> dict:
    tool = DeleteTaskTool()
    return await tool.execute(session, user_id, task_id)


DELETE_TASK_SCHEMA = {
    "name": "delete_task",
    "description": DeleteTaskTool.tool_description,
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
                "description": "Task's unique identifier to delete"
            }
        },
        "required": ["user_id", "task_id"]
    }
}


__all__ = [
    "DeleteTaskTool",
    "delete_task",
    "DELETE_TASK_SCHEMA",
    "TaskOwnershipError",
]
