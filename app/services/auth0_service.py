"""
Service layer for all Auth0 Management API interactions.
Handles user creation, role assignment, password resets, and user deletion.
Management API tokens are cached with TTL to minimize redundant token fetches.
"""

import time
import requests

from app.core.config import (
    AUTH0_CLIENT_ID,
    AUTH0_CLIENT_SECRET,
    AUTH0_DB_CONNECTION,
    AUTH0_DOMAIN,
    AUTH0_MANAGEMENT_API_AUDIENCE,
)

# Cached Management API token and its expiry timestamp
_mgmt_token_cache = None
_mgmt_token_expires_at = 0


def get_management_token() -> str:
    """
    Fetch a Management API token using client credentials grant.
    Returns a cached token if it is still valid (with a 60-second safety buffer).
    Only fetches a new token when the cached one is expired or missing.
    """
    global _mgmt_token_cache, _mgmt_token_expires_at
    
    current_time = time.time()
    if _mgmt_token_cache and current_time < (_mgmt_token_expires_at - 60):
        return _mgmt_token_cache

    url = f"https://{AUTH0_DOMAIN}/oauth/token"

    payload = {
        "client_id": AUTH0_CLIENT_ID,
        "client_secret": AUTH0_CLIENT_SECRET,
        "audience": AUTH0_MANAGEMENT_API_AUDIENCE,
        "grant_type": "client_credentials",
    }

    response = requests.post(url, json=payload)
    response_data = response.json()
    
    _mgmt_token_cache = response_data["access_token"]
    expires_in = response_data.get("expires_in", 3600)
    _mgmt_token_expires_at = current_time + expires_in
    
    return _mgmt_token_cache


def _management_headers() -> dict:
    """Build authorization headers for Auth0 Management API calls."""
    token = get_management_token()
    return {
        "authorization": f"Bearer {token}",
        "content-type": "application/json",
    }


def _safe_json(response):
    """Safely parse JSON from a response. Returns empty dict on failure."""
    try:
        return response.json()
    except ValueError:
        return {}


def create_auth0_user(email: str, password: str, name: str) -> dict:
    """Create a new user in Auth0 with email/password authentication."""
    url = f"https://{AUTH0_DOMAIN}/api/v2/users"

    data = {
        "email": email,
        "name": name,
        "password": password,
        "connection": "Username-Password-Authentication",
    }

    response = requests.post(url, json=data, headers=_management_headers())

    return {
        "success": response.ok,
        "status_code": response.status_code,
        "data": _safe_json(response),
    }


def assign_auth0_role_to_user(auth0_user_id: str, auth0_role_id: str) -> dict:
    """Assign a specific role to a user in Auth0."""
    url = f"https://{AUTH0_DOMAIN}/api/v2/users/{auth0_user_id}/roles"

    payload = {
        "roles": [auth0_role_id],
    }

    response = requests.post(url, json=payload, headers=_management_headers())

    return {
        "success": response.ok,
        "status_code": response.status_code,
        "data": _safe_json(response),
    }


def send_password_reset_email(email: str):
    """
    Trigger a password reset email via Auth0.
    This is sent as an invite after user creation so they can set their own password.
    """
    url = f"https://{AUTH0_DOMAIN}/dbconnections/change_password"

    payload = {
        "client_id": AUTH0_CLIENT_ID,
        "email": email,
        "connection": AUTH0_DB_CONNECTION,
    }

    headers = {
        "content-type": "application/json",
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Failed to send reset email: {response.text}")

    return response.text


def delete_auth0_user(user_id: str):
    """Permanently remove a user from Auth0 using the Management API."""
    token = get_management_token()

    url = f"https://{AUTH0_DOMAIN}/api/v2/users/{user_id}"

    response = requests.delete(
        url,
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    if not response.ok:
        raise Exception(f"Failed to delete Auth0 user: {response.text}")
