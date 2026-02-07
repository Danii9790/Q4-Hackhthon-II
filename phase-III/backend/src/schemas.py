"""
Pydantic schemas for request/response models.

Defines all Pydantic models for API request validation and response formatting.
Ensures type safety and provides automatic JSON serialization.
"""

from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


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
    # Error schema
    "ErrorResponse",
]
