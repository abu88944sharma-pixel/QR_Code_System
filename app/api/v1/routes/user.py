from typing import Optional

from fastapi import APIRouter, Depends, Query
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

router = APIRouter(prefix="/api/v1", tags=["User"])


@router.get("/me")
def get_me(current_user: dict = Depends(get_current_user)):
    return success_response(
        "User verified ✅",
        {
            "db_user": current_user["db_user"],
            "db_role": current_user["db_user"]["role"],
            "token_role_ids": current_user["token_role_ids"],
        },
    )


@router.post("/create-user")
def create_user(
    data: CreateUserRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    create_user_service(db, data, current_user)
    return success_response("User created successfully", {})


@router.get("/users")
def get_users(
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
def get_roles_auth0(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    roles = get_roles_service(current_user, db)
    return success_response("Roles fetched successfully", roles)


@router.delete("/users/{auth0_id}")
def delete_user(
    auth0_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    delete_user_service(db, auth0_id, current_user)
    return success_response("User deleted successfully", {})
