"""
Security configuration and middleware for Todo AI Chatbot API.

Provides rate limiting, input sanitization, and security utilities.
"""

import os
import re
from typing import Optional, List
from uuid import UUID

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException, status


# ============================================================================
# Environment Variables
# ============================================================================

def get_rate_limit() -> int:
    """
    Get rate limit per minute from environment variable.

    Defaults to 10 requests per minute if not configured.

    Returns:
        int: Maximum number of requests allowed per minute per user
    """
    return int(os.getenv("RATE_LIMIT_PER_MINUTE", "10"))


def get_max_message_length() -> int:
    """
    Get maximum message length from environment variable.

    Defaults to 10,000 characters if not configured.

    Returns:
        int: Maximum number of characters allowed per message
    """
    return int(os.getenv("MAX_MESSAGE_LENGTH", "10000"))


def get_frontend_urls() -> List[str]:
    """
    Get allowed frontend URLs from environment variable.

    Supports comma-separated list of URLs for multiple environments.

    Returns:
        List of allowed frontend origins for CORS

    Example:
        FRONTEND_URL="http://localhost:3000,https://example.com"
        Returns: ["http://localhost:3000", "https://example.com"]
    """
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")

    # Split by comma and strip whitespace
    urls = [url.strip() for url in frontend_url.split(",") if url.strip()]

    # Always include localhost for development
    if "http://localhost:3000" not in urls:
        urls.append("http://localhost:3000")

    return urls


def allow_credentials() -> bool:
    """
    Determine if CORS should allow credentials.

    In production, credentials should be disabled for security.
    Enable only for local development.

    Returns:
        bool: True if credentials allowed, False otherwise
    """
    return os.getenv("ENVIRONMENT", "development") == "development"


# ============================================================================
# Rate Limiting
# ============================================================================

def get_user_id_from_request(request: Request) -> str:
    """
    Extract user identifier for rate limiting.

    Uses a combination of IP address and user_id (if available in path)
    to create a unique rate limit key per user.

    Args:
        request: FastAPI Request object

    Returns:
        str: Unique identifier for rate limiting

    Example:
        # Request with user_id in path: /api/123e4567-e89b-12d3-a456-426614174000/chat
        Returns: "127.0.0.1:123e4567-e89b-12d3-a456-426614174000"

        # Request without user_id
        Returns: "127.0.0.1"
    """
    # Get IP address
    ip = get_remote_address(request)

    # Try to extract user_id from path
    path_parts = request.url.path.split("/")
    if len(path_parts) >= 3:
        # Check if the second-to-last part is a UUID (user_id in /api/{user_id}/chat)
        potential_uuid = path_parts[2]
        try:
            # Validate it's a valid UUID
            UUID(potential_uuid)
            return f"{ip}:{potential_uuid}"
        except (ValueError, AttributeError):
            pass

    # Fallback to IP-based rate limiting
    return ip


# Initialize rate limiter
limiter = Limiter(
    key_func=get_user_id_from_request,
    default_limits=[get_rate_limit()],
    storage_uri="memory://",  # In-memory storage (use Redis for production)
    headers_enabled=True,  # Enable X-RateLimit-* headers
)


# ============================================================================
# Input Sanitization
# ============================================================================

def sanitize_message(message: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize user message input to prevent injection attacks.

    Removes:
    - Null bytes
    - Control characters (except newlines and tabs)
    - Excessive whitespace
    - Truncates to maximum length

    Args:
        message: Raw user message input
        max_length: Maximum allowed length (defaults to env variable)

    Returns:
        str: Sanitized message safe for processing

    Raises:
        ValueError: If message is empty after sanitization or exceeds max length

    Examples:
        >>> sanitize_message("Hello\\x00World")
        'HelloWorld'

        >>> sanitize_message("Hello\\n\\tWorld")
        'Hello\\n\\tWorld'

        >>> sanitize_message("  Hello   World  ")
        'Hello World'
    """
    if max_length is None:
        max_length = get_max_message_length()

    # Check length before sanitization
    if len(message) > max_length:
        raise ValueError(
            f"Message exceeds maximum length of {max_length} characters. "
            f"Your message is {len(message)} characters long."
        )

    # Remove null bytes (potential injection vector)
    message = message.replace("\x00", "")

    # Remove control characters except newline, tab, and carriage return
    # This preserves message formatting while removing dangerous characters
    message = re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]", "", message)

    # Normalize whitespace (collapse multiple spaces into one)
    message = re.sub(r" {2,}", " ", message)

    # Strip leading/trailing whitespace
    message = message.strip()

    # Validate message is not empty after sanitization
    if not message:
        raise ValueError("Message cannot be empty")

    # Final length check
    if len(message) > max_length:
        raise ValueError(
            f"Message exceeds maximum length of {max_length} characters. "
            f"Your message is {len(message)} characters long."
        )

    return message


# ============================================================================
# Custom Exception Handlers
# ============================================================================

async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """
    Handle rate limit exceeded errors.

    Returns a 429 status code with clear error message and retry information.

    Args:
        request: FastAPI Request object
        exc: RateLimitExceeded exception

    Returns:
        JSON response with 429 status code
    """
    # Calculate retry time (1 minute from now)
    import time
    retry_after = 60  # seconds

    return HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail={
            "error": "Too Many Requests",
            "message": f"Rate limit exceeded. Please try again in {retry_after} seconds.",
            "code": "RATE_LIMIT_EXCEEDED",
            "retry_after": retry_after,
        },
        headers={"Retry-After": str(retry_after)}
    )


# ============================================================================
# Validation Helpers
# ============================================================================

def validate_message_length(message: str) -> None:
    """
    Validate message length against maximum allowed.

    Args:
        message: Message to validate

    Raises:
        ValueError: If message exceeds maximum length
        HTTPException: If message is too long (for API responses)

    Examples:
        >>> validate_message_length("Hello")  # Valid
        >>> validate_message_length("A" * 10001)  # Raises ValueError
    """
    max_length = get_max_message_length()

    if len(message) > max_length:
        raise ValueError(
            f"Message exceeds maximum length of {max_length} characters. "
            f"Your message is {len(message)} characters long. "
            f"Please shorten your message and try again."
        )


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    # Rate limiting
    "limiter",
    "get_user_id_from_request",
    "get_rate_limit",
    # Input sanitization
    "sanitize_message",
    "validate_message_length",
    # CORS configuration
    "get_frontend_urls",
    "allow_credentials",
    "get_max_message_length",
    # Exception handlers
    "rate_limit_exceeded_handler",
]
