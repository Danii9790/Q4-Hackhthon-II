"""
MCP Server for Todo AI Chatbot.

This module initializes and configures the MCP (Model Context Protocol) server
using the official MCP Python SDK. The server exposes task management tools
that can be invoked by AI agents through natural language.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from mcp.server.mcpserver import Context, MCPServer
from mcp.server.session import ServerSession

from src.db.session import get_session
from src.mcp_tools.add_task import add_task
from src.mcp_tools.complete_task import complete_task
from src.mcp_tools.delete_task import delete_task
from src.mcp_tools.list_tasks import list_tasks
from src.mcp_tools.update_task import update_task


# ============================================================================
# MCP Server Configuration
# ============================================================================

# Server metadata
MCP_SERVER_NAME = "todo-ai-chatbot"
MCP_SERVER_VERSION = "1.0.0"

# Server instructions for AI agents
MCP_INSTRUCTIONS = """
You are a task management assistant for the Todo AI Chatbot.
You help users manage their tasks through natural language conversation.

Available tools:
- add_task: Create a new task with a title and optional description
- list_tasks: List all tasks or filter by completion status
- complete_task: Mark a task as completed
- update_task: Modify an existing task's title or description
- delete_task: Remove a task permanently

All operations are scoped to the authenticated user's ID.
Always validate user_id before performing any operations.
"""


# ============================================================================
# Lifespan Management
# ============================================================================

@asynccontextmanager
async def mcp_lifespan(server: MCPServer) -> AsyncIterator[None]:
    """
    MCP server lifespan manager.

    Handles server startup and shutdown lifecycle.
    Database sessions are created per-request through dependency injection.

    Args:
        server: MCPServer instance

    Yields:
        None (no shared resources needed for stateless design)
    """
    # Startup: Initialize any server-wide resources
    print(f"Starting MCP server: {MCP_SERVER_NAME}")

    yield

    # Shutdown: Clean up server-wide resources
    print(f"Shutting down MCP server: {MCP_SERVER_NAME}")


# ============================================================================
# MCP Server Instance
# ============================================================================

# Create the MCP server with lifespan management
mcp_server = MCPServer(
    name=MCP_SERVER_NAME,
    instructions=MCP_INSTRUCTIONS,
    lifespan=mcp_lifespan,
)


# ============================================================================
# MCP Tool Registration
# ============================================================================

@mcp_server.tool()
async def register_add_task(user_id: str, title: str, description: Optional[str] = None) -> dict:
    """
    Create a new task for the authenticated user.

    This MCP tool allows the AI agent to create tasks on behalf of users
    through natural language interactions. The tool validates user permissions,
    inserts the task into the database, and returns the created task details.

    **When to use this tool:**
    - User says "Add a task to buy groceries"
    - User says "Create a reminder for my meeting"
    - User says "I need to remember to call John"
    - User says "Add todo: finish the report"

    **Parameters:**
    - user_id (str, required): User UUID from JWT token for data isolation
    - title (str, required): Task title (max 500 characters, non-empty)
    - description (str, optional): Detailed task description for additional context

    **Returns:**
    Dict with created task details:
    {
        "success": True,
        "message": "Task created successfully",
        "data": {
            "id": 1,                          # Auto-generated task ID
            "title": "Buy groceries",         # Task title
            "description": "Milk, eggs...",   # Optional description
            "completed": False,               # Always False for new tasks
            "user_id": "550e8400-...",       # User UUID
            "created_at": "2026-02-01T12:00:00"  # ISO timestamp
        }
    }

    **Example Usage for AI Agent:**

    User message: "Add a task to buy groceries"

    Agent reasoning:
    1. User wants to create a new task
    2. Extract task title: "Buy groceries"
    3. No description provided (optional)
    4. Call add_task tool with user_id from JWT

    Tool call:
    ```python
    add_task(
        user_id="550e8400-e29b-41d4-a716-446655440000",
        title="Buy groceries"
    )
    ```

    Response:
    ```python
    {
        "success": True,
        "message": "Task created successfully",
        "data": {
            "id": 1,
            "title": "Buy groceries",
            "description": null,
            "completed": False,
            "user_id": "550e8400-e29b-41d4-a716-446655440000",
            "created_at": "2026-02-01T12:00:00"
        }
    }
    ```

    Agent response to user:
    "I've created a task called 'Buy groceries' for you."

    **Error Handling:**
    - UserValidationError: If user_id is invalid or missing
    - DatabaseOperationError: If database operation fails
    - ValueError: If title is empty or exceeds 500 characters

    **Important Notes:**
    - Always validate user_id from JWT token before calling
    - Title is required and must be non-empty
    - Description is optional but can provide helpful context
    - New tasks are always created with completed=False
    - Task ID is auto-generated by the database
    - All operations are isolated by user_id for data security
    """
    return await add_task(user_id, title, description)


@mcp_server.tool()
async def register_list_tasks(user_id: str, status: str = "all") -> dict:
    """
    List tasks for the authenticated user with optional status filtering.

    This MCP tool allows the AI agent to retrieve and display tasks to users
    through natural language interactions. The tool validates user permissions,
    queries tasks with optional status filtering, and returns formatted results.

    **When to use this tool:**
    - User says "Show my tasks"
    - User says "What's pending?"
    - User says "What have I completed?"
    - User says "List all my tasks"

    **Parameters:**
    - user_id (str, required): User UUID from JWT token for data isolation
    - status (str, optional): Filter by status - "all" (default), "pending", or "completed"

    **Returns:**
    Dict with list of tasks:
    {
        "success": True,
        "message": "Found 3 tasks",
        "data": {
            "tasks": [
                {
                    "id": 1,
                    "title": "Buy groceries",
                    "description": "Milk, eggs, bread",
                    "completed": False,
                    "created_at": "2026-02-01T12:00:00"
                }
            ],
            "count": 3
        }
    }

    **Example Usage for AI Agent:**

    User message: "What's pending?"

    Agent reasoning:
    1. User wants to see pending (incomplete) tasks
    2. Set status filter to "pending"
    3. Call list_tasks tool with user_id from JWT

    Tool call:
    await list_tasks(user_id="550e8400-...", status="pending")

    Tool response:
    {"success": True, "data": {"tasks": [...], "count": 5}}

    Agent response: "You have 5 pending tasks. Here they are: 1. Buy groceries..."

    **Important Notes:**
    - status="all" returns all tasks (default)
    - status="pending" returns only incomplete tasks (completed=False)
    - status="completed" returns only completed tasks (completed=True)
    - Tasks are ordered by created_at DESC (newest first)
    - All operations are isolated by user_id for data security
    """
    return await list_tasks(user_id, status)


@mcp_server.tool()
async def register_complete_task(user_id: str, task_id: int) -> dict:
    """
    Mark a task as completed for the authenticated user.

    This MCP tool allows the AI agent to mark tasks as completed through
    natural language interactions. The tool validates task ownership before
    updating the completion status.

    **When to use this tool:**
    - User says "I finished buying groceries"
    - User says "Mark task 3 as done"
    - User says "Complete the dentist task"
    - User says "I'm done with the report"

    **Parameters:**
    - user_id (str, required): User UUID from JWT token for data isolation
    - task_id (int, required): Task's unique identifier (integer)

    **Returns:**
    Dict with updated task details:
    {
        "success": True,
        "message": "Task marked as completed",
        "data": {
            "id": 1,
            "title": "Buy groceries",
            "completed": True,
            "updated_at": "2026-02-01T15:30:00"
        }
    }

    **Example Usage for AI Agent:**

    User message: "Mark task 3 as done"

    Agent reasoning:
    1. User wants to complete task with ID 3
    2. Extract task_id from message: 3
    3. Call complete_task tool with user_id from JWT

    Tool call:
    await complete_task(user_id="550e8400-...", task_id=3)

    Tool response:
    {"success": True, "data": {"task": {...}}}

    Agent response: "Great! I've marked task 3 (Buy groceries) as completed."

    **Important Notes:**
    - Task must belong to the user (ownership validation)
    - Returns error if task doesn't exist (generic message)
    - Idempotent: Can re-complete an already completed task
    - Updates completed=True and updated_at timestamp
    - All operations are isolated by user_id for data security
    """
    return await complete_task(user_id, task_id)


@mcp_server.tool()
async def register_update_task(
    user_id: str,
    task_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None
) -> dict:
    """
    Update a task's title and/or description for the authenticated user.

    This MCP tool allows the AI agent to modify existing tasks through
    natural language interactions. The tool validates task ownership before
    updating and requires at least one field to change.

    **When to use this tool:**
    - User says "Change the dentist task to Tuesday"
    - User says "Update task 2 title to Buy groceries"
    - User says "Modify the report task description"
    - User says "Edit task 5"

    **Parameters:**
    - user_id (str, required): User UUID from JWT token for data isolation
    - task_id (int, required): Task's unique identifier (integer)
    - title (str, optional): New task title (max 500 characters)
    - description (str, optional): New task description (max 5000 characters)

    **Returns:**
    Dict with updated task details:
    {
        "success": True,
        "message": "Task updated: title from 'Old' to 'New'",
        "data": {
            "id": 1,
            "title": "New title",
            "description": "New description",
            "completed": False,
            "updated_at": "2026-02-01T16:00:00"
        }
    }

    **Example Usage for AI Agent:**

    User message: "Change the dentist task to Tuesday"

    Agent reasoning:
    1. User wants to modify a task description
    2. Identify task by title: "dentist"
    3. Set new description: "Tuesday"
    4. Call update_task tool with user_id from JWT

    Tool call:
    await update_task(user_id="550e8400-...", task_id=2, description="Tuesday")

    Tool response:
    {"success": True, "data": {"task": {...}}}

    Agent response: "I've updated the dentist task. Changed description to 'Tuesday'."

    **Important Notes:**
    - At least one of title or description must be provided
    - Task must belong to the user (ownership validation)
    - Returns error if task doesn't exist (generic message)
    - Tracks changes and includes them in response for confirmation
    - Updates updated_at timestamp
    - All operations are isolated by user_id for data security
    """
    return await update_task(user_id, task_id, title, description)


@mcp_server.tool()
async def register_delete_task(user_id: str, task_id: int) -> dict:
    """
    Delete a task for the authenticated user.

    This MCP tool allows the AI agent to permanently remove tasks through
    natural language interactions. The tool validates task ownership before
    performing the deletion.

    **When to use this tool:**
    - User says "Delete the grocery task"
    - User says "Remove task 4"
    - User says "Get rid of the dentist task"
    - User says "I don't need task 2 anymore"

    **Parameters:**
    - user_id (str, required): User UUID from JWT token for data isolation
    - task_id (int, required): Task's unique identifier (integer)

    **Returns:**
    Dict with deletion confirmation:
    {
        "success": True,
        "message": "Task 'Buy groceries' deleted successfully",
        "data": {"id": 1, "title": "Buy groceries", "completed": False}
    }

    **Important Notes:**
    - Deletion is permanent and cannot be undone
    - Task must belong to the user (ownership validation)
    - Returns error if task doesn't exist (generic message)
    - All operations are isolated by user_id for data security
    """
    return await delete_task(user_id, task_id)


# ============================================================================
# Tool Registration Decorators
# ============================================================================

def register_tool(func):
    """
    Decorator to register a function as an MCP tool.

    This decorator wraps functions to be registered with the MCP server.
    Tools must accept user_id as their first parameter for data isolation.

    Usage:
        @register_tool
        async def my_tool(user_id: str, param1: str, param2: int) -> str:
            # Tool implementation
            pass

    Args:
        func: Function to register as an MCP tool

    Returns:
        Wrapped function
    """
    # The actual registration happens when tools are imported
    # This decorator serves as documentation and future extensibility
    return func


# ============================================================================
# Dynamic User Context Injection
# ============================================================================

async def get_db_session_for_user(user_id: str) -> AsyncSession:
    """
    Get a database session for a specific user.

    In the MCP context, user_id is extracted from the JWT token
    and injected into tool calls by the agent system.

    Args:
        user_id: User UUID from JWT token

    Returns:
        AsyncSession: Database session
    """
    # This will be used by individual tool implementations
    # The session is created per-request
    async for session in get_session():
        yield session
        break


# ============================================================================
# Server Information
# ============================================================================

def get_server_info() -> dict:
    """
    Get information about the MCP server.

    Returns:
        Dict with server metadata
    """
    return {
        "name": MCP_SERVER_NAME,
        "version": MCP_SERVER_VERSION,
        "instructions": MCP_INSTRUCTIONS,
    }


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "mcp_server",
    "register_tool",
    "get_server_info",
    "get_db_session_for_user",
    "register_add_task",
]
