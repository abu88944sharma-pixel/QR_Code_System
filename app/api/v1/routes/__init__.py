from fastapi import APIRouter

from app.api.v1.routes.client import router as client_router
from app.api.v1.routes.user import router as user_router

router = APIRouter()
router.include_router(user_router)
router.include_router(client_router)

__all__ = ["router"]
