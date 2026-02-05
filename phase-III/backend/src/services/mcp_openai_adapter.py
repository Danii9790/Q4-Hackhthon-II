"""
OpenAI Adapter for MCP Tools.

This module provides an adapter layer that converts MCP (Model Context Protocol)
tool schemas into OpenAI Agents SDK function tools. It manages tool registration,
handles bidirectional format conversion, and provides a centralized agent interface.

The adapter follows OpenAI Agents SDK best practices:
- Uses @function_tool decorator for automatic schema generation
- Implements proper error handling with custom error functions
- Supports async tool execution
- Maintains tool registry for extensibility

Task T032 Scope:
- Convert MCP tool schemas to OpenAI function format
- Register MCP tools (add_task) with OpenAI Agents SDK
- Handle bidirectional conversion (MCP ↔ OpenAI)
- Support future tool additions (list_tasks, complete_task, etc.)
"""

import logging
from typing import Any, Dict, List, Optional

from agents import RunContextWrapper, function_tool
from pydantic import ValidationError

from src.mcp_tools.add_task import ADD_TASK_SCHEMA, AddTaskTool, TaskValidationError


# ============================================================================
# Logging Configuration
# ============================================================================

logger = logging.getLogger(__name__)


# ============================================================================
# Tool Registry for MCP Tools
# ============================================================================

