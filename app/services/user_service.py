"""
User service layer handling all user-related business logic.
This includes user creation (with Auth0 sync), listing, role fetching, and deletion.
Supports multi-tenant isolation: admins can only manage users within their own client scope.
"""

import logging
import secrets
import string
from math import ceil

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.db.models import Client, Role, User
from app.schemas.user import CreateUserRequest
from app.services.auth0_service import (
    assign_auth0_role_to_user,
    create_auth0_user,
    delete_auth0_user,
    send_password_reset_email,
)

logger = logging.getLogger(__name__)


def generate_temporary_password(length: int = 16) -> str:
    """
    Generate a strong random password that meets Auth0 complexity requirements.
    Guarantees at least one uppercase, one lowercase, one digit, and one special character.
    """
    uppercase = secrets.choice(string.ascii_uppercase)
    lowercase = secrets.choice(string.ascii_lowercase)
    digit = secrets.choice(string.digits)
    special = secrets.choice("!@#$%^&*")

    remaining_length = max(length - 4, 0)
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    remaining = "".join(secrets.choice(alphabet) for _ in range(remaining_length))

    password_chars = list(uppercase + lowercase + digit + special + remaining)
    secrets.SystemRandom().shuffle(password_chars)
    return "".join(password_chars)


def _ensure_super_admin_db_access(current_user: dict):
    """Guard function: raises 403 if the current user is not a super_admin in the database."""
    if current_user["db_user"]["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Not allowed")


def create_user_service(db: Session, data: CreateUserRequest, current_user: dict):
    """
    Create a new user in both Auth0 and the local database.
    
    Flow:
    1. Validate permissions (only super_admin and admin can create users)
    2. Determine role and client scope based on the creator's role
    3. Create the user in Auth0 and assign the role
    4. Save the user record in the local database
    5. Send a password reset email so the user can set their own password
    """
    try:
        db_user = current_user["db_user"]
        creator_role = db_user.get("role")
        if creator_role not in ["super_admin", "admin"]:
            raise HTTPException(status_code=403, detail="Not allowed")

        name = data.name.strip()
        email = data.email
        temporary_password = generate_temporary_password()

        if not name:
            raise HTTPException(status_code=400, detail="Name is required")

        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            raise HTTPException(status_code=409, detail="User already exists")

        # Admin users can only create users under their own client with the same role
        if creator_role == "admin":
            role = db.query(Role).filter(Role.auth0_role_name == "admin").first()
            if not role:
                raise HTTPException(status_code=500, detail="Admin role missing in database")
            
            client_id = db_user.get("client_id")
            if not client_id:
                raise HTTPException(status_code=400, detail="Admin doesn't have an associated client")

        # Super admins can assign any role and any client
        else:
            if not data.role or not data.role.strip():
                raise HTTPException(status_code=400, detail="Role is required")

            requested_role_id = data.role.strip()
            role = db.query(Role).filter(Role.auth0_role_id == requested_role_id).first()
            if not role:
                raise HTTPException(status_code=400, detail=f"Role id '{requested_role_id}' not found in database")

            if not role.auth0_role_id:
                raise HTTPException(status_code=400, detail=f"Auth0 role id missing for role '{role.auth0_role_name}'")

            # Super admins don't need a client, but admin-role users do
            client_id = data.client_id
            if role.auth0_role_name == "super_admin":
                client_id = None
            else:
                if client_id is None:
                    raise HTTPException(status_code=400, detail="client_id is required for admin users")
                
                # Support lookup by both numeric ID and string client_id
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
                    raise HTTPException(status_code=400, detail="Client not found in database")
                client_id = client.id

        # Step 1: Create user in Auth0
        auth0_response = create_auth0_user(email, temporary_password, name)
        print("AUTH0 CREATE USER RESPONSE:", auth0_response)

        if not auth0_response["success"]:
            auth0_error = auth0_response["data"]
            if auth0_response["status_code"] == 409 or (
                isinstance(auth0_error, dict)
                and "already exists" in auth0_error.get("message", "").lower()
            ):
                raise HTTPException(status_code=409, detail="User already exists")

            raise HTTPException(status_code=400, detail="Auth0 user creation failed")

        auth0_user_data = auth0_response["data"]
        if "user_id" not in auth0_user_data:
            raise HTTPException(
                status_code=400,
                detail="Auth0 user created but user_id missing in response",
            )

        auth0_id = auth0_user_data["user_id"]

        # Step 2: Assign the role in Auth0
        role_assignment_response = assign_auth0_role_to_user(auth0_id, role.auth0_role_id)
        print("AUTH0 ROLE ASSIGN RESPONSE:", role_assignment_response)

        if not role_assignment_response["success"]:
            raise HTTPException(status_code=400, detail="Auth0 role assignment failed")

        # Step 3: Save user in local database
        new_user = User(
            auth0_id=auth0_id,
            name=name,
            email=email,
            created_by=current_user["auth0_id"],
            role_id=role.id,
            client_id=client_id,
        )

        db.add(new_user)
        db.commit()

        # Step 4: Send invite email (non-blocking, failure here should not crash the flow)
        try:
            send_password_reset_email(email)
        except Exception as exc:
            print("Failed to send invite email:", str(exc))
    except Exception:
        db.rollback()
        raise


