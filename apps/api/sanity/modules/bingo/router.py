from fastapi import APIRouter

from .catalogue.router import router as catalogue_router
from .event.router import router as event_router

router = APIRouter(prefix="/bingo")
router.include_router(catalogue_router)
router.include_router(event_router)
