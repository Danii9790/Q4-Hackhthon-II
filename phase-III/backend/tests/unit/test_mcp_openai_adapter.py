"""
Unit tests for MCP to OpenAI adapter functionality.

Tests the schema conversion, tool registry, and response conversion
capabilities of the OpenAI adapter layer in agent.py.
"""

import pytest

from src.services.agent import (
    MCPToolRegistry,
    convert_mcp_schema_to_openai,
    convert_openai_response_to_mcp,
    mcp_tool_error_handler,
)
from src.mcp_tools.add_task import ADD_TASK_SCHEMA, AddTaskTool


# ============================================================================
# MCP Schema to OpenAI Conversion Tests
# ============================================================================

class TestConvertMCPSchemaToOpenAI:
    """Test MCP schema conversion to OpenAI function format."""

    def test_convert_add_task_schema(self):
        """Test converting ADD_TASK_SCHEMA to OpenAI format."""
        result = convert_mcp_schema_to_openai(ADD_TASK_SCHEMA)

        # Verify structure
        assert result["type"] == "function"
        assert "function" in result

        func = result["function"]
        assert func["name"] == "add_task"
        assert "Create a new task" in func["description"]

        # Verify parameters
        params = func["parameters"]
        assert params["type"] == "object"
        assert "properties" in params
        assert "user_id" in params["properties"]
        assert "title" in params["properties"]
        assert "description" in params["properties"]

        # Verify required fields
        assert "user_id" in params["required"]
        assert "title" in params["required"]
        assert "description" not in params["required"]

    def test_convert_minimal_schema(self):
        """Test converting a minimal MCP schema."""
        minimal_schema = {
            "name": "test_tool",
            "description": "A test tool",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "param1": {"type": "string"}
                }
            }
        }

        result = convert_mcp_schema_to_openai(minimal_schema)

        assert result["function"]["name"] == "test_tool"
        assert result["function"]["description"] == "A test tool"
        assert result["function"]["parameters"]["properties"]["param1"]["type"] == "string"
        assert result["function"]["parameters"]["required"] == []

    def test_convert_schema_with_required_fields(self):
        """Test converting schema with required fields."""
        schema = {
            "name": "test_tool",
            "description": "Test",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "required_param": {"type": "string"},
                    "optional_param": {"type": "string"}
                },
                "required": ["required_param"]
            }
        }

        result = convert_mcp_schema_to_openai(schema)

        required = result["function"]["parameters"]["required"]
        assert "required_param" in required
        assert "optional_param" not in required


# ============================================================================
# OpenAI Response to MCP Conversion Tests
# ============================================================================

class TestConvertOpenAIResponseToMCP:
    """Test OpenAI response conversion to MCP format."""

    def test_convert_string_success_response(self):
        """Test converting a string success response."""
        response = "Task created successfully"
        result = convert_openai_response_to_mcp(response)

        assert result["success"] is True
        assert result["message"] == "Task created successfully"
        assert result["data"]["output"] == "Task created successfully"

    def test_convert_string_error_response(self):
        """Test converting a string error response."""
        response = "Error: Invalid input"
        result = convert_openai_response_to_mcp(response)

        assert result["success"] is False
        assert result["message"] == "Error: Invalid input"
        assert result["data"] is None

    def test_convert_failed_response(self):
        """Test converting a failed string response."""
        response = "Failed to create task"
        result = convert_openai_response_to_mcp(response)

        assert result["success"] is False
        assert result["message"] == "Failed to create task"

    def test_convert_dict_with_success_field(self):
        """Test that MCP-formatted dicts pass through unchanged."""
        mcp_response = {
            "success": True,
            "message": "Already formatted",
            "data": {"id": 1}
        }

        result = convert_openai_response_to_mcp(mcp_response)

        assert result is mcp_response  # Should return same object
        assert result["success"] is True
        assert result["message"] == "Already formatted"

    def test_convert_dict_without_success_field(self):
        """Test converting a dict without success field."""
        response = {"result": "some value", "count": 5}
        result = convert_openai_response_to_mcp(response)

        assert result["success"] is True
        assert result["message"] == "Tool execution completed"
        assert result["data"]["result"] == "some value"
        assert result["data"]["count"] == 5

    def test_convert_none_response(self):
        """Test converting None response."""
        result = convert_openai_response_to_mcp(None)

        assert result["success"] is True
        assert result["message"] == "Tool execution completed"
        assert result["data"] is None


# ============================================================================
# MCP Tool Registry Tests
# ============================================================================

