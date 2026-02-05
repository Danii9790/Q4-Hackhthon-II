"""
Chat API helper functions and endpoint for Todo AI Chatbot.

Provides conversation and message retrieval logic for the chat endpoint
along with the main POST /api/{user_id}/chat endpoint.
All functions follow async patterns and enforce user data isolation.
"""

from logging import getLogger
from typing import Any, Dict, List, Optional
from uuid import UUID
import hashlib

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlmodel import select as sqlmodel_select

from datetime import datetime

from src.api.deps import get_current_user_id
from src.api.security import limiter, sanitize_message, validate_message_length
from src.db.session import get_session
from src.models import Conversation, Message
from src.schemas import ChatRequest, ChatResponse as SchemaChatResponse, ToolCallDetail
from src.services.agent import execute_agent
from src.services.conversation import (
    fetch_conversation_history,
    format_messages_for_agent,
    truncate_history_to_max,
)


# Configure logging
logger = getLogger(__name__)


# ============================================================================
# FastAPI Router
# ============================================================================

router = APIRouter()


# ============================================================================
# Type alias for backward compatibility
# ============================================================================

# Use the standardized schema from schemas.py
ChatRequest = ChatRequest
ChatResponse = SchemaChatResponse


# ============================================================================
# Conversation Management
# ============================================================================

async def get_or_create_conversation(
    session: AsyncSession,
    user_id: UUID,
    conversation_id: Optional[UUID] = None,
) -> Conversation:
    """
    Get existing conversation or create a new one for the user.

    This function implements the core conversation retrieval/creation logic:
    - If conversation_id provided: fetch and validate ownership
    - If conversation_id is None: create new conversation for user
    - Enforces user data isolation to prevent cross-user access

    Args:
        session: Async database session
        user_id: Authenticated user's UUID (from JWT token)
        conversation_id: Optional conversation UUID to retrieve

    Returns:
        Conversation object (existing or newly created)

    Raises:
        HTTPException: 404 if conversation_id not found or doesn't belong to user

    Example:
        # Continue existing conversation
        conv = await get_or_create_conversation(session, user_id, conversation_id)
        # Start new conversation
        conv = await get_or_create_conversation(session, user_id)
    """
    if conversation_id is not None:
        # Fetch existing conversation and validate ownership
        statement = sqlmodel_select(Conversation).where(
            Conversation.id == conversation_id
        )
        result = await session.execute(statement)
        conversation = result.scalar_one_or_none()

        # Validate conversation exists and belongs to user
        if conversation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Conversation with ID {conversation_id} not found"
            )

        if conversation.user_id != user_id:
            # Security: Don't reveal conversation existence to other users
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )

        return conversation

    else:
        # Create new conversation for user
        new_conversation = Conversation(user_id=user_id)
        session.add(new_conversation)
        await session.flush()  # Get the generated ID without committing

        return new_conversation




# ============================================================================
# Message Persistence Helper Functions
# ============================================================================

async def save_user_message(
    session: AsyncSession,
    conversation_id: UUID,
    user_id: UUID,
    content: str
) -> Message:
    """
    Save a user message to the database.

    Creates a new Message with role="user", persists it to the database,
    and returns the created message with generated id and timestamps.

    Args:
        session: Async database session
        conversation_id: UUID of the conversation
        user_id: UUID of the user (for data isolation)
        content: Message text content

    Returns:
        Message: Created message object with id and created_at populated

    Raises:
        HTTPException: 500 if database operation fails
        ValueError: If content is empty or invalid

    Example:
        >>> message = await save_user_message(session, conv_id, user_id, "Hello")
        >>> print(message.id, message.created_at)
        uuid.UUID('...'), datetime.datetime(...)
    """
    # Validate input
    if not content or not content.strip():
        raise ValueError("Message content cannot be empty")

    # Create new message with role="user"
    message = Message(
        conversation_id=conversation_id,
        user_id=user_id,
        role="user",
        content=content.strip()
    )

    try:
        # Add to session and commit
        session.add(message)
        await session.commit()
        # Refresh to get generated fields (id, created_at)
        await session.refresh(message)

        logger.info(
            f"Saved user message: id={message.id}, "
            f"conversation_id={conversation_id}, user_id={user_id}"
        )

        return message

    except SQLAlchemyError as e:
        # Rollback on error
        await session.rollback()
        logger.error(f"Database error saving user message: {str(e)}")
        raise RuntimeError(f"Failed to save user message: {str(e)}") from e


