from typing import Optional

from fastapi import APIRouter, Depends, Query
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

router = APIRouter(prefix="/api/v1")


@router.post("/clients")
def create_client(
    data: CreateClientRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    client = create_client_service(db, data, current_user)
    return success_response("Client created successfully", client)


@router.get("/clients")
def get_clients(
    page: int = Query(1, ge=1),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    clients = get_clients_service(db, current_user, page, search, status)
    return success_response("Clients fetched successfully", clients)


@router.put("/clients/{client_id}")
def update_client(
    client_id: str,
    data: UpdateClientRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    client = update_client_service(db, client_id, data, current_user)
    return success_response("Client updated successfully", client)


@router.delete("/clients/{client_id}")
def delete_client(
    client_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    delete_client_service(db, client_id, current_user)
    return success_response("Client deleted successfully", {})
