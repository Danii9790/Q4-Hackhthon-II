"""
FastAPI application main entry point.

Initializes the FastAPI app with error handlers, middleware, and routers.
Implements T077: Structured logging with request ID tracking.
"""

import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from src.db import close_db, init_db
from src.utils.logging_config import get_logger, generate_request_id, PerformanceTimer, SLOW_REQUEST_THRESHOLD_MS
from src.api.security import get_frontend_urls, allow_credentials
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler


# ============================================================================
# Logger Setup (T077)
# ============================================================================

logger = get_logger(__name__)


# ============================================================================
# Error Response Models
# ============================================================================

class ErrorResponse(dict):
    """
    Standardized error response format.

    All API errors follow this structure for consistent client handling.
    """

    def __init__(
        self,
        error: str,
        message: str,
        code: str,
        status_code: int,
        details: Any = None,
    ):
        super().__init__(
            error=error,
            message=message,
            code=code,
            details=details,
        )
        self.status_code = status_code


# ============================================================================
# Exception Handlers
# ============================================================================

async def http_exception_handler(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:
    """
    Handle HTTPException with standardized error response.

    Maps common HTTP status codes to user-friendly error messages.
    Logs all HTTP errors with context (T077).
    """
    # Extract request ID from state if available
    request_id = getattr(request.state, "request_id", "unknown")

    # Log HTTP exception with context (T077)
    logger.error(
        f"HTTP exception: {exc.status_code} - {exc.detail}",
        extra={
            "request_id": request_id,
            "status_code": exc.status_code,
            "path": str(request.url.path),
            "method": request.method,
        }
    )

    error_mapping = {
        status.HTTP_400_BAD_REQUEST: (
            "Bad Request",
            exc.detail or "The request could not be understood",
            "BAD_REQUEST"
        ),
        status.HTTP_401_UNAUTHORIZED: (
            "Unauthorized",
            exc.detail or "Authentication is required to access this resource",
            "UNAUTHORIZED"
        ),
        status.HTTP_403_FORBIDDEN: (
            "Forbidden",
            exc.detail or "You don't have permission to access this resource",
            "FORBIDDEN"
        ),
        status.HTTP_404_NOT_FOUND: (
            "Not Found",
            exc.detail or "The requested resource was not found",
            "NOT_FOUND"
        ),
        status.HTTP_422_UNPROCESSABLE_ENTITY: (
            "Validation Error",
            exc.detail or "Request validation failed",
            "VALIDATION_ERROR"
        ),
        status.HTTP_429_TOO_MANY_REQUESTS: (
            "Too Many Requests",
            exc.detail or "Rate limit exceeded. Please try again later",
            "RATE_LIMIT_EXCEEDED"
        ),
    }

    # Get error info or use defaults
    error, message, code = error_mapping.get(
        exc.status_code,
        (
            "Error",
            exc.detail or "An unexpected error occurred",
            "UNKNOWN_ERROR"
        )
    )

    error_response = ErrorResponse(
        error=error,
        message=message,
        code=code,
        status_code=exc.status_code,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response,
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Handle all unhandled exceptions with standardized error response.

    This is a catch-all handler for unexpected errors.
    Logs all unexpected exceptions with full context (T077).
    """
    # Extract request ID from state if available
    request_id = getattr(request.state, "request_id", "unknown")

    # Log unexpected exception with full context (T077)
    logger.error(
        f"Unhandled exception: {exc.__class__.__name__}",
        exc_info=True,
        extra={
            "request_id": request_id,
            "exception_type": exc.__class__.__name__,
            "path": str(request.url.path),
            "method": request.method,
        }
    )

    error_response = ErrorResponse(
        error="Internal Server Error",
        message="An unexpected error occurred. Please try again later",
        code="INTERNAL_ERROR",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        details=str(exc) if os.getenv("DEBUG") else None,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response,
    )


async def validation_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Handle Pydantic validation errors with standardized response.

    Provides detailed field-level validation error messages.
    Logs validation errors with field details (T077).
    """
    # Extract request ID from state if available
    request_id = getattr(request.state, "request_id", "unknown")

    # Pydantic validation errors have a specific structure
    if hasattr(exc, "errors"):
        errors = exc.errors()  # type: ignore
        details = [
            {
                "field": ".".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            }
            for error in errors
        ]

        # Log validation error with field details (T077)
        logger.warning(
            f"Validation error: {len(errors)} field(s)",
            extra={
                "request_id": request_id,
                "validation_errors": details,
                "path": str(request.url.path),
                "method": request.method,
            }
        )
    else:
        details = None

        # Log generic validation error (T077)
        logger.warning(
            f"Validation error: {str(exc)}",
            extra={
                "request_id": request_id,
                "path": str(request.url.path),
                "method": request.method,
            }
        )

    error_response = ErrorResponse(
        error="Validation Error",
        message="Request validation failed. Please check your input",
        code="VALIDATION_ERROR",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details=details,
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response,
    )


async def rate_limit_exception_handler(
    request: Request,
    exc: RateLimitExceeded,
) -> JSONResponse:
    """
    Handle rate limit exceeded errors with standardized response.

    T083: Rate limiting - Returns 429 status with clear error message
    and retry information. Logs rate limit violations for monitoring.
    """
    # Extract request ID from state if available
    request_id = getattr(request.state, "request_id", "unknown")

    # Log rate limit violation (T077, T083)
    logger.warning(
        f"Rate limit exceeded",
        extra={
            "request_id": request_id,
            "path": str(request.url.path),
            "method": request.method,
            "client_ip": request.client.host if request.client else "unknown",
        }
    )

    # Calculate retry time (1 minute from now)
    retry_after = 60  # seconds

    error_response = ErrorResponse(
        error="Too Many Requests",
        detail=f"Rate limit exceeded. Please try again in {retry_after} seconds.",
        code="RATE_LIMIT_EXCEEDED",
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        details={"retry_after": retry_after}
    )

    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content=error_response,
        headers={"Retry-After": str(retry_after)}
    )


# ============================================================================
# Application Lifecycle
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events for database connections
    and other resources. Logs lifecycle events (T077).
    """
    # Startup: Initialize database
    logger.info("Starting up Todo AI Chatbot API...")

    # Import engine to pass to init_db
    from src.db.session import engine

    db_initialized = await init_db(engine)
    if not db_initialized:
        logger.warning("Database initialization failed, but application will continue")
    else:
        logger.info("Database initialized successfully")

    yield

    # Shutdown: Close database connections
    logger.info("Shutting down Todo AI Chatbot API...")
    await close_db()
    logger.info("Database connections closed")


# ============================================================================
# FastAPI Application
# ============================================================================

# Create FastAPI app with lifespan
app = FastAPI(
    title="Todo AI Chatbot API",
    description="AI-powered task management with natural language interface",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ============================================================================
# Request Logging Middleware (T077)
# ============================================================================

@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """
    Middleware to log all requests and responses with timing (T077).

    Features:
    - Generates unique request ID for log correlation
    - Logs request method, path, and client IP
    - Measures and logs request duration
    - Logs slow requests (>3s) at WARNING level
    - Logs response status code
    - Adds request ID to request state for access in handlers
    """
    # Generate request ID for log correlation
    request_id = generate_request_id()
    request.state.request_id = request_id

    # Record start time
    start_time = time.time()

    # Extract client IP (handle proxy headers)
    forwarded_for = request.headers.get("X-Forwarded-For")
    client_ip = forwarded_for.split(",")[0] if forwarded_for else request.client.host if request.client else "unknown"

    # Log incoming request (T077)
    logger.info(
        f"Request started: {request.method} {request.url.path}",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query_params": str(request.query_params) if request.query_params else None,
            "client_ip": client_ip,
            "user_agent": request.headers.get("user-agent"),
        }
    )

    try:
        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        # Log response (T077)
        log_level = logger.warning if duration_ms > SLOW_REQUEST_THRESHOLD_MS else logger.info
        log_level(
            f"Request completed: {request.method} {request.url.path} - {response.status_code}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "client_ip": client_ip,
            }
        )

        # Add request ID to response header for client-side correlation
        response.headers["X-Request-ID"] = request_id

        return response

    except Exception as e:
        # Calculate duration for failed requests
        duration_ms = (time.time() - start_time) * 1000

        # Log failed request (T077)
        logger.error(
            f"Request failed: {request.method} {request.url.path}",
            exc_info=True,
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "duration_ms": duration_ms,
                "client_ip": client_ip,
                "exception_type": e.__class__.__name__,
            }
        )
        raise


# Register exception handlers
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Register Pydantic validation error handler if available
try:
    from fastapi.exceptions import RequestValidationError
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
except ImportError:
    pass

# T083: Register rate limit exception handler
app.add_exception_handler(RateLimitExceeded, rate_limit_exception_handler)


# ============================================================================
# CORS Middleware (T085: Environment-based CORS Configuration)
# ============================================================================

# T085: Configure CORS from environment variables
# Supports multiple origins via comma-separated FRONTEND_URL
# Disables credentials in production for security
frontend_origins = get_frontend_urls()
allow_creds = allow_credentials()

logger.info(
    f"CORS configured: origins={frontend_origins}, allow_credentials={allow_creds}"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=frontend_origins,
    allow_credentials=allow_creds,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],  # Explicit methods for security
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-Request-ID",
        "X-Client-Version",
    ],  # Explicit headers for security
)


# ============================================================================
# Health Check Endpoint
# ============================================================================

@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.

    Returns service status and basic information.
    """
    return {
        "status": "healthy",
        "service": "todo-ai-chatbot",
        "version": "1.0.0",
    }


# ============================================================================
# Root Endpoint
# ============================================================================

@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "message": "Todo AI Chatbot API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


# ============================================================================
# Router Registration
# ============================================================================

# Register chat router with /api prefix
from src.api.chat import router as chat_router
from src.api.auth import router as auth_router

# Include routers
app.include_router(auth_router)  # Authentication endpoints
app.include_router(chat_router, prefix="/api")

# Example: Register conversation and task routers
# from src.api.conversations import router as conversations_router
# from src.api.tasks import router as tasks_router
# app.include_router(conversations_router, prefix="/api", tags=["conversations"])
# app.include_router(tasks_router, prefix="/api", tags=["tasks"])


# ============================================================================
# Imports
# ============================================================================

import os


# ============================================================================
# Exports
# ============================================================================

__all__ = ["app"]
