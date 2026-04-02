"""
JWT token verification and user authentication using Auth0.
Handles JWKS key fetching with TTL-based caching to survive key rotations.
"""

import time

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

# In-memory cache for JWKS keys to avoid fetching on every request
_jwks_cache = {}
_jwks_last_fetched = 0


def get_jwks(force_refresh=False) -> dict:
    """
    Fetch Auth0 JWKS keys with a 24-hour TTL cache.
    If force_refresh is True, bypass cache and fetch fresh keys.
    Falls back to stale cache if the network request fails.
    """
    global _jwks_cache, _jwks_last_fetched
    current_time = time.time()
    
    # Refresh if forced, or cache is empty, or cache is older than 24 hours
    if force_refresh or not _jwks_cache or (current_time - _jwks_last_fetched > 86400):
        try:
            _jwks_cache = requests.get(jwks_url).json()
            _jwks_last_fetched = current_time
        except Exception:
            # If we have old keys, keep using them rather than crashing
            if not _jwks_cache:
                raise
    return _jwks_cache


def get_rsa_key(unverified_header: dict, jwks: dict) -> dict:
    """Find the matching RSA key from JWKS using the token's 'kid' (Key ID)."""
    for key in jwks.get("keys", []):
        if key.get("kid") == unverified_header.get("kid"):
            return {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"],
            }
    return {}


def verify_token(token: str) -> dict:
    """
    Decode and verify a JWT token against Auth0's public keys.
    If the key ID is not found (possibly due to key rotation),
    it will force-refresh the JWKS cache and retry once.
    """
    try:
        unverified_header = jwt.get_unverified_header(token)

        jwks = get_jwks()
        rsa_key = get_rsa_key(unverified_header, jwks)
        
        # If kid is not found, Auth0 may have rotated keys. Force refresh and retry.
        if not rsa_key:
            jwks = get_jwks(force_refresh=True)
            rsa_key = get_rsa_key(unverified_header, jwks)

        if rsa_key:
            return jwt.decode(
                token,
                rsa_key,
                algorithms=[ALGORITHMS],
                audience=AUTH0_AUDIENCE,
                issuer=f"https://{AUTH0_DOMAIN}/",
            )

        raise HTTPException(status_code=401, detail="Invalid token (kid not found in JWKS)")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Token validation failed")


def get_current_user(
    credentials=Depends(security),
    db: Session = Depends(get_db),
) -> dict:
    """
    FastAPI dependency that extracts the current user from the Bearer token.
    Verifies the JWT, then looks up the user in the database.
    Returns a dict with auth0_id, db_user details, and token role IDs.
    """
    token = credentials.credentials
    payload = verify_token(token)
    token_role_ids = payload.get(AUTH0_ROLE_IDS_CLAIM, [])

    # Normalize role_ids to always be a list
    if isinstance(token_role_ids, str):
        token_role_ids = [token_role_ids]
    elif not isinstance(token_role_ids, list):
        token_role_ids = []

    # Eagerly load the role relationship to avoid extra queries later
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
