"""
API dependencies for FastAPI endpoints.

This module exports authentication and authorization dependencies
that can be used to protect API endpoints.
"""
from .auth import (
    get_current_user,
    get_current_user_id,
    require_auth,
    get_optional_user,
    CurrentUser,
    CurrentUserId,
)

__all__ = [
    "get_current_user",
    "get_current_user_id",
    "require_auth",
    "get_optional_user",
    "CurrentUser",
    "CurrentUserId",
]
