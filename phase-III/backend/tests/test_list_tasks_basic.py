"""
Basic verification test for list_tasks MCP tool.

This script verifies the tool structure and basic functionality without
requiring a full database setup.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_tool_initialization():
    """Test that the tool can be initialized."""
    print("Testing tool initialization...")
    from src.mcp_tools.list_tasks import ListTasksTool

    tool = ListTasksTool()
    assert tool.tool_name == "list_tasks"
    assert tool.tool_description is not None
    print("✓ Tool initialized successfully")


def test_status_validation():
    """Test status parameter validation."""
    print("\nTesting status validation...")
    from src.mcp_tools.list_tasks import ListTasksTool

    tool = ListTasksTool()

    # Test valid statuses
    assert tool.validate_status("all") == "all"
    assert tool.validate_status("pending") == "pending"
    assert tool.validate_status("completed") == "completed"

    # Test case insensitivity
    assert tool.validate_status("ALL") == "all"
    assert tool.validate_status("PENDING") == "pending"
    assert tool.validate_status("COMPLETED") == "completed"

    # Test default (None)
    assert tool.validate_status(None) == "all"

    # Test empty string
    assert tool.validate_status("  ") == "all"

    print("✓ Status validation works correctly")


def test_status_validation_errors():
    """Test that invalid status raises appropriate error."""
    print("\nTesting status validation errors...")
    from src.mcp_tools.list_tasks import ListTasksTool, TaskFilterValidationError

    tool = ListTasksTool()

    # Test invalid status
    try:
        tool.validate_status("invalid")
        assert False, "Should have raised TaskFilterValidationError"
    except TaskFilterValidationError as e:
        assert "Invalid status" in str(e.message)
        print(f"✓ Invalid status correctly rejected: {e.message}")

    # Test non-string input
    try:
        tool.validate_status(123)
        assert False, "Should have raised TaskFilterValidationError"
    except TaskFilterValidationError as e:
        assert "must be a string" in str(e.message)
        print(f"✓ Non-string status correctly rejected: {e.message}")


def test_mcp_schema():
    """Test that MCP schema is properly defined."""
    print("\nTesting MCP schema...")
    from src.mcp_tools.list_tasks import LIST_TASKS_SCHEMA

    assert LIST_TASKS_SCHEMA["name"] == "list_tasks"
    assert "description" in LIST_TASKS_SCHEMA
    assert "inputSchema" in LIST_TASKS_SCHEMA
    assert LIST_TASKS_SCHEMA["inputSchema"]["type"] == "object"
    assert "user_id" in LIST_TASKS_SCHEMA["inputSchema"]["properties"]
    assert "status" in LIST_TASKS_SCHEMA["inputSchema"]["properties"]
    assert LIST_TASKS_SCHEMA["inputSchema"]["properties"]["status"]["enum"] == ["all", "pending", "completed"]
    print("✓ MCP schema is properly defined")


def test_tool_structure():
    """Test that tool has required methods."""
    print("\nTesting tool structure...")
    from src.mcp_tools.list_tasks import ListTasksTool

    tool = ListTasksTool()

    # Check that tool inherits from BaseMCPTool
    assert hasattr(tool, 'validate_user_id')
    assert hasattr(tool, 'get_db_session')
    assert hasattr(tool, 'format_success_response')
    assert hasattr(tool, 'format_error_response')

    # Check that tool has execute method
    assert hasattr(tool, 'execute')
    assert callable(tool.execute)

    # Check for new methods
    assert hasattr(tool, 'build_task_query')
    assert hasattr(tool, 'format_task_dict')

    print("✓ Tool structure is correct")


def test_query_building():
    """Test that query building works correctly."""
    print("\nTesting query building...")
    from src.mcp_tools.list_tasks import ListTasksTool
    from uuid import uuid4

    tool = ListTasksTool()
    user_id = uuid4()

    # Test "all" query
    query_all = tool.build_task_query(user_id, "all")
    assert query_all is not None
    print("✓ 'all' query built successfully")

    # Test "pending" query
    query_pending = tool.build_task_query(user_id, "pending")
    assert query_pending is not None
    print("✓ 'pending' query built successfully")

    # Test "completed" query
    query_completed = tool.build_task_query(user_id, "completed")
    assert query_completed is not None
    print("✓ 'completed' query built successfully")


def main():
    """Run all verification tests."""
    print("=" * 60)
    print("List Tasks MCP Tool - Basic Verification")
    print("=" * 60)

    try:
        test_tool_initialization()
        test_status_validation()
        test_status_validation_errors()
        test_mcp_schema()
        test_tool_structure()
        test_query_building()

        print("\n" + "=" * 60)
        print("All verification tests passed! ✓")
        print("=" * 60)
        print("\nThe list_tasks tool is ready for:")
        print("  - MCP server registration")
        print("  - Database integration (with proper session)")
        print("  - AI agent invocation")
        return 0

    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
