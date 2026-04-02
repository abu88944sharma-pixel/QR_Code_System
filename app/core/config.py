"""
Application configuration loaded from environment variables.
All secrets and connection strings are stored in the .env file (never committed to git).
"""

import os

from dotenv import load_dotenv

load_dotenv()

# Auth0 JWT verification settings
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE")
ALGORITHMS = os.getenv("ALGORITHMS")

# Auth0 Management API credentials (Machine-to-Machine app)
AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID")
AUTH0_CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET")
AUTH0_MANAGEMENT_API_AUDIENCE = os.getenv("AUTH0_MANAGEMENT_API_AUDIENCE")

# Custom claim key where Auth0 stores role IDs in the JWT token
AUTH0_ROLE_IDS_CLAIM = os.getenv(
    "AUTH0_ROLE_IDS_CLAIM",
    "https://qr-system-api.com/role_ids",
)

AUTH0_DB_CONNECTION = os.getenv("AUTH0_DB_CONNECTION")

# PostgreSQL connection string
DATABASE_URL = os.getenv("DATABASE_URL")

# Parse comma-separated CORS origins into a list
CORS_ALLOW_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ALLOW_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    ).split(",")
    if origin.strip()
]
