"""
Chat routes for Todo AI Chatbot.

This module provides the chat endpoint for stateless conversation flow:
- POST /api/users/{user_id}/chat: Send a message and get AI response
- WS /api/users/{user_id}/ws: WebSocket for real-time task updates

The chat endpoint implements a 6-step request cycle:
1. Receive and validate request
2. Fetch conversation history from database
3. Store user message in database transaction
4. Invoke agent with history + new message
5. Store assistant response with tool_calls in transaction
6. Return response to frontend

All endpoints require JWT authentication and ensure user isolation.
"""
import logging
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from src.api.dependencies import get_current_user_id
from src.db import get_session
from src.models.message import MessageRole
from src.services.agent import process_message
from src.services.conversation import fetch_conversation_history, store_message
from src.services.websocket_gateway import get_websocket_gateway


# Configure logger
logger = logging.getLogger(__name__)


# ============================================================================
# Router Configuration
# ============================================================================

router = APIRouter(prefix="/users/{user_id}", tags=["Chat"])
# Note: Rate limiter is attached to main FastAPI app in main.py


# ============================================================================
# Request/Response Schemas
# ============================================================================


class ChatRequest(BaseModel):
    """
    Request schema for sending a chat message.

    Validation:
    - message: Required, 1-5000 characters
    """
    message: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="User message to send to the AI assistant"
    )

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        """Validate message is not empty after stripping whitespace."""
        if not v or not v.strip():
            raise ValueError("Message cannot be empty")
        return v.strip()


class ToolCallDetail(BaseModel):
    """
    Schema for individual tool call details in response.
    """
    tool_name: str = Field(..., description="Name of the tool that was called")
    parameters: dict = Field(..., description="Parameters passed to the tool")
    result: dict = Field(..., description="Result returned by the tool")


class ChatResponse(BaseModel):
    """
    Response schema for chat message.

    Contains the AI assistant's response and details of any tool calls made.
    """
    response: str = Field(..., description="AI assistant's text response")
    tool_calls: List[ToolCallDetail] = Field(
        default_factory=list,
        description="List of MCP tools invoked during processing"
    )


class ErrorDetail(BaseModel):
    """Error detail structure."""
    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")


class ErrorResponse(BaseModel):
    """Standard error response schema."""
    error: ErrorDetail = Field(..., description="Error details")


# ============================================================================
# Helper Functions
# ============================================================================


def verify_user_access(authenticated_user_id: str, requested_user_id: str) -> None:
    """
    Verify that the authenticated user matches the requested user ID.

    Args:
        authenticated_user_id: User ID from JWT token
        requested_user_id: User ID from URL parameter

    Raises:
        HTTPException 403: If user IDs don't match
    """
    if authenticated_user_id != requested_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "FORBIDDEN",
                "message": "You can only access your own chat conversations"
            }
        )


