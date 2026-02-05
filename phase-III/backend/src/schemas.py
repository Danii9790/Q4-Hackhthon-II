"""
Pydantic schemas for request/response models.

Defines all Pydantic models for API request validation and response formatting.
Ensures type safety and provides automatic JSON serialization.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================================
# Chat Response Schemas (T035)
# ============================================================================

class ToolCallDetail(BaseModel):
    """
    Represents a single tool call made by the AI agent.

    Captures the tool name, arguments passed, and the result returned.
    Used in chat responses to provide transparency into agent actions.

    Attributes:
        tool_name: Name of the MCP tool that was called (e.g., "add_task", "list_tasks")
        arguments: Dictionary of arguments passed to the tool
        result: The result returned by the tool execution

    Example:
        >>> tool_call = ToolCallDetail(
        ...     tool_name="add_task",
        ...     arguments={"title": "Buy groceries", "description": "Milk, eggs, bread"},
        ...     result={"success": True, "data": {"id": 1, "title": "Buy groceries"}}
        ... )
    """
    tool_name: str = Field(
        ...,
        description="Name of the MCP tool that was invoked",
        examples=["add_task", "list_tasks", "complete_task", "update_task", "delete_task"]
    )
    arguments: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arguments passed to the tool"
    )
    result: Optional[Any] = Field(
        default=None,
        description="Result returned by the tool execution"
    )


class ChatResponse(BaseModel):
    """
    Standardized response model for the chat endpoint.

    This schema defines the structure of responses returned by the /api/chat endpoint.
    It includes the conversation ID, assistant's message, any tool calls made,
    and a timestamp for client-side synchronization.

    The response is JSON-serializable and follows RESTful conventions.

    Attributes:
        conversation_id: UUID of the conversation (new or existing)
        assistant_message: The AI agent's text response to the user
        tool_calls: List of tool calls executed during agent processing
        timestamp: ISO 8601 timestamp of when the response was generated

    Example:
        >>> response = ChatResponse(
        ...     conversation_id="123e4567-e89b-12d3-a456-426614174000",
        ...     assistant_message="I've added that task for you!",
        ...     tool_calls=[
        ...         {
        ...             "tool_name": "add_task",
        ...             "arguments": {"title": "Buy groceries"},
        ...             "result": {"success": True, "data": {"id": 1}}
        ...         }
        ...     ],
        ...     timestamp=datetime.now()
        ... )
    """
    conversation_id: UUID = Field(
        ...,
        description="UUID of the conversation (new or existing)"
    )
    assistant_message: str = Field(
        ...,
        description="The AI agent's text response to the user",
        min_length=1
    )
    tool_calls: List[ToolCallDetail] = Field(
        default_factory=list,
        description="List of tool calls executed during agent processing"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="ISO 8601 timestamp of response generation"
    )

    class Config:
        """
        Pydantic model configuration.

        Enables JSON encoding of UUID and datetime objects.
        """
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


# ============================================================================
# Request Schemas
# ============================================================================

class ChatRequest(BaseModel):
    """
    Request model for the chat endpoint.

    Validates incoming chat requests from the frontend.

    Attributes:
        message: User's message text (required)
        conversation_id: Optional UUID to continue existing conversation

    Example:
        >>> request = ChatRequest(
        ...     message="Add a task to buy groceries",
        ...     conversation_id=None  # Start new conversation
        ... )
    """
    message: str = Field(
        ...,
        description="User's message to the AI assistant",
        min_length=1,
        max_length=10000
    )
    conversation_id: Optional[UUID] = Field(
        default=None,
        description="Optional conversation UUID to continue existing conversation"
    )


# ============================================================================
# Error Response Schemas
# ============================================================================

class ErrorResponse(BaseModel):
    """
    Standardized error response model.

    Used for consistent error reporting across all API endpoints.

    Attributes:
        error: Brief error title
        message: Detailed error message
        code: Machine-readable error code
        details: Optional additional error details
    """
    error: str = Field(
        ...,
        description="Brief error title",
        examples=["Bad Request", "Unauthorized", "Not Found"]
    )
    message: str = Field(
        ...,
        description="Detailed error message"
    )
    code: str = Field(
        ...,
        description="Machine-readable error code",
        examples=["BAD_REQUEST", "UNAUTHORIZED", "NOT_FOUND"]
    )
    details: Optional[Any] = Field(
        default=None,
        description="Additional error details (e.g., validation errors)"
    )


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    # Chat schemas
    "ChatRequest",
    "ChatResponse",
    "ToolCallDetail",
    # Error schema
    "ErrorResponse",
]
