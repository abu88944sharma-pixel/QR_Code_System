from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.schemas.client import CreateClientRequest, UpdateClientRequest
from app.services.client_service import (
    create_client_service,
    delete_client_service,
    update_client_service,
    get_clients_service,
)
from app.utils.helpers import success_response
from app.core.rate_limit import limiter

router = APIRouter(prefix="/api/v1", tags=["Client"])


@router.post("/clients")
@limiter.limit("10/minute")
def create_client(
    request: Request,
    data: CreateClientRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    client = create_client_service(db, data, current_user)
    return success_response("Client created successfully", client, status_code=201)


@router.get("/clients")
@limiter.limit("100/minute")
def get_clients(
    request: Request,
    page: int = Query(1, ge=1),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    clients = get_clients_service(db, current_user, page, search, status)
    return success_response("Clients fetched successfully", clients)


@router.put("/clients/{client_id}")
@limiter.limit("20/minute")
def update_client(
    request: Request,
    client_id: str,
    data: UpdateClientRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    client = update_client_service(db, client_id, data, current_user)
    return success_response("Client updated successfully", client)


@router.delete("/clients/{client_id}")
@limiter.limit("10/minute")
def delete_client(
    request: Request,
    client_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    delete_client_service(db, client_id, current_user)
    return success_response("Client deleted successfully", {})
