from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routes import router as api_router
from app.core.config import CORS_ALLOW_ORIGINS
from app.db.base import Base
from app.db.session import engine, run_schema_migrations
from app.db import models as db_models  # noqa: F401
from app.utils.helpers import error_response

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)
run_schema_migrations()

app.include_router(api_router)


def _parse_exception_detail(detail):
    if isinstance(detail, dict):
        return detail.get("message", "Request failed"), detail.get("data", {})

    if isinstance(detail, list):
        return "Validation error", detail

    return str(detail), {}


@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException):
    message, data = _parse_exception_detail(exc.detail)
    return error_response(message, status_code=exc.status_code, data=data)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: Request, exc: RequestValidationError):
    return error_response("Validation error", status_code=422, data=exc.errors())


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Request, exc: Exception):
    print("Unhandled server error:", str(exc))
    return error_response("Internal server error", status_code=500)
