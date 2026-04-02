from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.schemas.user import CreateUserRequest
from app.services.user_service import (
    create_user_service,
    delete_user_service,
    get_roles_service,
    get_users_service,
)
from app.utils.helpers import success_response
from app.core.rate_limit import limiter

router = APIRouter(prefix="/api/v1", tags=["User"])


@router.get("/me")
@limiter.limit("60/minute")
def get_me(request: Request, current_user: dict = Depends(get_current_user)):
    return success_response(
        "User verified",
        {
            "db_user": current_user["db_user"],
            "db_role": current_user["db_user"]["role"],
            "token_role_ids": current_user["token_role_ids"],
        },
    )


@router.post("/create-user")
@limiter.limit("10/minute")
def create_user(
    request: Request,
    data: CreateUserRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    create_user_service(db, data, current_user)
    return success_response("User created successfully", {}, status_code=201)


@router.get("/users")
@limiter.limit("100/minute")
def get_users(
    request: Request,
    page: int = Query(1, ge=1),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    client_id: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    users = get_users_service(db, current_user, page, search, status, role, client_id)
    return success_response("Users fetched successfully", users)


@router.get("/roles")
@limiter.limit("100/minute")
def get_roles_auth0(request: Request, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    roles = get_roles_service(current_user, db)
    return success_response("Roles fetched successfully", roles)


@router.delete("/users/{auth0_id}")
@limiter.limit("20/minute")
def delete_user(
    request: Request,
    auth0_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    delete_user_service(db, auth0_id, current_user)
    return success_response("User deleted successfully", {})
