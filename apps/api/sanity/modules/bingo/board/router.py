from fastapi import APIRouter, status

from sanity.db.core import DatabaseDependency
from sanity.modules.bingo.board.schema import (
    BoardReadWithTiles,
    BoardUpdate,
    TileCreate,
    TileRead,
    TileUpdate,
)

router = APIRouter(tags=["Bingo Boards"])


@router.patch(
    "/boards/{board_id}",
    response_model=BoardReadWithTiles,
)
async def update_board_by_id(
    db_session: DatabaseDependency,
    board_id: int,
    body: BoardUpdate,
):
    pass


@router.post(
    "/boards/{board_id}/tiles",
    status_code=status.HTTP_201_CREATED,
    response_model=TileRead,
)
async def create_tile_by_board_id(
    db_session: DatabaseDependency,
    board_id: int,
    body: TileCreate,
):
    pass


@router.get(
    "/tiles/{tile_id}",
    response_model=TileRead,
)
async def get_tile_by_id(
    db_session: DatabaseDependency,
    tile_id: int,
):
    pass


@router.patch(
    "/tiles/{tile_id}",
    response_model=TileRead,
)
async def update_tile_by_id(
    db_session: DatabaseDependency,
    tile_id: int,
    body: TileUpdate,
):
    pass


@router.delete(
    "/tiles/{tile_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_tile_by_id(
    db_session: DatabaseDependency,
    tile_id: int,
):
    pass
