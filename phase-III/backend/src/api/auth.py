"""
Authentication API endpoints for the Todo AI Chatbot.

Implements Better Auth-compatible endpoints for sign in, sign up, and session management.
Works with the Neon PostgreSQL database.
"""

import os
from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import AsyncSessionLocal
from src.models.user import User

# ============================================================================
# Configuration
# ============================================================================

router = APIRouter(prefix="/api/auth", tags=["authentication"])

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Secret from environment
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# ============================================================================
# Pydantic Models
# ============================================================================

class SignInRequest(BaseModel):
    email: EmailStr
    password: str

class SignUpRequest(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None

class AuthResponse(BaseModel):
    user: dict
    token: str
    message: str

# ============================================================================
# Helper Functions
# ============================================================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)

def create_access_token(data: dict) -> str:
    """Create a JWT access token."""
    from jose import jwt
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)
    return encoded_jwt

# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/signin", response_model=AuthResponse)
async def sign_in(request: SignInRequest):
    """
    Sign in an existing user.

    Compatible with Better Auth client's sign in flow.
    """
    async with AsyncSessionLocal() as session:
        # Find user by email
        statement = select(User).where(User.email == request.email)
        result = await session.execute(statement)
        user = result.scalar_one_or_none()

        # Verify user exists and password is correct
        if not user or not verify_password(request.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )

        # Create access token
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )

        return AuthResponse(
            user={
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
            },
            token=access_token,
            message="Sign in successful"
        )

@router.post("/signup", response_model=AuthResponse)
async def sign_up(request: SignUpRequest):
    """
    Sign up a new user.

    Compatible with Better Auth client's sign up flow.
    """
    async with AsyncSessionLocal() as session:
        # Check if user already exists
        statement = select(User).where(User.email == request.email)
        result = await session.execute(statement)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # Create new user
        new_user = User(
            id=str(uuid4()),
            email=request.email,
            password_hash=get_password_hash(request.password),
            name=request.name or request.email.split("@")[0],
            created_at=datetime.utcnow()
        )

        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)

        # Create access token
        access_token = create_access_token(
            data={"sub": str(new_user.id), "email": new_user.email}
        )

        return AuthResponse(
            user={
                "id": str(new_user.id),
                "email": new_user.email,
                "name": new_user.name,
            },
            token=access_token,
            message="Account created successfully"
        )

@router.get("/session")
async def get_current_session(token: str):
    """
    Get the current session from a JWT token.

    Compatible with Better Auth client's session check.
    """
    from jose import jwt, JWTError

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        email: str = payload.get("email")

        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Fetch user from database
    async with AsyncSessionLocal() as session:
        statement = select(User).where(User.id == user_id)
        result = await session.execute(statement)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "user": {
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
            },
            "token": token
        }

@router.post("/signout")
async def sign_out():
    """
    Sign out the current user.

    For JWT-based auth, this is mainly a client-side operation,
    but we provide the endpoint for Better Auth compatibility.
    """
    return {"message": "Signed out successfully"}

# ============================================================================
# Dependencies
# ============================================================================

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/signin")

async def get_current_user(token: str = None) -> Optional[dict]:
    """Get the current user from a JWT token."""
    if not token:
        return None

    from jose import jwt, JWTError
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")

        if user_id is None:
            return None

    except JWTError:
        return None

    # Fetch user from database
    async with get_session() as session:
        statement = select(User).where(User.id == user_id)
        result = await session.execute(statement)
        user = result.scalar_one_or_none()

        if not user:
            return None

        return {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
        }