async def save_assistant_message(
    session: AsyncSession,
    conversation_id: UUID,
    user_id: UUID,
    content: str
) -> Message:
    """
    Save an assistant message to the database.

    Creates a new Message with role="assistant", persists it to the database,
    and returns the created message with generated id and timestamps.

    Args:
        session: Async database session
        conversation_id: UUID of the conversation
        user_id: UUID of the user (for data isolation)
        content: Message text content

    Returns:
        Message: Created message object with id and created_at populated

    Raises:
        HTTPException: 500 if database operation fails
        ValueError: If content is empty or invalid

    Example:
        >>> message = await save_assistant_message(session, conv_id, user_id, "Hi!")
        >>> print(message.id, message.created_at)
        uuid.UUID('...'), datetime.datetime(...)
    """
    # Validate input
    if not content or not content.strip():
        raise ValueError("Message content cannot be empty")

    # Create new message with role="assistant"
    message = Message(
        conversation_id=conversation_id,
        user_id=user_id,
        role="assistant",
        content=content.strip()
    )

    try:
        # Add to session and commit
        session.add(message)
        await session.commit()
        # Refresh to get generated fields (id, created_at)
        await session.refresh(message)

        logger.info(
            f"Saved assistant message: id={message.id}, "
            f"conversation_id={conversation_id}, user_id={user_id}"
        )

        return message

    except SQLAlchemyError as e:
        # Rollback on error
        await session.rollback()
        logger.error(f"Database error saving assistant message: {str(e)}")
        raise RuntimeError(f"Failed to save assistant message: {str(e)}") from e


# ============================================================================
# Performance: T082 - Caching Helpers
# ============================================================================

def generate_etag(
    conversation_id: UUID,
    message_count: int,
    last_message_time: Optional[datetime] = None
) -> str:
    """
    Generate ETag for conditional HTTP requests.

    Performance: T082 - ETag support for efficient caching.
    Creates a weak ETag based on conversation state to support
    conditional requests (If-None-Match) without transmitting
    full response bodies.

    Args:
        conversation_id: UUID of conversation
        message_count: Number of messages in conversation
        last_message_time: Timestamp of most recent message

    Returns:
        ETag string for HTTP caching headers

    Example:
        >>> etag = generate_etag(conv_id, 42, datetime.utcnow())
        >>> f'W/"{etag}"'  # Weak ETag for use in response headers
    """
    # Create hash from conversation state
    state_str = f"{conversation_id}:{message_count}:{last_message_time.isoformat() if last_message_time else ''}"
    hash_obj = hashlib.sha256(state_str.encode())
    return hash_obj.hexdigest()


# ============================================================================
# Message Formatting for OpenAI Agents SDK
# ============================================================================

    return formatted



    # Reverse to restore chronological order and slice messages
    truncated_indices.reverse()
    return [messages[i] for i in truncated_indices]


# ============================================================================
# Chat Endpoint
# ============================================================================

