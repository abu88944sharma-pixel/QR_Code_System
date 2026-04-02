"""
FastAPI application entry point.
Sets up middleware (CORS, rate limiting) and global exception handlers.
Database migrations are managed by Alembic (see README.md for setup instructions).
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1.routes import router as api_router
from app.core.config import CORS_ALLOW_ORIGINS
from app.core.rate_limit import limiter
from app.db.base import Base
from app.db.session import engine
from app.db import models as db_models  # noqa: F401
from app.utils.helpers import error_response

app = FastAPI()

# Attach rate limiter to app state so slowapi can access it globally
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database tables are now managed by Alembic migrations.
# Run "alembic upgrade head" before starting the server.

app.include_router(api_router)


def _parse_exception_detail(detail):
    """Extract a clean message and data payload from an HTTPException detail."""
    if isinstance(detail, dict):
        return detail.get("message", "Request failed"), detail.get("data", {})

    if isinstance(detail, list):
        return "Validation error", detail

    return str(detail), {}


@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException):
    """Return all HTTP errors in a consistent {status, message, data} format."""
    message, data = _parse_exception_detail(exc.detail)
    return error_response(message, status_code=exc.status_code, data=data)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors with a clean 422 response."""
    return error_response("Validation error", status_code=422, data=exc.errors())


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Request, exc: Exception):
    """
    Catch-all for unexpected errors.
    Logs the real error server-side but returns a generic message to the client
    to prevent internal details from leaking.
    """
    print("Unhandled server error:", str(exc))
    return error_response("Internal server error", status_code=500)
