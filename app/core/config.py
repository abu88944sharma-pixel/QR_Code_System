import os

from dotenv import load_dotenv

load_dotenv()

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE")
ALGORITHMS = os.getenv("ALGORITHMS")

AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID")
AUTH0_CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET")
AUTH0_MANAGEMENT_API_AUDIENCE = os.getenv("AUTH0_MANAGEMENT_API_AUDIENCE")
AUTH0_ROLE_IDS_CLAIM = os.getenv(
    "AUTH0_ROLE_IDS_CLAIM",
    "https://qr-system-api.com/role_ids",
)

AUTH0_DB_CONNECTION = os.getenv("AUTH0_DB_CONNECTION")

DATABASE_URL = os.getenv("DATABASE_URL")

CORS_ALLOW_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ALLOW_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    ).split(",")
    if origin.strip()
]
