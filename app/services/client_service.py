"""
Client service layer for managing tenant/client organizations.
All operations are restricted to super_admin users only.
"""

from math import ceil

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.models import Client, User
from app.schemas.client import CreateClientRequest, UpdateClientRequest
from app.services.user_service import _ensure_super_admin_db_access


def create_client_service(
    db: Session,
    data: CreateClientRequest,
    current_user: dict,
) -> dict:
    """Create a new client organization. Duplicate client_id values are rejected."""
    try:
        _ensure_super_admin_db_access(current_user)

        name = data.name.strip()

        if not name:
            raise HTTPException(status_code=400, detail="Client name is required")

        existing_client = db.query(Client).filter(Client.client_id == data.client_id).first()
        if existing_client:
            raise HTTPException(status_code=409, detail="Client already exists")

        new_client = Client(client_id=data.client_id, name=name)
        db.add(new_client)
        db.commit()
        db.refresh(new_client)
        return {
            "id": new_client.id,
            "client_id": new_client.client_id,
            "name": new_client.name,
            "status": "active" if new_client.is_active else "inactive",
        }
    except Exception:
        db.rollback()
        raise


def get_clients_service(
    db: Session,
    current_user: dict,
    page: int = 1,
    search: str = None,
    status: str = None,
) -> dict:
    """
    Fetch a paginated list of all clients (active, inactive, and deleted).
    Supports optional filtering by status and name search.
    """
    try:
        _ensure_super_admin_db_access(current_user)
        limit = 10
        normalized_page = max(page or 1, 1)

        # No default filter - shows all clients including deleted ones
        scoped_query = db.query(Client)
        
        # Only apply status filter when explicitly requested
        if status:
            is_active = True if status.lower() == "active" else False
            scoped_query = scoped_query.filter(Client.is_active.is_(is_active))
        
        if search:
            scoped_query = scoped_query.filter(Client.name.ilike(f"%{search}%"))
        total_items = scoped_query.count()
        clients = (
            scoped_query
            .order_by(Client.client_id.asc())
            .offset((normalized_page - 1) * limit)
            .limit(limit)
            .all()
        )

        return {
            "items": [
                {
                    "id": client.id,
                    "client_id": client.client_id,
                    "name": client.name,
                    "status": "active" if client.is_active else "inactive",
                }
                for client in clients
            ],
            "pagination": {
                "page": normalized_page,
                "limit": limit,
                "total": total_items,
                "pages": ceil(total_items / limit) if total_items else 0,
            },
        }
    except Exception:
        db.rollback()
        raise


def update_client_service(
    db: Session,
    client_id: str,
    data: UpdateClientRequest,
    current_user: dict,
) -> dict:
    """
    Update a client's name.
    Supports lookup by both numeric DB id and string client_id for flexibility.
    """
    try:
        _ensure_super_admin_db_access(current_user)

        name = data.name.strip()
        if not name:
            raise HTTPException(status_code=400, detail="Client name is required")

        # Allow lookup by numeric ID or string client_id
        if isinstance(client_id, int) or (isinstance(client_id, str) and client_id.isdigit()):
            client_id_as_int = int(client_id)
            filter_condition = or_(
                Client.client_id == str(client_id),
                Client.id == client_id_as_int,
            )
        else:
            filter_condition = Client.client_id == str(client_id)

        client = db.query(Client).filter(filter_condition).first()
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")

        client.name = name
        db.commit()
        db.refresh(client)

        return {
            "id": client.id,
            "client_id": client.client_id,
            "name": client.name,
            "status": "active" if client.is_active else "inactive",
        }
    except Exception:
        db.rollback()
        raise


def delete_client_service(
    db: Session,
    client_id: str,
    current_user: dict,
):
    """
    Soft-delete a client by marking it as deleted and inactive.
    Prevents deletion if any active users are still associated with the client.
    """
    try:
        _ensure_super_admin_db_access(current_user)

        if isinstance(client_id, int) or (isinstance(client_id, str) and client_id.isdigit()):
            client_id_as_int = int(client_id)
            filter_condition = or_(
                Client.client_id == str(client_id),
                Client.id == client_id_as_int,
            )
        else:
            filter_condition = Client.client_id == str(client_id)

        # Only allow deleting clients that are not already deleted
        client = (
            db.query(Client)
            .filter(
                Client.is_deleted.is_(False),
                filter_condition,
            )
            .first()
        )
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")

        # Block deletion if there are active users under this client
        associated_user = (
            db.query(User)
            .filter(
                User.client_id == client.id,
                User.is_deleted.is_(False),
            )
            .first()
        )
        if associated_user:
            raise HTTPException(
                status_code=400,
                detail="Client cannot be deleted because users are associated with it",
            )

        client.is_deleted = True
        client.is_active = False
        db.commit()
    except Exception:
        db.rollback()
        raise
