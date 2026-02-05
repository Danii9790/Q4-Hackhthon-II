"""
FastAPI dependencies for Todo Application.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.services.auth import get_user_id_from_token

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """
    FastAPI dependency to extract authenticated user ID from JWT token.

    This dependency should be used in all protected endpoints to verify
    the user is authenticated and extract their user ID.

    Args:
        credentials: HTTP Bearer credentials containing the JWT token

    Returns:
        User ID (str) extracted from the JWT token

    Raises:
        HTTPException: 401 if token is invalid or missing
    """
    token = credentials.credentials
    try:
        user_id = get_user_id_from_token(token)
        return user_id
    except HTTPException as e:
        # Re-raise with consistent error format
        if e.status_code == status.HTTP_401_UNAUTHORIZED:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "INVALID_TOKEN",
                    "message": "Authentication token is missing or invalid"
                }
            )
        raise
