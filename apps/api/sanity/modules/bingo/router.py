from fastapi import APIRouter

from .board.router import router as board_router
from .catalogue.router import router as catalogue_router
from .event.router import router as event_router
from .tile.router import router as tile_router

router = APIRouter(prefix="/bingo")
router.include_router(board_router)
router.include_router(catalogue_router)
router.include_router(event_router)
router.include_router(tile_router)
