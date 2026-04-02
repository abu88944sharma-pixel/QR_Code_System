import requests
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from jose import jwt
from sqlalchemy.orm import Session, joinedload

from app.core.config import ALGORITHMS, AUTH0_AUDIENCE, AUTH0_DOMAIN, AUTH0_ROLE_IDS_CLAIM
from app.db.models import User
from app.db.session import get_db

security = HTTPBearer()

jwks_url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
jwks = requests.get(jwks_url).json()


def verify_token(token: str) -> dict:
    try:
        unverified_header = jwt.get_unverified_header(token)

        rsa_key = {}
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"],
                }

        if rsa_key:
            return jwt.decode(
                token,
                rsa_key,
                algorithms=[ALGORITHMS],
                audience=AUTH0_AUDIENCE,
                issuer=f"https://{AUTH0_DOMAIN}/",
            )

        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception:
        raise HTTPException(status_code=401, detail="Token validation failed")


def get_current_user(
    credentials=Depends(security),
    db: Session = Depends(get_db),
) -> dict:
    token = credentials.credentials
    payload = verify_token(token)
    token_role_ids = payload.get(AUTH0_ROLE_IDS_CLAIM, [])

    if isinstance(token_role_ids, str):
        token_role_ids = [token_role_ids]
    elif not isinstance(token_role_ids, list):
        token_role_ids = []

    user = (
        db.query(User)
        .options(joinedload(User.role))
        .filter(User.auth0_id == payload["sub"])
        .first()
    )

    if not user:
        raise HTTPException(status_code=403, detail="User not found in DB")

    role_name = user.role.auth0_role_name if user.role else None

    return {
        "auth0_id": user.auth0_id,
        "created_by": user.created_by,
        "db_user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": role_name,
            "client_id": user.client_id,
        },
        "token_role_ids": token_role_ids,
    }
