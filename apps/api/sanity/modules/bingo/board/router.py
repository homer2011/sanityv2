from fastapi import APIRouter, status

from sanity.db.core import DatabaseSession

from ..tile.schemas import TileCreate, TileRead
from .schemas import BoardReadWithTiles, BoardUpdate

router = APIRouter(prefix="/boards", tags=["Bingo Boards"])


@router.patch(
    "/{board_id}",
    response_model=BoardReadWithTiles,
)
async def update_board_by_id(
    db_session: DatabaseSession,
    board_id: int,
    body: BoardUpdate,
):
    pass


@router.post(
    "/{board_id}/tiles",
    status_code=status.HTTP_201_CREATED,
    response_model=TileRead,
)
async def create_tile_by_board_id(
    db_session: DatabaseSession,
    board_id: int,
    body: TileCreate,
):
    pass
