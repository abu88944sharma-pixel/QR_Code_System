import requests

from app.core.config import (
    AUTH0_CLIENT_ID,
    AUTH0_CLIENT_SECRET,
    AUTH0_DB_CONNECTION,
    AUTH0_DOMAIN,
    AUTH0_MANAGEMENT_API_AUDIENCE,
)


def get_management_token() -> str:
    url = f"https://{AUTH0_DOMAIN}/oauth/token"

    payload = {
        "client_id": AUTH0_CLIENT_ID,
        "client_secret": AUTH0_CLIENT_SECRET,
        "audience": AUTH0_MANAGEMENT_API_AUDIENCE,
        "grant_type": "client_credentials",
    }

    response = requests.post(url, json=payload)
    return response.json()["access_token"]


def _management_headers() -> dict:
    token = get_management_token()
    return {
        "authorization": f"Bearer {token}",
        "content-type": "application/json",
    }


def _safe_json(response):
    try:
        return response.json()
    except ValueError:
        return {}


def create_auth0_user(email: str, password: str, name: str) -> dict:
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


def get_auth0_roles() -> dict:
    url = f"https://{AUTH0_DOMAIN}/api/v2/roles"

    response = requests.get(url, headers=_management_headers())

    return {
        "success": response.ok,
        "status_code": response.status_code,
        "data": _safe_json(response),
    }


def remove_all_roles_from_user(user_id: str):
    token = get_management_token()

    url = f"https://{AUTH0_DOMAIN}/api/v2/users/{user_id}/roles"

    roles = requests.get(
        url,
        headers={
            "Authorization": f"Bearer {token}",
        },
    ).json()

    role_ids = [role["id"] for role in roles]

    if role_ids:
        requests.delete(
            url,
            json={"roles": role_ids},
            headers={
                "Authorization": f"Bearer {token}",
            },
        )


def delete_auth0_user(user_id: str):
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
