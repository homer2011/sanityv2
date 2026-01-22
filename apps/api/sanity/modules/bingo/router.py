from fastapi import APIRouter

from .catalogue.router import router as catalogue_router

router = APIRouter(prefix="/bingo")
router.include_router(catalogue_router)