class TestMCPToolRegistry:
    """Test the MCP tool registry functionality."""

    def test_register_tool(self):
        """Test registering a tool."""
        registry = MCPToolRegistry()
        tool_instance = AddTaskTool()

        registry.register_tool("add_task", ADD_TASK_SCHEMA, tool_instance)

        assert "add_task" in registry.list_tools()

    def test_register_duplicate_tool_raises_error(self):
        """Test that registering duplicate tool raises ValueError."""
        registry = MCPToolRegistry()
        tool_instance = AddTaskTool()

        registry.register_tool("add_task", ADD_TASK_SCHEMA, tool_instance)

        with pytest.raises(ValueError, match="already registered"):
            registry.register_tool("add_task", ADD_TASK_SCHEMA, tool_instance)

    def test_get_tool(self):
        """Test retrieving a tool from registry."""
        registry = MCPToolRegistry()
        tool_instance = AddTaskTool()

        registry.register_tool("add_task", ADD_TASK_SCHEMA, tool_instance)
        retrieved = registry.get_tool("add_task")

        assert retrieved is not None
        assert retrieved["instance"] == tool_instance
        assert retrieved["schema"] == ADD_TASK_SCHEMA

    def test_get_nonexistent_tool_returns_none(self):
        """Test retrieving non-existent tool returns None."""
        registry = MCPToolRegistry()

        result = registry.get_tool("nonexistent")

        assert result is None

    def test_list_tools(self):
        """Test listing all registered tools."""
        registry = MCPToolRegistry()
        tool_instance = AddTaskTool()

        registry.register_tool("add_task", ADD_TASK_SCHEMA, tool_instance)

        tools = registry.list_tools()
        assert "add_task" in tools
        assert len(tools) == 1

    def test_list_multiple_tools(self):
        """Test listing multiple registered tools."""
        registry = MCPToolRegistry()

        schema1 = {"name": "tool1", "description": "Tool 1", "inputSchema": {}}
        schema2 = {"name": "tool2", "description": "Tool 2", "inputSchema": {}}

        registry.register_tool("tool1", schema1, "instance1")
        registry.register_tool("tool2", schema2, "instance2")

        tools = registry.list_tools()
        assert len(tools) == 2
        assert "tool1" in tools
        assert "tool2" in tools


# ============================================================================
# Error Handler Tests
# ============================================================================

class TestMCPToolErrorHandler:
    """Test the MCP tool error handler."""

    def test_task_validation_error(self):
        """Test handling TaskValidationError."""
        from src.mcp_tools.add_task import TaskValidationError

        error = TaskValidationError("Invalid title")
        result = mcp_tool_error_handler(None, error)

        assert "Task validation failed" in result
        assert "Invalid title" in result

    def test_value_error(self):
        """Test handling ValueError."""
        error = ValueError("Invalid parameter value")
        result = mcp_tool_error_handler(None, error)

        assert "Invalid input" in result
        assert "Invalid parameter value" in result

    def test_permission_error(self):
        """Test handling PermissionError."""
        error = PermissionError("Access denied")
        result = mcp_tool_error_handler(None, error)

        assert "Permission denied" in result

    def test_connection_error(self):
        """Test handling ConnectionError."""
        error = ConnectionError("Network unreachable")
        result = mcp_tool_error_handler(None, error)

        assert "Connection error" in result

    def test_generic_exception(self):
        """Test handling generic exception."""
        error = RuntimeError("Something went wrong")
        result = mcp_tool_error_handler(None, error)

        assert "error occurred while processing" in result
        assert "try again" in result


# ============================================================================
# Integration Tests
# ============================================================================

class TestAdapterIntegration:
    """Integration tests for the adapter layer."""

    def test_full_conversion_roundtrip(self):
        """Test full MCP schema -> OpenAI -> response conversion."""
        # Convert schema
        openai_schema = convert_mcp_schema_to_openai(ADD_TASK_SCHEMA)

        # Simulate OpenAI tool call response
        openai_response = "Task created successfully: Buy groceries"

        # Convert back to MCP format
        mcp_response = convert_openai_response_to_mcp(openai_response)

        assert mcp_response["success"] is True
        assert "Task created successfully" in mcp_response["message"]

    def test_tool_registry_with_schema_conversion(self):
        """Test using registry with schema conversion."""
        registry = MCPToolRegistry()
        tool_instance = AddTaskTool()

        # Register tool
        registry.register_tool("add_task", ADD_TASK_SCHEMA, tool_instance)

        # Retrieve and convert
        tool_data = registry.get_tool("add_task")
        openai_schema = convert_mcp_schema_to_openai(tool_data["schema"])

        assert openai_schema["function"]["name"] == "add_task"
        assert "title" in openai_schema["function"]["parameters"]["properties"]
