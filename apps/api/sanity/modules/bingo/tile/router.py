from fastapi import APIRouter, status

from sanity.db.core import DatabaseSession

from .schemas import TileRead, TileUpdate

router = APIRouter(prefix="/tiles", tags=["Bingo Boards"])


@router.get(
    "/{tile_id}",
    response_model=TileRead,
)
async def get_tile_by_id(
    db_session: DatabaseSession,
    tile_id: int,
):
    pass


@router.patch(
    "/{tile_id}",
    response_model=TileRead,
)
async def update_tile_by_id(
    db_session: DatabaseSession,
    tile_id: int,
    body: TileUpdate,
):
    pass


@router.delete(
    "/{tile_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_tile_by_id(
    db_session: DatabaseSession,
    tile_id: int,
):
    pass
