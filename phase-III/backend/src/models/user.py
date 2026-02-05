"""
User model for Todo AI Chatbot.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """
    User model for authentication and task ownership.
    """
    __tablename__ = "users"

    id: str = Field(sa_column=Column(String(255), primary_key=True))
    email: str = Field(sa_column=Column(String(255), unique=True, nullable=False, index=True))
    password_hash: str = Field(sa_column=Column(String(255), nullable=False))
    name: str = Field(default="", sa_column=Column(String(255), nullable=False))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    reset_token: Optional[str] = Field(default=None, sa_column=Column(String(255), nullable=True))
    reset_token_expires: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