def get_users_service(
    db: Session,
    current_user: dict,
    page: int = 1,
    search: str = None,
    status: str = None,
    role: str = None,
    client_id: str = None,
) -> dict:
    """
    Fetch a paginated, filterable list of users.
    Super admins see all users; admins only see users within their own client.
    The current user is always excluded from the results.
    """
    try:
        db_user = current_user["db_user"]
        user_role = db_user["role"]
        limit = 10
        normalized_page = max(page or 1, 1)

        # Eagerly load role and client to avoid N+1 queries in the response
        query = db.query(User).options(joinedload(User.role), joinedload(User.client))
        # Exclude the requesting user from the list
        query = query.filter(User.auth0_id != current_user["auth0_id"])

        if search:
            query = query.filter(
                or_(
                    User.name.ilike(f"%{search}%"),
                    User.email.ilike(f"%{search}%")
                )
            )

        if status:
            is_active = True if status.lower() == "active" else False
            query = query.filter(User.is_active == is_active)

        if role:
            query = query.join(Role, User.role_id == Role.id).filter(Role.auth0_role_name == role)

        if client_id:
            query = query.join(Client, User.client_id == Client.id).filter(Client.client_id == client_id)

        # Multi-tenant scoping: admins can only see their own client's users
        if user_role == "super_admin":
            scoped_query = query
        elif user_role == "admin":
            current_client_id = db_user.get("client_id")
            if current_client_id is None:
                return {
                    "items": [],
                    "pagination": {
                        "page": normalized_page,
                        "limit": limit,
                        "total": 0,
                        "pages": 0,
                    },
                }

            scoped_query = query.filter(User.client_id == current_client_id)
        else:
            raise HTTPException(status_code=403, detail="Not allowed")

        total_items = scoped_query.count()
        users = (
            scoped_query
            .order_by(User.id.asc())
            .offset((normalized_page - 1) * limit)
            .limit(limit)
            .all()
        )

        return {
            "items": [
                {
                    "auth0_id": user.auth0_id,
                    "name": user.name,
                    "email": user.email,
                    "status": "active" if user.is_active else "inactive",
                    "role": user.role.auth0_role_name if user.role else None,
                    "client_id": user.client.client_id if user.client else None,
                    "client_name": user.client.name if user.client else None,
                }
                for user in users
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


def get_roles_service(current_user: dict, db: Session) -> list[dict]:
    """Return all active roles. Only accessible by super admins."""
    _ensure_super_admin_db_access(current_user)

    roles = db.query(Role).filter(Role.is_deleted == False, Role.is_active == True).all()

    return [
        {
            "id": role.auth0_role_id,
            "name": role.auth0_role_name,
        }
        for role in roles
        if role.auth0_role_id
    ]


def delete_user_service(db: Session, auth0_id: str, current_user: dict):
    """
    Delete a user from both the local database (soft delete) and Auth0 (hard delete).
    
    Flow:
    1. Mark user as deleted and inactive in the local DB
    2. Delete the user from Auth0 via Management API
    3. Commit the DB transaction only if Auth0 deletion succeeds
    
    If Auth0 deletion fails, the DB transaction is rolled back to keep both in sync.
    """
    try:
        db_user = current_user["db_user"]
        creator_role = db_user.get("role")
        current_auth0_id = current_user["auth0_id"]

        if creator_role not in ["super_admin", "admin"]:
            raise HTTPException(status_code=403, detail="Not allowed")

        if auth0_id == current_auth0_id:
            raise HTTPException(status_code=400, detail="You cannot delete yourself")

        target_user = db.query(User).filter(User.auth0_id == auth0_id).first()
        if not target_user:
            raise HTTPException(status_code=404, detail="User not found")

        # Admins can only delete users within their own client scope
        if creator_role == "admin":
            current_client_id = db_user.get("client_id")
            if target_user.client_id != current_client_id:
                raise HTTPException(status_code=403, detail="Not allowed to delete users outside your client scope")

        # Soft delete in local DB first
        target_user.is_deleted = True
        target_user.is_active = False

        # Hard delete from Auth0 (if this fails, DB changes are rolled back below)
        delete_auth0_user(auth0_id)
        
        db.commit()

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        # Log the real error server-side but return a generic message to the client
        logger.error(f"Error deleting user {auth0_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
