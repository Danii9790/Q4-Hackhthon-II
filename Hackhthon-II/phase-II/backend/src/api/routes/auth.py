"""
Authentication routes for Todo Application.

This module provides signup and signin endpoints that issue JWT tokens
compatible with Better Auth on the frontend.
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from jose import jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db import get_session
from src.models import User

# Router configuration
router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Security configuration
SECRET_KEY = os.getenv("BETTER_AUTH_SECRET")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Basic for initial credentials
security = HTTPBasic()


# ============================================================================
# Request/Response Schemas
# ============================================================================


class SignupRequest(BaseModel):
    """
    Request schema for user signup.

    Validation:
    - email: Must be valid email format
    - password: Min 8 characters
    - name: Optional display name
    """

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, max_length=100, description="Password (min 8 chars)")
    name: str | None = Field(None, max_length=200, description="Optional display name")

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v


class SigninRequest(BaseModel):
    """
    Request schema for user signin.

    Validation:
    - email: Must be valid email format
    - password: Required
    """

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class UserResponse(BaseModel):
    """
    User information response.

    Note: Password is NEVER included in responses.
    """

    id: str = Field(..., description="User ID (UUID)")
    email: str = Field(..., description="User email address")
    name: str | None = Field(None, description="User display name")
    created_at: datetime = Field(..., description="Account creation timestamp")


class AuthResponse(BaseModel):
    """
    Response schema for successful authentication.

    Returns:
    - token: JWT bearer token (7-day expiration)
    - user: User object with id, email, name
    """

    token: str = Field(..., description="JWT bearer token")
    user: UserResponse = Field(..., description="Authenticated user information")


class ErrorDetail(BaseModel):
    """
    Error detail structure.
    """

    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")


class ErrorResponse(BaseModel):
    """
    Standard error response schema.
    """

    error: ErrorDetail = Field(..., description="Error details")


# ============================================================================
# JWT Token Utilities
# ============================================================================


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Payload data to encode (typically user_id, email, name)
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string

    Raises:
        HTTPException: If SECRET_KEY is not configured
    """
    if not SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "SERVER_ERROR",
                "message": "Server authentication configuration error"
            }
        )

    to_encode = data.copy()

    # Set expiration time
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)

    to_encode.update({
        "iat": datetime.now(timezone.utc),
        "exp": expire
    })

    # Encode JWT
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# ============================================================================
# Password Utilities
# ============================================================================


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plaintext password against a hashed password.

    Args:
        plain_password: Plain text password from user input
        hashed_password: Hashed password from database

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a plaintext password for storage.

    Args:
        password: Plain text password

    Returns:
        Hashed password suitable for database storage
    """
    return pwd_context.hash(password)


# ============================================================================
# Endpoints
# ============================================================================


@router.post(
    "/signup",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Validation error or email already exists"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
async def signup(
    request: SignupRequest,
    session: Annotated[Session, Depends(get_session)]
) -> AuthResponse:
    """
    Create a new user account and issue a JWT token.

    This endpoint:
    1. Validates email format and password strength
    2. Checks if email already exists
    3. Hashes password with bcrypt
    4. Creates user in database
    5. Issues JWT token with 7-day expiration

    Args:
        request: Signup request with email, password, and optional name
        session: Database session

    Returns:
        AuthResponse with JWT token and user information

    Raises:
        HTTPException 400: If email already exists or validation fails
        HTTPException 500: If server error occurs
    """
    # Check if user already exists
    existing_user = session.execute(
        select(User).where(User.email == request.email)
    ).scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "EMAIL_EXISTS",
                "message": "An account with this email already exists"
            }
        )

    # Generate UUID for new user
    import uuid
    user_id = str(uuid.uuid4())

    # Hash password
    hashed_password = get_password_hash(request.password)

    # Create user
    user = User(
        id=user_id,
        email=request.email,
        password_hash=hashed_password,
        name=request.name,
        created_at=datetime.now(timezone.utc)
    )

    session.add(user)

    try:
        session.commit()
        session.refresh(user)
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "DATABASE_ERROR",
                "message": "Failed to create user account"
            }
        )

    # Create JWT token
    token_data = {
        "sub": user.id,
        "email": user.email,
        "name": user.name
    }
    access_token = create_access_token(token_data)

    return AuthResponse(
        token=access_token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            created_at=user.created_at
        )
    )


@router.post(
    "/signin",
    response_model=AuthResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid credentials"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
async def signin(
    request: SigninRequest,
    session: Annotated[Session, Depends(get_session)]
) -> AuthResponse:
    """
    Authenticate a user and issue a JWT token.

    This endpoint:
    1. Finds user by email
    2. Verifies password against hash
    3. Issues JWT token with 7-day expiration

    Args:
        request: Signin request with email and password
        session: Database session

    Returns:
        AuthResponse with JWT token and user information

    Raises:
        HTTPException 401: If credentials are invalid
        HTTPException 500: If server error occurs
    """
    # Find user by email
    user = session.execute(
        select(User).where(User.email == request.email)
    ).scalar_one_or_none()

    # Verify user exists
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_CREDENTIALS",
                "message": "Invalid email or password"
            }
        )

    # Verify password
    if not user.password_hash or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_CREDENTIALS",
                "message": "Invalid email or password"
            }
        )

    # Create JWT token
    token_data = {
        "sub": user.id,
        "email": user.email,
        "name": user.name
    }
    access_token = create_access_token(token_data)

    return AuthResponse(
        token=access_token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            created_at=user.created_at
        )
    )
