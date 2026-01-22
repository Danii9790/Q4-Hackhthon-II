"""
User model for Todo Application.

Note: This model is managed by Better Auth.
Shown here for reference and relationship definitions.
"""
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .task import Task


class User(SQLModel, table=True):
    """
    Represents a person who can log into the system and own tasks.

    This table is managed by Better Auth for authentication purposes.

    Attributes:
        id: Unique user identifier (UUID)
        email: User's email address (unique, indexed)
        password_hash: Bcrypt hash of user's password (never returned in responses)
        name: User's display name (optional)
        created_at: Account creation timestamp
        reset_token: Password reset token (optional)
        reset_token_expires: When the reset token expires (optional)
    """
    __tablename__ = "users"

    id: str = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    password_hash: str = Field(default=None, exclude=True)  # Never return in API responses
    name: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    reset_token: Optional[str] = None
    reset_token_expires: Optional[datetime] = None

    # Relationships
    tasks: list["Task"] = Relationship(back_populates="user")