class MCPToolRegistry:
    """
    Centralized registry for MCP tools exposed to OpenAI agents.

    This class maintains a mapping of MCP tool names to their implementations
    and provides a clean interface for registering and retrieving tools.

    Design Rationale:
    - Separation of concerns: MCP tools remain independent of agent framework
    - Extensibility: New tools can be added without modifying agent code
    - Testability: Registry can be mocked for unit testing
    - Type Safety: Uses type hints for clarity

    Usage:
        >>> registry = MCPToolRegistry()
        >>> registry.register_tool("add_task", ADD_TASK_SCHEMA, AddTaskTool())
        >>> tools = registry.list_tools()
    """

    def __init__(self):
        """Initialize the tool registry with empty tool map."""
        self._tools: Dict[str, Dict[str, Any]] = {}
        logger.info("MCPToolRegistry initialized")

    def register_tool(
        self,
        tool_name: str,
        mcp_schema: Dict[str, Any],
        mcp_tool_instance: Any
    ) -> None:
        """
        Register an MCP tool with its schema and implementation.

        Args:
            tool_name: Unique identifier for the tool (e.g., "add_task")
            mcp_schema: MCP tool schema dict with name, description, inputSchema
            mcp_tool_instance: Instance of the MCP tool class (e.g., AddTaskTool())

        Raises:
            ValueError: If tool_name is already registered

        Example:
            >>> registry = MCPToolRegistry()
            >>> registry.register_tool("add_task", ADD_TASK_SCHEMA, AddTaskTool())
        """
        if tool_name in self._tools:
            raise ValueError(f"Tool '{tool_name}' is already registered")

        self._tools[tool_name] = {
            "schema": mcp_schema,
            "instance": mcp_tool_instance
        }
        logger.info(f"Registered MCP tool: {tool_name}")

    def get_tool(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve tool registration by name.

        Args:
            tool_name: Name of the tool to retrieve

        Returns:
            Dict with 'schema' and 'instance' keys, or None if not found

        Example:
            >>> tool = registry.get_tool("add_task")
            >>> instance = tool["instance"]
        """
        return self._tools.get(tool_name)

    def list_tools(self) -> List[str]:
        """
        List names of all registered tools.

        Returns:
            List of tool names

        Example:
            >>> registry.list_tools()
            ['add_task', 'list_tasks', 'complete_task']
        """
        return list(self._tools.keys())


# ============================================================================
# Schema Conversion Utilities
# ============================================================================

def convert_mcp_schema_to_openai(mcp_schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert MCP tool schema to OpenAI function calling format.

    This utility transforms MCP JSON Schema format to the format expected
    by OpenAI's function calling API. It handles structural differences between
    the two protocols.

    Key transformations:
    - Extracts tool name and description
    - Converts inputSchema to parameters format
    - Handles required/optional fields
    - Preserves type information and constraints

    Args:
        mcp_schema: MCP tool schema in format:
            {
                "name": "tool_name",
                "description": "Tool description",
                "inputSchema": {
                    "type": "object",
                    "properties": {...},
                    "required": [...]
                }
            }

    Returns:
        dict: OpenAI function format:
            {
                "type": "function",
                "function": {
                    "name": "tool_name",
                    "description": "Tool description",
                    "parameters": {
                        "type": "object",
                        "properties": {...},
                        "required": [...]
                    }
                }
            }

    Example:
        >>> mcp_schema = {
        ...     "name": "add_task",
        ...     "description": "Create a new task",
        ...     "inputSchema": {
        ...         "type": "object",
        ...         "properties": {
        ...             "title": {"type": "string"}
        ...         },
        ...         "required": ["title"]
        ...     }
        ... }
        >>> openai_schema = convert_mcp_schema_to_openai(mcp_schema)
        >>> print(openai_schema["function"]["name"])
        'add_task'
    """
    logger.debug(f"Converting MCP schema to OpenAI format: {mcp_schema.get('name')}")

    # Extract core information
    tool_name = mcp_schema.get("name")
    description = mcp_schema.get("description", "")
    input_schema = mcp_schema.get("inputSchema", {})

    # Build OpenAI function format
    openai_function = {
        "type": "function",
        "function": {
            "name": tool_name,
            "description": description,
            "parameters": {
                "type": input_schema.get("type", "object"),
                "properties": input_schema.get("properties", {}),
                "required": input_schema.get("required", [])
            }
        }
    }

    # Add additional schema properties if present
    if "additionalProperties" in input_schema:
        openai_function["function"]["parameters"]["additionalProperties"] = \
            input_schema["additionalProperties"]

    if "$defs" in input_schema:
        openai_function["function"]["parameters"]["$defs"] = input_schema["$defs"]

    logger.debug(f"Converted schema successfully: {tool_name}")
    return openai_function


def convert_openai_response_to_mcp(openai_response: Any) -> Dict[str, Any]:
    """
    Convert OpenAI function tool response to MCP format.

    This utility transforms responses from OpenAI function calls into the
    standardized MCP response format expected by the backend.

    Args:
        openai_response: Response from OpenAI function tool (str, dict, or other)

    Returns:
        dict: MCP-formatted response:
            {
                "success": True/False,
                "message": "Status message",
                "data": {...}
            }

    Example:
        >>> openai_response = "Task created successfully"
        >>> mcp_response = convert_openai_response_to_mcp(openai_response)
        >>> print(mcp_response["success"])
        True
    """
    # If already a dict with success field, return as-is
    if isinstance(openai_response, dict) and "success" in openai_response:
        return openai_response

    # If string response, convert to MCP format
    if isinstance(openai_response, str):
        # Check if it looks like an error message
        if openai_response.startswith("Error:") or openai_response.startswith("Failed"):
            return {
                "success": False,
                "message": openai_response,
                "data": None
            }
        else:
            return {
                "success": True,
                "message": openai_response,
                "data": {"output": openai_response}
            }

    # For other types, wrap in generic success format
    return {
        "success": True,
        "message": "Tool execution completed",
        "data": openai_response
    }


# ============================================================================
# Error Handling Functions
# ============================================================================

def mcp_tool_error_handler(
    context: RunContextWrapper[Any],
    error: Exception
) -> str:
    """
    Custom error handler for MCP tool failures in OpenAI agents.

    Provides user-friendly error messages to the agent while logging
    detailed error information for debugging.

    Args:
        context: Run context wrapper (unused but required by SDK)
        error: The exception that occurred during tool execution

    Returns:
        str: User-friendly error message for the agent

    Example:
        >>> @function_tool(failure_error_function=mcp_tool_error_handler)
        >>> def my_tool():
        ...     pass
    """
    # Log the full error for debugging
    logger.error(f"MCP tool execution failed: {type(error).__name__}: {str(error)}")

    # Determine error type and provide context-specific message
    if isinstance(error, TaskValidationError):
        return f"Task validation failed: {error.message}. Please provide valid input."

    if isinstance(error, ValidationError):
        return f"Input validation error: Please check your parameters and try again."

    if isinstance(error, PermissionError):
        return "Permission denied. You don't have access to perform this action."

    if isinstance(error, ConnectionError):
        return "Connection error. Please check your network and try again."

    # Generic fallback for unexpected errors
    return (
        "An error occurred while processing your request. "
        "Please try again or contact support if the issue persists."
    )


# ============================================================================
# OpenAI Function Tool Wrappers
# ============================================================================

@function_tool(
    name_override="add_task",
    failure_error_function=mcp_tool_error_handler
)
async def add_task_openai(
    user_id: str,
    title: str,
    description: Optional[str] = None
) -> str:
    """
    Create a new task for the user.

    This function tool wraps the MCP add_task tool for use with OpenAI agents.
    It validates input, creates the task in the database, and returns a formatted response.

    When to use:
    - User says "Add a task to buy groceries"
    - User says "Create a reminder for my meeting"
    - User says "I need to remember to call John"
    - User says "Add todo: finish the report"

    Args:
        user_id: User's unique identifier (UUID from JWT token). This is automatically
                 injected by the backend from the authenticated user's session.
        title: Task title (required, max 500 characters). The main task identifier.
        description: Optional detailed task description (max 5000 characters) for
                     additional context about the task.

    Returns:
        str: JSON string containing the created task details:
        {
            "success": true,
            "message": "Task created successfully",
            "data": {
                "id": 1,
                "title": "Buy groceries",
                "description": "Milk, eggs, bread",
                "completed": false
            }
        }

    Example:
        User: "Add a task to buy groceries"

        Agent calls:
        add_task_openai(
            user_id="550e8400-e29b-41d4-a716-446655440000",
            title="Buy groceries"
        )

        Returns:
        '{"success": true, "message": "Task created successfully", "data": {...}}'

    Note:
        - The user_id is automatically injected by the FastAPI route handler
        - Title must be non-empty and <= 500 characters
        - Description is optional but recommended for clarity
        - New tasks are always created with completed=False
    """
    logger.info(f"OpenAI tool 'add_task' invoked with user_id={user_id}, title='{title}'")

    # Get MCP tool instance from registry
    tool = AddTaskTool()

    try:
        # Execute MCP tool
        result = await tool.execute(
            user_id=user_id,
            title=title,
            description=description
        )

        # Format response for OpenAI agent
        if result.get("success"):
            task_data = result["data"]
            logger.info(f"Task created successfully: id={task_data['id']}")
            return (
                f"Task created successfully!\n"
                f"Title: {task_data['title']}\n"
                f"ID: {task_data['id']}\n"
                f"Description: {task_data['description'] or 'No description'}"
            )
        else:
            logger.error(f"Task creation failed: {result.get('message')}")
            return f"Failed to create task: {result.get('message')}"

    except TaskValidationError as e:
        logger.warning(f"Task validation failed: {e.message}")
        return f"Validation error: {e.message}. Please check your input."

    except Exception as e:
        logger.error(f"Unexpected error in add_task: {str(e)}", exc_info=True)
        return (
            "An unexpected error occurred while creating the task. "
            "Please try again or contact support if the issue persists."
        )


# ============================================================================
# Global Tool Registry Instance
# ============================================================================

# Create a singleton registry for the application
tool_registry = MCPToolRegistry()

# Register the add_task tool
tool_registry.register_tool("add_task", ADD_TASK_SCHEMA, AddTaskTool())


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    # Core classes
    "MCPToolRegistry",

    # OpenAI function tools
    "add_task_openai",

    # Schema conversion utilities
    "convert_mcp_schema_to_openai",
    "convert_openai_response_to_mcp",

    # Error handling
    "mcp_tool_error_handler",

    # Global registry
    "tool_registry",
]
