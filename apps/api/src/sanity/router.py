from fastapi import APIRouter

from sanity.modules.health.endpoints import router as health_router

api_router = APIRouter(prefix="/v1")
api_router.include_router(health_router)
