from fastapi import APIRouter

from sanity.modules.bingo.router import router as bingo_router
from sanity.modules.health.router import router as health_router

api_router = APIRouter(prefix="/v1")
api_router.include_router(bingo_router)
api_router.include_router(health_router)