@router.post(
    "/api/{user_id}/chat",
    response_model=SchemaChatResponse,
    status_code=status.HTTP_200_OK,
    tags=["Chat"]
)
@limiter.limit("10/minute")  # T083: Rate limiting - 10 requests per minute per user
async def chat_endpoint(
    request_obj: Request,  # T083: Request object for rate limiting
    user_id: UUID,
    request: ChatRequest,
    response: Response,
    token_user_id: UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_session),
):
    """
    POST /api/{user_id}/chat - Send a message and receive AI response (T035).

    This endpoint handles incoming chat messages by:
    1. Validating the JWT token and extracting user_id
    2. Ensuring the path user_id matches the token user_id
    3. Getting or creating a conversation
    4. Saving the user message to the database
    5. Fetching conversation history
    6. Executing the AI agent with conversation context
    7. Saving the assistant's response to the database
    8. Returning formatted response with tool call details

    The endpoint integrates with OpenAI Agents SDK to provide AI-powered
    task management through natural language.

    Args:
        user_id: UUID from path parameter (must match JWT token)
        request: ChatRequest with conversation_id (optional) and message (required)
        token_user_id: UUID extracted from JWT token via dependency
        session: Async database session from dependency

    Returns:
        SchemaChatResponse with conversation_id, assistant_message, tool_calls, and timestamp

    Raises:
        HTTPException 403: If path user_id doesn't match token user_id
        HTTPException 404: If conversation_id not found or doesn't belong to user
        HTTPException 422: If message validation fails
        HTTPException 500: If agent execution or database operations fail

    Example Request:
        POST /api/123e4567-e89b-12d3-a456-426614174000/chat
        {
            "conversation_id": null,
            "message": "Add a task to buy groceries"
        }

    Example Response:
        {
            "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
            "assistant_message": "I've added that task for you!",
            "tool_calls": [
                {
                    "tool_name": "add_task",
                    "arguments": {"title": "Buy groceries"},
                    "result": {"success": true, "data": {"id": 1}}
                }
            ],
            "timestamp": "2025-01-19T12:00:00Z"
        }
    """
    # Security: Verify path user_id matches token user_id
    # This prevents users from accessing other users' conversations
    if user_id != token_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User ID in path does not match authenticated user"
        )

    # T084: Message length validation and sanitization
    # This prevents injection attacks and ensures messages are within size limits
    try:
        # Validate message length
        validate_message_length(request.message)

        # Sanitize message content (remove null bytes, control chars, etc.)
        sanitized_message = sanitize_message(request.message)

        # Update request with sanitized message
        request.message = sanitized_message

        logger.debug(
            f"Message sanitized: original_length={len(request.message)}, "
            f"sanitized_length={len(sanitized_message)}"
        )

    except ValueError as e:
        # Message validation failed
        logger.warning(f"Message validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # Step 1: Get or create conversation for the user
    conversation = await get_or_create_conversation(
        session=session,
        user_id=user_id,
        conversation_id=request.conversation_id
    )

    # Step 2: Save user message to database
    saved_message = await save_user_message(
        session=session,
        conversation_id=conversation.id,
        user_id=user_id,
        content=request.message
    )

    logger.info(
        f"Processing chat request: conversation_id={conversation.id}, "
        f"user_id={user_id}, message_length={len(saved_message.content)}"
    )

    # ========================================================================
    # T036: Comprehensive Error Handling
    # ========================================================================

    try:
        # Step 3: Fetch conversation history for agent context
        conversation_history = await fetch_conversation_history(
            session=session,
            conversation_id=conversation.id,
            limit=50  # Last 50 messages for context
        )

        logger.debug(
            f"Retrieved {len(conversation_history)} messages from conversation history"
        )

    except HTTPException:
        # Re-raise HTTP exceptions from fetch_conversation_history
        raise
    except Exception as e:
        # Database error fetching history
        logger.error(f"Database error fetching conversation history: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="I'm having trouble loading your conversation history. Please try again."
        )

    # ========================================================================
    # T036: Agent Execution Error Handling
    # ========================================================================
    try:
        # Step 4: Execute AI agent with conversation context and new message
        agent_result = await execute_agent(
            user_id=user_id,
            conversation_history=conversation_history,
            message=request.message
        )

        # Check if agent execution failed
        if not agent_result.get("success"):
            error_code = agent_result.get("error", "UNKNOWN_ERROR")
            assistant_message = agent_result.get("assistant_message", "")

            logger.error(f"Agent execution failed: error_code={error_code}")

            # Map agent error codes to HTTP status codes
            if error_code == "AGENT_TIMEOUT":
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=assistant_message or
                        "I'm taking too long to respond. Please try with a shorter request."
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=assistant_message or
                        "I'm having trouble processing your request. Please try again."
                )

        # Step 5: Extract agent response and tool calls
        assistant_message = agent_result.get("assistant_message", "")
        tool_calls_raw = agent_result.get("tool_calls", [])

        logger.info(
            f"Agent execution successful: response_length={len(assistant_message)}, "
            f"tool_calls_count={len(tool_calls_raw)}"
        )

    except HTTPException:
        # Re-raise HTTP exceptions from agent execution
        raise
    except ValueError as e:
        # Agent validation errors (e.g., empty message)
        logger.warning(f"Validation error in agent execution: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except RuntimeError as e:
        # Runtime error from execute_agent (e.g., timeout)
        logger.error(f"Runtime error in agent execution: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="I'm taking too long to respond. Please try again."
        )
    except Exception as e:
        # OpenAI API error or other unexpected error
        logger.error(
            f"Unexpected error in agent execution: {str(e)}",
            exc_info=True
        )

        # Check for OpenAI-specific errors (T036 requirement)
        error_str = str(e).lower()
        if "rate limit" in error_str or "429" in error_str:
            logger.warning("OpenAI rate limit detected")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="I'm receiving too many requests right now. Please try again in a moment."
            )
        elif "timeout" in error_str or "timed out" in error_str:
            logger.warning("Agent timeout detected")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="I'm taking too long to respond. Please try again."
            )
        elif "authentication" in error_str or "api key" in error_str or "unauthorized" in error_str:
            # Server configuration error - don't expose to users
            logger.critical("OpenAI API authentication error - check API key configuration")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="I'm having trouble connecting right now. Please try again."
            )
        else:
            # Generic error - user-friendly message (never expose internal errors)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="I'm having trouble connecting right now. Please try again."
            )

    # ========================================================================
    # T036: Assistant Message Persistence Error Handling
    # ========================================================================
    try:
        # Step 6: Save assistant message to database
        await save_assistant_message(
            session=session,
            conversation_id=conversation.id,
            user_id=user_id,
            content=assistant_message
        )
        logger.debug("Assistant message saved successfully")

    except ValueError as e:
        # Validation error (empty content)
        logger.warning(f"Validation error saving assistant message: {str(e)}")
        # Continue anyway - user message was already saved
    except RuntimeError as e:
        # Database error from save_assistant_message
        logger.error(f"Database error saving assistant message: {str(e)}", exc_info=True)
        # Continue anyway - user message was already saved
    except Exception as e:
        # Unexpected error
        logger.error(f"Unexpected error saving assistant message: {str(e)}", exc_info=True)
        # Continue anyway - user message was already saved

    # ========================================================================
    # T036: Tool Execution Error Handling
    # ========================================================================
    try:
        # Step 7: Format tool calls according to T035 schema
        formatted_tool_calls = []
        tool_errors = []

        for tool_call in tool_calls_raw:
            tool_name = tool_call.get("tool_name", "unknown")
            arguments = tool_call.get("arguments", {})
            result = tool_call.get("result")

            # Check for tool execution errors (T036 requirement)
            if result and ("error" in result.lower() or "failed" in result.lower()):
                tool_errors.append({
                    "tool_name": tool_name,
                    "error": result
                })
                logger.warning(f"Tool execution error: {tool_name} - {result[:100]}")

            formatted_tool_calls.append(ToolCallDetail(
                tool_name=tool_name,
                arguments=arguments,
                result=result
            ))

        # Log tool errors for debugging (but don't expose internal details)
        if tool_errors:
            logger.warning(f"Tool execution errors detected: {[e['tool_name'] for e in tool_errors]}")

    except Exception as e:
        # Error formatting tool calls
        logger.error(f"Error formatting tool calls: {str(e)}", exc_info=True)
        formatted_tool_calls = []

    # ========================================================================
    # T036: Response Building
    # ========================================================================
    try:
        # Step 8: Build and return standardized response (T035)
        chat_response = SchemaChatResponse(
            conversation_id=conversation.id,
            assistant_message=assistant_message,
            tool_calls=formatted_tool_calls,
            timestamp=datetime.utcnow()
        )

        # Performance: T082 - Add caching headers
        # Chat responses are dynamic and user-specific, so we use no-cache
        # but provide ETag for future conditional request support
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"  # HTTP/1.0 compatibility
        response.headers["Expires"] = "0"  # Prevent caching

        # Generate weak ETag based on conversation state
        # This enables potential conditional requests in the future
        # (not currently used, but infrastructure in place)
        etag_value = generate_etag(
            conversation_id=conversation.id,
            message_count=len(conversation_history) + 2,  # +2 for user and assistant messages
            last_message_time=chat_response.timestamp
        )
        response.headers["ETag"] = f'W/"{etag_value}"'

        logger.info(
            f"Chat endpoint successful: conversation_id={conversation.id}, "
            f"tool_calls_count={len(formatted_tool_calls)}, "
            f"response_length={len(assistant_message)}, "
            f"etag={etag_value[:16]}..."  # Log first 16 chars of ETag
        )

        return chat_response

    except Exception as e:
        # Error building response (shouldn't happen, but handle gracefully)
        logger.error(f"Error building response: {str(e)}", exc_info=True)
        # Return minimal response
        return SchemaChatResponse(
            conversation_id=conversation.id,
            assistant_message=assistant_message,
            tool_calls=[],
            timestamp=datetime.utcnow()
        )


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "router",
    "ChatRequest",
    "ChatResponse",
    "chat_endpoint",
    "get_or_create_conversation",
    "fetch_conversation_history",
    "save_user_message",
    "save_assistant_message",
    "format_messages_for_agent",
    "truncate_history_to_max",
    "generate_etag",
]
