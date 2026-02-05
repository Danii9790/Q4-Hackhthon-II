"""
Authentication dependencies for FastAPI routes.

Extracts and validates user_id from JWT tokens issued by Better Auth.
Provides dependency injection for protected routes.
"""

import os
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from pydantic import ValidationError
from uuid import UUID

# HTTP Bearer scheme for extracting Authorization header
security = HTTPBearer()


# ============================================================================
# JWT Configuration
# ============================================================================

# Better Auth JWT secret (must match frontend Better Auth configuration)
BETTER_AUTH_SECRET = os.getenv(
    "BETTER_AUTH_SECRET",
    "your-secret-key-change-in-production"  # Default for development only
)

# JWT algorithm (Better Auth uses HS256)
JWT_ALGORITHM = "HS256"


# ============================================================================
# JWT Token Verification
# ============================================================================

def decode_jwt_token(token: str) -> dict:
    """
    Decode and verify JWT token issued by Better Auth.

    Args:
        token: JWT token string from Authorization header

    Returns:
        Decoded token payload with user claims

    Raises:
        HTTPException: 401 if token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            BETTER_AUTH_SECRET,
            algorithms=[JWT_ALGORITHM],
            options={
                "verify_signature": True,
                "verify_exp": True,
                "require": ["sub"],  # Required claims (subject = user_id)
            }
        )
        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def extract_user_id_from_token(payload: dict) -> UUID:
    """
    Extract user_id from JWT payload.

    Better Auth stores user_id as UUID string in the 'sub' claim.

    Args:
        payload: Decoded JWT payload

    Returns:
        User UUID

    Raises:
        HTTPException: 401 if user_id is missing or invalid
    """
    user_id_str = payload.get("sub")

    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject claim (user_id)"
        )

    # Validate and convert to UUID
    try:
        user_id = UUID(user_id_str)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format in token (expected UUID)"
        )

    return user_id


# ============================================================================
# Authentication Dependencies
# ============================================================================

async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UUID:
    """
    Dependency to extract user_id from JWT token.

    This is the primary authentication dependency for protected routes.
    It extracts and validates the JWT token, returning the authenticated user's ID.

    Usage in routes:
        @router.get("/api/conversations")
        async def list_conversations(
            user_id: UUID = Depends(get_current_user_id),
            session: AsyncSession = Depends(get_session)
        ):
            # user_id is guaranteed to be valid UUID from JWT
            statement = select(Conversation).where(Conversation.user_id == user_id)
            ...

    Returns:
        UUID: Authenticated user's ID

    Raises:
        HTTPException: 401 if token is missing, invalid, or expired
    """
    # Extract token from Authorization header
    token = credentials.credentials

    # Decode and verify token
    payload = decode_jwt_token(token)

    # Extract and return user_id
    user_id = extract_user_id_from_token(payload)

    return user_id


async def get_current_user_id_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    ),
) -> Optional[UUID]:
    """
    Optional authentication dependency.

    Returns user_id if valid token provided, None otherwise.
    Useful for endpoints that work for both authenticated and anonymous users.

    Usage in routes:
        @router.get("/api/public/content")
        async def get_public_content(
            user_id: Optional[UUID] = Depends(get_current_user_id_optional)
        ):
            if user_id:
                # Authenticated user - return personalized content
                return {"message": "Welcome back!", "authenticated": True}
            else:
                # Anonymous user - return generic content
                return {"message": "Welcome, guest!", "authenticated": False}

    Returns:
        UUID if authenticated, None otherwise
    """
    if not credentials:
        return None

    try:
        return await get_current_user_id(credentials)
    except HTTPException:
        return None


# ============================================================================
# Exports
# ============================================================================

__all__ = [
    "get_current_user_id",
    "get_current_user_id_optional",
    "decode_jwt_token",
    "extract_user_id_from_token",
    "security",
]
