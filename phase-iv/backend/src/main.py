"""
FastAPI application for Todo Full-Stack Web Application.
"""
import os
import logging
import sys
from pathlib import Path
from typing import Callable
from uuid import UUID, uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

# Load environment variables from .env file
load_dotenv()

# Configure logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Create logs directory if it doesn't exist
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Configure root logger
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format=LOG_FORMAT,
    datefmt=DATE_FORMAT,
    handlers=[
        logging.StreamHandler(sys.stdout),  # Console handler for development
        logging.FileHandler(LOG_DIR / "app.log"),  # File handler
    ],
)

logger = logging.getLogger(__name__)


# Request ID Middleware
class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add unique request IDs to all incoming requests.
    Helps with tracing and debugging requests through the system.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate or retrieve request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid4())

        # Add request ID to request state for access in endpoints
        request.state.request_id = request_id

        # Process request
        logger.info(f"Request started: {request.method} {request.url.path} [ID: {request_id}]")
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            logger.info(
                f"Request completed: {request.method} {request.url.path} "
                f"[ID: {request_id}] Status: {response.status_code}"
            )
            return response
        except Exception as e:
            logger.error(
                f"Request failed: {request.method} {request.url.path} "
                f"[ID: {request_id}] Error: {str(e)}"
            )
            raise


# Create FastAPI application
app = FastAPI(
    title="Todo API",
    description="RESTful API for multi-user task management with JWT authentication",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add request ID middleware
app.add_middleware(RequestIDMiddleware)

# Configure CORS middleware
# This allows the frontend (running on a different port/domain) to make API requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://full-stack-application-82mc4iqod.vercel.app",
        "https://q4-hackhthon-ii.vercel.app",
        "https://todo-application-rho-flax.vercel.app",
        "https://todo-application-chatbot.vercel.app",
    ],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """
    Validate environment variables on startup.
    Ensures critical configuration is present before accepting requests.
    """
    logger.info("=" * 60)
    logger.info("Starting Todo API Application")
    logger.info("=" * 60)

    critical_errors = []

    # Validate BETTER_AUTH_SECRET
    better_auth_secret = os.getenv("BETTER_AUTH_SECRET")
    if not better_auth_secret or better_auth_secret.strip() == "":
        error_msg = "CRITICAL: BETTER_AUTH_SECRET environment variable not set or empty!"
        logger.error(error_msg)
        logger.error("This variable is required for JWT token generation and validation.")
        logger.error("Please set it in Render Dashboard with at least 32 random characters.")
        critical_errors.append("BETTER_AUTH_SECRET is required")
    elif len(better_auth_secret) < 32:
        logger.warning(
            f"WARNING: BETTER_AUTH_SECRET is shorter than 32 characters "
            f"(current length: {len(better_auth_secret)}). "
            "For security, use at least 32 characters."
        )
        logger.info(f"BETTER_AUTH_SECRET configured (length: {len(better_auth_secret)})")
    else:
        logger.info(f"BETTER_AUTH_SECRET configured (length: {len(better_auth_secret)})")

    # Validate DATABASE_URL
    database_url = os.getenv("DATABASE_URL")
    if not database_url or database_url.strip() == "":
        error_msg = "CRITICAL: DATABASE_URL environment variable not set or empty!"
        logger.error(error_msg)
        logger.error("This variable is required for database connectivity.")
        logger.error("Please set it in Render Dashboard.")
        critical_errors.append("DATABASE_URL is required")
    else:
        # Check if DATABASE_URL starts with correct prefix
        if not database_url.startswith(("postgresql://", "postgresql+asyncpg://", "postgresql+psycopg2://")):
            logger.warning(
                f"WARNING: DATABASE_URL may not be a valid PostgreSQL URL: {database_url[:20]}..."
            )
        # Extract and log database host (without credentials for security)
        try:
            at_index = database_url.find("@")
            if at_index != -1:
                # Get everything after @ until the next / or ?
                host_start = at_index + 1
                separator_pos = database_url.find("/", host_start)
                query_pos = database_url.find("?", host_start)
                host_end = min(separator_pos, query_pos) if -1 not in (separator_pos, query_pos) else max(separator_pos, query_pos)
                if host_end == -1:
                    host_end = len(database_url)
                db_host = database_url[host_start:host_end]
                logger.info(f"DATABASE_URL configured (host: {db_host})")
            else:
                logger.info("DATABASE_URL configured")
        except Exception:
            logger.info("DATABASE_URL configured")

    # Fail startup if critical errors exist
    if critical_errors:
        error_summary = ", ".join(critical_errors)
        logger.error(f"Startup failed: {error_summary}")
        logger.error("Please set these environment variables in Render Dashboard:")
        logger.error("1. Go to your Web Service in Render Dashboard")
        logger.error("2. Click 'Environment' tab")
        logger.error("3. Add the missing environment variables")
        raise ValueError(f"Startup failed: {error_summary}")

    # Log other configuration
    logger.info(f"Log level: {LOG_LEVEL}")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    logger.info(f"Debug mode: {os.getenv('DEBUG', 'False')}")

    # Log CORS configuration
    logger.info(f"CORS allowed origins: http://localhost:3000, http://127.0.0.1:3000, https://todo-application-chatbot.vercel.app")
    if os.getenv("FRONTEND_URL"):
        logger.info(f"Additional CORS origin: {os.getenv('FRONTEND_URL')}")

    # Log API documentation URL
    logger.info(f"API Documentation: http://localhost:8000/docs")
    logger.info("=" * 60)
    logger.info("Application startup completed successfully")
    logger.info("=" * 60)


@app.get("/")
async def root():
    """Root endpoint - API information."""
    return {
        "message": "Todo API",
        "version": "1.0.0",
        "status": "healthy",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """
    Basic health check endpoint.
    Returns the overall health status of the API.
    """
    return {"status": "healthy", "timestamp": "2026-01-22"}


@app.get("/health/live")
async def liveness_probe():
    """
    Liveness probe - indicates if the server is running.
    This is a simple check that returns 200 if the server is up.
    Used by Kubernetes and other orchestrators to check if the container is alive.
    """
    return {"status": "alive"}


@app.get("/health/ready")
async def readiness_probe():
    """
    Readiness probe - indicates if the server is ready to accept requests.
    Checks database connectivity and other critical dependencies.
    Used by Kubernetes and other orchestrators to check if the container is ready.
    """
    try:
        from src.db import engine
        from sqlalchemy import text

        # Test database connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        logger.debug("Readiness probe: database connection successful")
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        logger.error(f"Readiness probe failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "database": "disconnected",
                "error": str(e)
            }
        )


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler that logs all unhandled exceptions.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(
        f"Unhandled exception: {exc.__class__.__name__}: {str(exc)} "
        f"[Request ID: {request_id}] Path: {request.url.path}"
    )
    return HTTPException(
        status_code=500,
        detail={"error": "Internal server error", "request_id": request_id}
    )


# Rate limit exception handler
from src.api.security import rate_limit_exceeded_handler
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)


# Include routers
from src.api.routes import auth, tasks, chat
app.include_router(auth.router)
app.include_router(tasks.router)
app.include_router(tasks.task_router)
app.include_router(chat.router)


if __name__ == "__main__":
    import uvicorn

    # Run the application
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
