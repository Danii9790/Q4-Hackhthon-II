"""
Authentication routes for Todo Application.

This module provides signup and signin endpoints that issue JWT tokens
compatible with Better Auth on the frontend.
"""
import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from jose import jwt
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import select
from sqlmodel import Session

from src.db import get_session
from src.models import User

logger = logging.getLogger(__name__)

# Router configuration
router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Security configuration
SECRET_KEY = os.getenv("BETTER_AUTH_SECRET")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7


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

    Note:
        Bcrypt has a 72-byte limit, so we truncate passwords before hashing.
        This is safe as bcrypt only uses the first 72 bytes anyway.
    """
    # Truncate to 72 bytes (bcrypt limit)
    password_bytes = plain_password.encode('utf-8')[:72]
    return bcrypt.checkpw(password_bytes, hashed_password.encode('utf-8'))


def get_password_hash(password: str) -> str:
    """
    Hash a plaintext password for storage.

    Args:
        password: Plain text password

    Returns:
        Hashed password suitable for database storage

    Note:
        Bcrypt has a 72-byte limit, so we truncate passwords before hashing.
        This is safe as bcrypt only uses the first 72 bytes anyway.
    """
    # Truncate to 72 bytes (bcrypt limit)
    password_bytes = password.encode('utf-8')[:72]
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt(rounds=12))
    return hashed.decode('utf-8')


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
def signup(
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
    statement = select(User).where(User.email == request.email)
    existing_user = session.exec(statement).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "EMAIL_EXISTS",
                "message": "An account with this email already exists"
            }
        )

    # Hash password
    hashed_password = get_password_hash(request.password)

    # Create user
    try:
        user = User(
            email=request.email,
            password_hash=hashed_password,
            name=request.name
        )
        session.add(user)
        session.commit()
        session.refresh(user)
    except Exception as e:
        session.rollback()
        logger.error(f"Database error during user creation: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "DATABASE_ERROR",
                "message": f"Failed to create user account: {str(e)}"
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
def signin(
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
    statement = select(User).where(User.email == request.email)
    user = session.exec(statement).first()

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


# ============================================================================
# Password Reset Endpoints
# ============================================================================


class ForgotPasswordRequest(BaseModel):
    """
    Request schema for password reset.
    """
    email: EmailStr = Field(..., description="User email address")


class ForgotPasswordResponse(BaseModel):
    """
    Response schema for password reset request.
    """
    message: str = Field(..., description="Confirmation message")
    reset_link: str = Field(..., description="Password reset link (for development)")


class ResetPasswordRequest(BaseModel):
    """
    Request schema for resetting password with token.
    """
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, max_length=100, description="New password (min 8 chars)")


class ResetPasswordResponse(BaseModel):
    """
    Response schema for successful password reset.
    """
    message: str = Field(..., description="Success message")


@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
    status_code=status.HTTP_200_OK,
    responses={
        404: {"model": ErrorResponse, "description": "Email not found"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
def forgot_password(
    request: ForgotPasswordRequest,
    session: Annotated[Session, Depends(get_session)]
) -> ForgotPasswordResponse:
    """
    Initiate password reset by generating a reset token.

    This endpoint:
    1. Finds user by email
    2. Generates a secure reset token
    3. Stores token with expiration (1 hour)
    4. Returns reset link (in production, this would be emailed)

    Args:
        request: Forgot password request with email
        session: Database session

    Returns:
        ForgotPasswordResponse with reset link

    Raises:
        HTTPException 404: If email not found (we still return success for security)
        HTTPException 500: If server error occurs
    """
    # Find user by email
    statement = select(User).where(User.email == request.email)
    user = session.exec(statement).first()

    # For security, always return success even if email doesn't exist
    if not user:
        return ForgotPasswordResponse(
            message="If an account exists with this email, a password reset link has been sent.",
            reset_link=""
        )

    # Generate reset token
    import secrets
    reset_token = secrets.token_urlsafe(32)
    
    # Set expiration to 1 hour from now
    reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=1)

    # Store reset token in database
    user.reset_token = reset_token
    user.reset_token_expires = reset_token_expires

    try:
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database error during password reset request: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "DATABASE_ERROR",
                "message": "Failed to process password reset request"
            }
        )

    # In production, you would send an email with the reset link
    # For now, we return it in the response for development
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    reset_link = f"{frontend_url}/reset-password?token={reset_token}"

    return ForgotPasswordResponse(
        message="If an account exists with this email, a password reset link has been sent.",
        reset_link=reset_link  # In production, don't include this
    )


@router.post(
    "/reset-password",
    response_model=ResetPasswordResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid or expired token"},
        404: {"model": ErrorResponse, "description": "Token not found"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
def reset_password(
    request: ResetPasswordRequest,
    session: Annotated[Session, Depends(get_session)]
) -> ResetPasswordResponse:
    """
    Reset user password using a valid reset token.

    This endpoint:
    1. Finds user by reset token
    2. Validates token hasn't expired
    3. Hashes new password
    4. Updates password in database
    5. Clears reset token

    Args:
        request: Reset password request with token and new password
        session: Database session

    Returns:
        ResetPasswordResponse with success message

    Raises:
        HTTPException 400: If token is invalid or expired
        HTTPException 500: If server error occurs
    """
    # Find user by reset token
    statement = select(User).where(User.reset_token == request.token)
    user = session.exec(statement).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_TOKEN",
                "message": "Invalid or expired reset token"
            }
        )

    # Check if token has expired
    if not user.reset_token_expires or user.reset_token_expires < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "EXPIRED_TOKEN",
                "message": "Reset token has expired. Please request a new one."
            }
        )

    # Hash new password
    hashed_password = get_password_hash(request.new_password)

    # Update password and clear reset token
    user.password_hash = hashed_password
    user.reset_token = None
    user.reset_token_expires = None

    try:
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database error during password reset: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "DATABASE_ERROR",
                "message": "Failed to reset password"
            }
        )

    return ResetPasswordResponse(
        message="Password has been reset successfully. You can now sign in with your new password."
    )
