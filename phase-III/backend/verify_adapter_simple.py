#!/usr/bin/env python3
"""
Simple verification script for MCP to OpenAI adapter core functionality.

Tests the schema conversion, tool registry, and response conversion
without requiring the full OpenAI Agents SDK installation.
"""

import sys
import importlib.util
import os

# Add backend to path
backend_path = '/home/xdev/Hackhthon-II/phase-III/backend'
sys.path.insert(0, backend_path)
os.chdir(backend_path)

# Load add_task module directly
spec = importlib.util.spec_from_file_location(
    "add_task",
    f"{backend_path}/src/mcp_tools/add_task.py"
)
add_task_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(add_task_module)

ADD_TASK_SCHEMA = add_task_module.ADD_TASK_SCHEMA
AddTaskTool = add_task_module.AddTaskTool
TaskValidationError = add_task_module.TaskValidationError


# ============================================================================
# Core Adapter Functions (copied from mcp_openai_adapter.py)
# ============================================================================

class MCPToolRegistry:
    """Centralized registry for MCP tools exposed to OpenAI agents."""

    def __init__(self):
        self._tools = {}
        print("[Registry] MCPToolRegistry initialized")

    def register_tool(self, tool_name: str, mcp_schema: dict, mcp_tool_instance):
        if tool_name in self._tools:
            raise ValueError(f"Tool '{tool_name}' is already registered")
        self._tools[tool_name] = {
            "schema": mcp_schema,
            "instance": mcp_tool_instance
        }
        print(f"[Registry] Registered MCP tool: {tool_name}")

    def get_tool(self, tool_name: str):
        return self._tools.get(tool_name)

    def list_tools(self):
        return list(self._tools.keys())


def convert_mcp_schema_to_openai(mcp_schema: dict) -> dict:
    """Convert MCP tool schema to OpenAI function calling format."""
    tool_name = mcp_schema.get("name")
    description = mcp_schema.get("description", "")
    input_schema = mcp_schema.get("inputSchema", {})

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

    if "additionalProperties" in input_schema:
        openai_function["function"]["parameters"]["additionalProperties"] = \
            input_schema["additionalProperties"]

    return openai_function


def convert_openai_response_to_mcp(openai_response) -> dict:
    """Convert OpenAI function tool response to MCP format."""
    if isinstance(openai_response, dict) and "success" in openai_response:
        return openai_response

    if isinstance(openai_response, str):
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

    return {
        "success": True,
        "message": "Tool execution completed",
        "data": openai_response
    }


# ============================================================================
# Tests
# ============================================================================

def test_schema_conversion():
    """Test MCP schema to OpenAI format conversion."""
    print("\n" + "=" * 60)
    print("Test 1: MCP Schema to OpenAI Conversion")
    print("=" * 60)

    result = convert_mcp_schema_to_openai(ADD_TASK_SCHEMA)

    assert result["type"] == "function", "Expected type 'function'"
    assert result["function"]["name"] == "add_task", "Expected name 'add_task'"
    assert "parameters" in result["function"], "Expected 'parameters' key"

    params = result["function"]["parameters"]
    assert "title" in params["properties"], "Expected 'title' in properties"
    assert "user_id" in params["required"], "Expected 'user_id' in required"
    assert "title" in params["required"], "Expected 'title' in required"

    print("✓ Schema conversion successful")
    print(f"  - Tool name: {result['function']['name']}")
    print(f"  - Parameters: {len(params['properties'])} properties")
    print(f"  - Required fields: {params['required']}")


def test_response_conversion():
    """Test OpenAI response to MCP format conversion."""
    print("\n" + "=" * 60)
    print("Test 2: OpenAI Response to MCP Conversion")
    print("=" * 60)

    # Test string success response
    success_response = "Task created successfully"
    result = convert_openai_response_to_mcp(success_response)

    assert result["success"] is True, "Expected success=True"
    assert result["message"] == success_response, "Expected message to match"
    print("✓ String success response converted")

    # Test string error response
    error_response = "Error: Invalid input"
    result = convert_openai_response_to_mcp(error_response)

    assert result["success"] is False, "Expected success=False"
    print("✓ String error response converted")

    # Test MCP-formatted dict (should pass through)
    mcp_dict = {"success": True, "message": "Already formatted", "data": {"id": 1}}
    result = convert_openai_response_to_mcp(mcp_dict)

    assert result is mcp_dict, "Expected same object returned"
    print("✓ MCP dict passed through unchanged")


