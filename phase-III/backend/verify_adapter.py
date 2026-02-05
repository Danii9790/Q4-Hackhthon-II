#!/usr/bin/env python3
"""
Verification script for MCP to OpenAI adapter.

Tests the adapter functionality without requiring pytest or external dependencies.
Run this script to verify the adapter is working correctly.
"""

import sys
import os

# Add backend to path
backend_path = '/home/xdev/Hackhthon-II/phase-III/backend'
sys.path.insert(0, backend_path)
os.chdir(backend_path)

# Import directly from file to avoid __init__.py issues
import importlib.util

# Load mcp_openai_adapter directly
spec = importlib.util.spec_from_file_location(
    "mcp_openai_adapter",
    f"{backend_path}/src/services/mcp_openai_adapter.py"
)
mcp_openai_adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mcp_openai_adapter)

# Load add_task directly
spec2 = importlib.util.spec_from_file_location(
    "add_task",
    f"{backend_path}/src/mcp_tools/add_task.py"
)
add_task_module = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(add_task_module)

# Extract what we need
MCPToolRegistry = mcp_openai_adapter.MCPToolRegistry
convert_mcp_schema_to_openai = mcp_openai_adapter.convert_mcp_schema_to_openai
convert_openai_response_to_mcp = mcp_openai_adapter.convert_openai_response_to_mcp
mcp_tool_error_handler = mcp_openai_adapter.mcp_tool_error_handler
tool_registry = mcp_openai_adapter.tool_registry
ADD_TASK_SCHEMA = add_task_module.ADD_TASK_SCHEMA
AddTaskTool = add_task_module.AddTaskTool
TaskValidationError = add_task_module.TaskValidationError


def test_schema_conversion():
    """Test MCP schema to OpenAI format conversion."""
    print("=" * 60)
    print("Test 1: MCP Schema to OpenAI Conversion")
    print("=" * 60)

    result = convert_mcp_schema_to_openai(ADD_TASK_SCHEMA)

    assert result["type"] == "function", "Expected type 'function'"
    assert result["function"]["name"] == "add_task", "Expected name 'add_task'"
    assert "parameters" in result["function"], "Expected 'parameters' key"

    params = result["function"]["parameters"]
    assert "title" in params["properties"], "Expected 'title' in properties"
    assert "user_id" in params["required"], "Expected 'user_id' in required"

    print("✓ Schema conversion successful")
    print(f"  - Tool name: {result['function']['name']}")
    print(f"  - Parameters: {len(params['properties'])} properties")
    print(f"  - Required fields: {len(params['required'])} fields")
    print()


def test_response_conversion():
    """Test OpenAI response to MCP format conversion."""
    print("=" * 60)
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
    print()


def test_tool_registry():
    """Test MCP tool registry functionality."""
    print("=" * 60)
    print("Test 3: MCP Tool Registry")
    print("=" * 60)

    # Create a new registry for testing
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
    print()


def test_error_handler():
    """Test MCP tool error handler."""
    print("=" * 60)
    print("Test 4: Error Handler")
    print("=" * 60)

    # Test TaskValidationError
    error = TaskValidationError("Invalid title")
    result = mcp_tool_error_handler(None, error)

    assert "Task validation failed" in result, "Expected validation error message"
    assert "Invalid title" in result, "Expected original error message"
    print("✓ TaskValidationError handled correctly")

    # Test ValueError
    error = ValueError("Invalid parameter")
    result = mcp_tool_error_handler(None, error)

    assert "Invalid input" in result, "Expected 'Invalid input' in response"
    print("✓ ValueError handled correctly")

    # Test generic exception
    error = RuntimeError("Something went wrong")
    result = mcp_tool_error_handler(None, error)

    assert "error occurred" in result.lower(), "Expected generic error message"
    print("✓ Generic exception handled correctly")
    print()


def test_global_registry():
    """Test global tool registry instance."""
    print("=" * 60)
    print("Test 5: Global Tool Registry")
    print("=" * 60)

    # Check that global registry has add_task registered
    tools = tool_registry.list_tools()
    assert "add_task" in tools, "Expected 'add_task' in global registry"

    retrieved = tool_registry.get_tool("add_task")
    assert retrieved is not None, "Expected to retrieve 'add_task'"
    assert "schema" in retrieved, "Expected 'schema' in retrieved tool"
    assert "instance" in retrieved, "Expected 'instance' in retrieved tool"

    print("✓ Global registry initialized with add_task")
    print(f"  - Registered tools: {', '.join(tools)}")
    print()


def test_integration():
    """Test full integration scenario."""
    print("=" * 60)
    print("Test 6: Integration Scenario")
    print("=" * 60)

    # Simulate full workflow
    registry = MCPToolRegistry()
    tool_instance = AddTaskTool()

    # Step 1: Register tool
    registry.register_tool("add_task", ADD_TASK_SCHEMA, tool_instance)
    print("✓ Step 1: Tool registered")

    # Step 2: Convert schema for OpenAI
    tool_data = registry.get_tool("add_task")
    openai_schema = convert_mcp_schema_to_openai(tool_data["schema"])
    print("✓ Step 2: Schema converted to OpenAI format")

    # Step 3: Simulate OpenAI response
    simulated_response = "Task created successfully: Buy groceries"
    mcp_response = convert_openai_response_to_mcp(simulated_response)
    print("✓ Step 3: Response converted to MCP format")

    # Verify
    assert openai_schema["function"]["name"] == "add_task"
    assert mcp_response["success"] is True
    print("✓ Integration successful - all steps verified")
    print()


def main():
    """Run all verification tests."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "MCP to OpenAI Adapter Verification" + " " * 13 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    try:
        test_schema_conversion()
        test_response_conversion()
        test_tool_registry()
        test_error_handler()
        test_global_registry()
        test_integration()

        print("╔" + "=" * 58 + "╗")
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
