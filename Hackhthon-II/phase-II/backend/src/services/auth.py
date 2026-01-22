"""
Authentication service for JWT token verification.
"""
import os
from jose import jwt, JWTError
from fastapi import HTTPException

# Secret key for JWT verification (must match frontend)
SECRET_KEY = os.getenv("BETTER_AUTH_SECRET")
ALGORITHM = "HS256"

if not SECRET_KEY:
    raise ValueError(
        "BETTER_AUTH_SECRET environment variable not set. "
        "Please set it in your .env file."
    )


def verify_token(token: str) -> dict:
    """
    Verify JWT token and return payload.

    Args:
        token: JWT token from Authorization header

    Returns:
        Decoded JWT payload containing user information

    Raises:
        HTTPException: If token is invalid or expired (401 Unauthorized)
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=401,
            detail={
                "code": "INVALID_TOKEN",
                "message": "Authentication token is missing or invalid"
            }
        )


def get_user_id_from_token(token: str) -> str:
    """
    Extract user ID from JWT token.

    Args:
        token: JWT token

    Returns:
        User ID (sub claim)

    Raises:
        HTTPException: If token is invalid or user_id is missing
    """
    payload = verify_token(token)
    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail={
                "code": "INVALID_TOKEN",
                "message": "Invalid user ID in token"
            }
        )

    return user_id