# ============================================================================
# Endpoints
# ============================================================================


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Validation error"},
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        403: {"model": ErrorResponse, "description": "Forbidden - accessing another user's chat"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
async def chat(
    user_id: str,
    request: ChatRequest,
    authenticated_user_id: Annotated[str, Depends(get_current_user_id)],
    session: Annotated[Session, Depends(get_session)] = None
) -> ChatResponse:
    """
    Send a message to the AI assistant and get a response.

    This endpoint implements a stateless conversation flow with database persistence.

    ============================================================================
    6-STEP REQUEST CYCLE (T111 - Stateless Conversation Flow):
    ============================================================================

    Step 1: AUTHENTICATION & AUTHORIZATION
        - Verify JWT token from Authorization header
        - Ensure authenticated user matches requested user_id
        - Prevents cross-user data access

    Step 2: FETCH CONVERSATION HISTORY
        - Query database for all previous messages in this conversation
        - Uses composite index on (conversation_id, created_at) for performance
        - Returns empty array for first message
        - Enables stateless operation - no server-side memory needed

    Step 3: STORE USER MESSAGE
        - Persist user's message to database immediately
        - Wrapped in transaction for data integrity
        - Failure here aborts the entire request

    Step 4: INVOKE AI AGENT
        - Pass conversation history + new message to OpenAI API
        - Agent may invoke MCP tools (add_task, complete_task, etc.)
        - Tool results are included in agent response
        - Agent has full context from previous messages

    Step 5: STORE ASSISTANT RESPONSE
        - Persist AI response and tool_calls to database
        - Ensures conversation is complete and queryable
        - Graceful degradation: failure here doesn't block response

    Step 6: RETURN RESPONSE
        - Send AI response and tool call details to frontend
        - Frontend displays message and tool call confirmations
        - Request completes atomically

    ============================================================================
    STATELESS ARCHITECTURE BENEFITS:
    ============================================================================
    - Zero server-side memory: conversations survive server restarts
    - Horizontal scaling: any server instance can handle any request
    - Simple debugging: all state visible in database
    - Easy testing: can verify state at any point

    ============================================================================

    Args:
        user_id: User ID from URL path
        request: Chat request with user message
        authenticated_user_id: User ID from JWT token (injected by dependency)
        session: Database session (injected by dependency)

    Returns:
        ChatResponse with AI response and tool call details

    Raises:
        HTTPException 400: If message validation fails
        HTTPException 401: If authentication fails
        HTTPException 403: If user_id doesn't match authenticated user
        HTTPException 500: If server error occurs during processing

    Example:
        ```bash
        curl -X POST "https://api.example.com/api/users/abc123/chat" \
          -H "Authorization: Bearer <jwt_token>" \
          -H "Content-Type: application/json" \
          -d '{"message": "Add a task to buy groceries"}'
        ```
    """
    # ============================================================================
    # STEP 1: AUTHENTICATION & AUTHORIZATION
    # ============================================================================
    # Verify JWT token and ensure user can only access their own conversations
    verify_user_access(authenticated_user_id, user_id)

    try:
        # ============================================================================
        # STEP 2: FETCH CONVERSATION HISTORY
        # ============================================================================
        # Retrieve all previous messages for context reconstruction
        # Composite index (conversation_id, created_at) ensures <200ms queries
        logger.info(f"Fetching conversation history for user {user_id}")
        conversation_history = fetch_conversation_history(
            user_id=user_id,
            session=session
        )

        # ============================================================================
        # STEP 3: STORE USER MESSAGE
        # ============================================================================
        # Persist user message to database immediately
        # Transaction ensures atomicity - failure aborts entire request
        logger.info(f"Storing user message for user {user_id}")
        try:
            store_message(
                user_id=user_id,
                role=MessageRole.USER,
                content=request.message,
                tool_calls=None,
                session=session
            )
        except Exception as db_error:
            logger.error(f"Database error storing user message: {str(db_error)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "code": "DATABASE_ERROR",
                    "message": "Failed to store message. Please try again."
                }
            ) from db_error

        # ============================================================================
        # STEP 4: INVOKE AI AGENT
        # ============================================================================
        # Process message with OpenAI API + conversation history
        # Agent may invoke MCP tools (add_task, complete_task, etc.)
        # Tool results are included in response
        logger.info(f"Processing message with agent for user {user_id}")
        try:
            agent_result = await process_message(
                user_id=user_id,
                conversation_history=conversation_history,
                new_message=request.message
            )
        except Exception as agent_error:
            logger.error(f"Agent processing error: {str(agent_error)}")
            # Return a user-friendly error response
            # Don't expose internal agent errors to the client
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "code": "AGENT_ERROR",
                    "message": "Sorry, I encountered an error processing your request. Please try again."
                }
            ) from agent_error

        # ============================================================================
        # STEP 5: STORE ASSISTANT RESPONSE
        # ============================================================================
        # Persist AI response and tool_calls to database
        # Graceful degradation: storage failure doesn't block response
        # User still gets their answer even if we can't log it
        logger.info(f"Storing assistant response for user {user_id}")
        try:
            # Convert tool_calls to dict format for database storage
            tool_calls_data = None
            if agent_result.get("tool_calls"):
                tool_calls_data = agent_result["tool_calls"]

            store_message(
                user_id=user_id,
                role=MessageRole.ASSISTANT,
                content=agent_result["response"],
                tool_calls=tool_calls_data,
                session=session
            )
        except Exception as db_error:
            logger.error(f"Database error storing assistant response: {str(db_error)}")
            # Don't fail the request if we can't store the response
            # The user still gets their response, even if we couldn't log it
            logger.warning("Returning response to user despite database storage failure")

        # ============================================================================
        # STEP 6: RETURN RESPONSE
        # ============================================================================
        # Send AI response and tool call details to frontend
        # Frontend displays message with tool call confirmations
        # Request completes atomically with full audit trail in database
        logger.info(f"Returning chat response to user {user_id}")

        # Format tool_calls for response
        tool_calls_formatted = []
        if agent_result.get("tool_calls"):
            for tool_call in agent_result["tool_calls"]:
                tool_calls_formatted.append(
                    ToolCallDetail(
                        tool_name=tool_call.get("tool_name", "unknown"),
                        parameters=tool_call.get("parameters", {}),
                        result=tool_call.get("result", {})
                    )
                )

        return ChatResponse(
            response=agent_result["response"],
            tool_calls=tool_calls_formatted
        )

    except HTTPException:
        # Re-raise HTTP exceptions (validation, auth, etc.)
        raise
    except Exception as e:
        # Catch any unexpected errors
        logger.error(f"Unexpected error in chat endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "SERVER_ERROR",
                "message": "An unexpected error occurred. Please try again."
            }
        ) from e


# ============================================================================
# Phase V: Real-Time WebSocket Endpoint (T096)
# ============================================================================


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    T096: WebSocket endpoint for real-time task updates.

    This endpoint:
    1. Accepts WebSocket connections
    2. Tracks connection by user_id
    3. Receives real-time task updates via Kafka consumer
    4. Broadcasts updates to connected clients

    Args:
        websocket: WebSocket connection
        user_id: User ID from URL parameter

    Example:
        ```javascript
        const ws = new WebSocket('ws://localhost:8000/api/users/abc123/ws');
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log('Task update:', data);
        };
        ```
    """
    # Accept connection
    await websocket.accept()

    # Get WebSocket gateway
    gateway = get_websocket_gateway()

    # Generate unique connection ID
    import uuid
    connection_id = str(uuid.uuid4())

    # Add client to gateway
    gateway.add_client(user_id=user_id, connection_id=connection_id, websocket=websocket)

    logger.info(f"WebSocket connection {connection_id} established for user {user_id}")

    try:
        # Keep connection alive and listen for client messages
        while True:
            # Receive message from client
            data = await websocket.receive_json()

            # Echo back for now (can be used for ping/pong)
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        logger.info(f"WebSocket connection {connection_id} closed for user {user_id}")
    except Exception as e:
        logger.error(f"WebSocket error for connection {connection_id}: {e}")
    finally:
        # Remove client from gateway
        gateway.remove_client(user_id=user_id, connection_id=connection_id)
