"""
JWT Authentication dependencies for FastAPI.

This module provides dependencies for verifying JWT tokens issued during authentication.
All protected endpoints should use these dependencies to ensure only authenticated users can access them.
"""
import os
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from jose import jwt, JWTError
from pydantic import BaseModel

from src.db import get_session
from src.models import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Security configuration
SECRET_KEY = os.getenv("BETTER_AUTH_SECRET")
ALGORITHM = "HS256"


# ============================================================================
# Error Models
# ============================================================================


class AuthenticationError(BaseModel):
    """Error response for authentication failures."""
    detail: str = "Authentication required"
    code: str = "AUTHENTICATION_REQUIRED"


class AuthorizationError(BaseModel):
    """Error response for authorization failures."""
    detail: str = "You don't have permission to access this resource"
    code: str = "FORBIDDEN"


# ============================================================================
# JWT Token Payload
# ============================================================================


class TokenPayload(BaseModel):
    """
    JWT token payload structure.

    The token issued by FastAPI contains:
    - sub: User ID (UUID)
    - email: User email
    - name: User display name (optional)
    - iat: Issued at timestamp
    - exp: Expiration timestamp
    """
    sub: str
    email: str
    name: str | None = None
    iat: int
    exp: int


# ============================================================================
# Authentication Dependencies
# ============================================================================


async def get_current_user(
    authorization: Annotated[str, Header(...)],
    session: Annotated[AsyncSession, Depends(get_session)]
) -> User:
    """
    Verify JWT token and return the current authenticated user.

    This dependency:
    1. Extracts the JWT token from the Authorization header
    2. Verifies the token signature using BETTER_AUTH_SECRET
    3. Checks token expiration
    4. Fetches the user from the database
    5. Returns the user object

    Args:
        authorization: Authorization header value (format: "Bearer <token>")
        session: Database session

    Returns:
        User object from database

    Raises:
        HTTPException 401: If token is missing, invalid, or expired
        HTTPException 500: If SECRET_KEY is not configured

    Example:
        ```python
        @app.get("/api/users/me")
        async def get_me(user: User = Depends(get_current_user)):
            return user
        ```
    """
    # Check if SECRET_KEY is configured
    if not SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "SERVER_ERROR",
                "message": "Server authentication configuration error"
            }
        )

    # Extract token from Authorization header
    # Format: "Bearer <token>"
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_TOKEN_FORMAT",
                "message": "Authorization header must be in format: Bearer <token>"
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.split(" ")[1]

    # Verify and decode JWT token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        token_data = TokenPayload(**payload)
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_TOKEN",
                "message": "Invalid or expired token"
            },
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    # Get user from database
    result = await session.execute(
        select(User).where(User.id == token_data.sub)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "USER_NOT_FOUND",
                "message": "User not found"
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_user_id(
    user: Annotated[User, Depends(get_current_user)]
) -> str:
    """
    Get the current user's ID from the authenticated user.

    This is a convenience dependency for endpoints that only need the user ID
    rather than the full user object.

    Args:
        user: Current authenticated user (from get_current_user)

    Returns:
        User ID (UUID string)

    Example:
        ```python
        @app.get("/api/tasks")
        async def get_tasks(user_id: str = Depends(get_current_user_id)):
            return tasks.filter(user_id=user_id)
        ```
    """
    return user.id


async def require_auth(
    authorization: Annotated[str, Header(...)]
) -> TokenPayload:
    """
    Verify JWT token and return the payload without fetching user.

    This is a lightweight dependency for endpoints that only need to verify
    authentication but don't need the full user object.

    Args:
        authorization: Authorization header value (format: "Bearer <token>")

    Returns:
        Token payload with user ID, email, name

    Example:
        ```python
        @app.post("/api/verify-auth")
        async def verify_auth(payload: TokenPayload = Depends(require_auth)):
            return {"authenticated": True, "user_id": payload.sub}
        ```
    """
    # Check if SECRET_KEY is configured
    if not SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "SERVER_ERROR",
                "message": "Server authentication configuration error"
            }
        )

    # Extract token from Authorization header
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_TOKEN_FORMAT",
                "message": "Authorization header must be in format: Bearer <token>"
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.split(" ")[1]

    # Verify and decode JWT token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return TokenPayload(**payload)
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_TOKEN",
                "message": "Invalid or expired token"
            },
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


# ============================================================================
# Optional Authentication
# ============================================================================


async def get_optional_user(
    authorization: Annotated[str | None, Header(None)] = None,
    session: Annotated[AsyncSession, Depends(get_session)] = None
) -> User | None:
    """
    Optional authentication - returns user if token provided, None otherwise.

    This dependency is useful for endpoints that have different behavior for
    authenticated vs anonymous users, but don't require authentication.

    Args:
        authorization: Authorization header value (optional)
        session: Database session

    Returns:
        User object if authenticated, None otherwise

    Example:
        ```python
        @app.get("/api/public-endpoint")
        async def public_endpoint(user: User | None = Depends(get_optional_user)):
            if user:
                return {"message": f"Hello {user.name}"}
            return {"message": "Hello anonymous user"}
        ```
    """
    # No authorization header provided
    if not authorization:
        return None

    # Check if SECRET_KEY is configured
    if not SECRET_KEY:
        return None

    # Extract token from Authorization header
    if not authorization.startswith("Bearer "):
        return None

    token = authorization.split(" ")[1]

    # Verify and decode JWT token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        token_data = TokenPayload(**payload)
    except JWTError:
        return None

    # Get user from database
    result = await session.execute(
        select(User).where(User.id == token_data.sub)
    )
    user = result.scalar_one_or_none()

    return user


# ============================================================================
# Type Aliases for Convenience
# ============================================================================

# Common dependency aliases for cleaner code
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentUserId = Annotated[str, Depends(get_current_user_id)]
