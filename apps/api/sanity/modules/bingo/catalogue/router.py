from fastapi import APIRouter, status

from sanity.db.core import DatabaseSession

from .schemas import (
    BossCreate,
    BossRead,
    BossReadWithItems,
    BossReadWithItemsList,
    BossUpdate,
    ItemCreate,
    ItemRead,
    ItemUpdate,
)

router = APIRouter(prefix="/catalogue", tags=["Bingo Catalogue"])


@router.get(
    "/bosses",
    response_model=BossReadWithItemsList,
)
async def list_bosses(
    db_session: DatabaseSession,
):
    pass


@router.post(
    "/bosses",
    status_code=status.HTTP_201_CREATED,
    response_model=BossRead,
)
async def create_boss(
    db_session: DatabaseSession,
    body: BossCreate,
):
    pass


@router.get(
    "/bosses/{boss_id}",
    response_model=BossReadWithItems,
)
async def get_boss_by_id(
    db_session: DatabaseSession,
    boss_id: int,
):
    pass


@router.patch(
    "/bosses/{boss_id}",
    response_model=BossRead,
)
async def update_boss_by_id(
    db_session: DatabaseSession,
    boss_id: int,
    body: BossUpdate,
):
    pass


@router.delete(
    "/bosses/{boss_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_boss_by_id(
    db_session: DatabaseSession,
    boss_id: int,
):
    pass


@router.post(
    "/bosses/{boss_id}/items",
    status_code=status.HTTP_201_CREATED,
    response_model=ItemRead,
)
async def create_item_by_boss_id(
    db_session: DatabaseSession,
    boss_id: int,
    body: ItemCreate,
):
    pass


@router.get(
    "/items/{item_id}",
    response_model=ItemRead,
)
async def get_item_by_id(
    db_session: DatabaseSession,
    item_id: int,
):
    pass


@router.patch(
    "/items/{item_id}",
    response_model=ItemRead,
)
async def update_item_by_id(
    db_session: DatabaseSession,
    item_id: int,
    body: ItemUpdate,
):
    pass


@router.delete(
    "/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_item_by_id(
    db_session: DatabaseSession,
    item_id: int,
):
    pass