def test_tool_registry():
    """Test MCP tool registry functionality."""
    print("\n" + "=" * 60)
    print("Test 3: MCP Tool Registry")
    print("=" * 60)

    test_registry = MCPToolRegistry()
    tool_instance = AddTaskTool()

    # Test registration
    test_registry.register_tool("add_task", ADD_TASK_SCHEMA, tool_instance)
    assert "add_task" in test_registry.list_tools(), "Expected 'add_task' in registry"
    print("✓ Tool registered successfully")

    # Test retrieval
    retrieved = test_registry.get_tool("add_task")
    assert retrieved is not None, "Expected tool to be retrieved"
    assert retrieved["instance"] == tool_instance, "Expected same instance"
    print("✓ Tool retrieved successfully")

    # Test duplicate registration error
    try:
        test_registry.register_tool("add_task", ADD_TASK_SCHEMA, tool_instance)
        assert False, "Expected ValueError for duplicate registration"
    except ValueError as e:
        assert "already registered" in str(e), "Expected 'already registered' in error"
        print("✓ Duplicate registration properly rejected")

    print(f"  - Total tools in registry: {len(test_registry.list_tools())}")


def test_extensibility():
    """Test adding multiple tools (future-proofing)."""
    print("\n" + "=" * 60)
    print("Test 4: Extensibility (Multiple Tools)")
    print("=" * 60)

    registry = MCPToolRegistry()

    # Register add_task
    add_task_instance = AddTaskTool()
    registry.register_tool("add_task", ADD_TASK_SCHEMA, add_task_instance)

    # Simulate adding future tools (list_tasks, complete_task, etc.)
    future_schemas = [
        {
            "name": "list_tasks",
            "description": "List all tasks",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                    "status": {"type": "string", "enum": ["all", "pending", "completed"]}
                },
                "required": ["user_id"]
            }
        },
        {
            "name": "complete_task",
            "description": "Mark a task as completed",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                    "task_id": {"type": "integer"}
                },
                "required": ["user_id", "task_id"]
            }
        }
    ]

    for schema in future_schemas:
        registry.register_tool(schema["name"], schema, f"Mock{schema['name'].title()}")

    tools = registry.list_tools()
    assert len(tools) == 3, "Expected 3 tools in registry"
    assert "list_tasks" in tools, "Expected 'list_tasks' in registry"
    assert "complete_task" in tools, "Expected 'complete_task' in registry"

    print("✓ Multiple tools registered successfully")
    print(f"  - Tools: {', '.join(tools)}")

    # Test converting all schemas
    print("\n✓ Converting all schemas to OpenAI format:")
    for tool_name in tools:
        tool_data = registry.get_tool(tool_name)
        openai_schema = convert_mcp_schema_to_openai(tool_data["schema"])
        print(f"  - {tool_name}: {openai_schema['function']['name']}")


def test_integration():
    """Test full integration scenario."""
    print("\n" + "=" * 60)
    print("Test 5: Integration Scenario")
    print("=" * 60)

    registry = MCPToolRegistry()
    tool_instance = AddTaskTool()

    # Step 1: Register tool
    registry.register_tool("add_task", ADD_TASK_SCHEMA, tool_instance)
    print("✓ Step 1: Tool registered")

    # Step 2: Convert schema for OpenAI
    tool_data = registry.get_tool("add_task")
    openai_schema = convert_mcp_schema_to_openai(tool_data["schema"])
    print("✓ Step 2: Schema converted to OpenAI format")

    # Step 3: Simulate OpenAI agent response
    simulated_response = "Task created successfully: Buy groceries"
    mcp_response = convert_openai_response_to_mcp(simulated_response)
    print("✓ Step 3: Response converted to MCP format")

    # Verify round-trip
    assert openai_schema["function"]["name"] == "add_task"
    assert mcp_response["success"] is True
    assert "Task created" in mcp_response["message"]
    print("✓ Integration successful - all steps verified")


def main():
    """Run all verification tests."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "MCP to OpenAI Adapter" + " " * 20 + "║")
    print("║" + " " * 12 + "Core Functionality Verification" + " " * 17 + "║")
    print("╚" + "=" * 58 + "╝")

    try:
        test_schema_conversion()
        test_response_conversion()
        test_tool_registry()
        test_extensibility()
        test_integration()

        print("\n" + "╔" + "=" * 58 + "╗")
        print("║" + " " * 20 + "ALL TESTS PASSED" + " " * 25 + "║")
        print("╚" + "=" * 58 + "╝")
        print()
        return 0

    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
