from fastapi import APIRouter, status

from sanity.common.pagination import ListResponse
from sanity.db.deps import DatabaseReadSession, DatabaseWriteSession
from sanity.errors.schemas import ResourceAlreadyExistsResponse, ResourceNotFoundResponse

from ..boss.schemas import BossCreate, BossPatch, BossRead
from ..item.schemas import ItemCreate, ItemPatch, ItemRead
from .schemas import BossReadWithItems, ItemReadWithBoss

router = APIRouter(prefix="/catalogue", tags=["Bingo Catalogue"])


@router.get(
    "/bosses",
    response_model=ListResponse[BossReadWithItems],
)
async def list_bosses(
    db_session: DatabaseReadSession,
):
    pass


@router.post(
    "/bosses",
    status_code=status.HTTP_201_CREATED,
    response_model=BossRead,
    responses={409: ResourceAlreadyExistsResponse},
)
async def create_boss(
    db_session: DatabaseWriteSession,
    boss_create: BossCreate,
):
    pass


@router.get(
    "/bosses/{boss_id}",
    response_model=BossReadWithItems,
    responses={404: ResourceNotFoundResponse},
)
async def get_boss_by_id(
    db_session: DatabaseReadSession,
    boss_id: int,
):
    pass


@router.patch(
    "/bosses/{boss_id}",
    response_model=BossRead,
    responses={404: ResourceNotFoundResponse},
)
async def patch_boss_by_id(
    db_session: DatabaseWriteSession,
    boss_id: int,
    boss_patch: BossPatch,
):
    pass


@router.delete(
    "/bosses/{boss_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    responses={404: ResourceNotFoundResponse},
)
async def delete_boss_by_id(
    db_session: DatabaseWriteSession,
    boss_id: int,
):
    pass


@router.post(
    "/bosses/{boss_id}/items",
    status_code=status.HTTP_201_CREATED,
    response_model=ItemRead,
    responses={404: ResourceNotFoundResponse, 409: ResourceAlreadyExistsResponse},
)
async def create_item_by_boss_id(
    db_session: DatabaseWriteSession,
    boss_id: int,
    item_create: ItemCreate,
):
    pass


@router.get(
    "/bosses/{boss_id}/items",
    response_model=ListResponse[ItemRead],
    responses={404: ResourceNotFoundResponse},
)
async def list_items_by_boss_id(
    db_session: DatabaseReadSession,
    boss_id: int,
):
    pass


@router.get(
    "/items/{item_id}",
    response_model=ItemReadWithBoss,
    responses={404: ResourceNotFoundResponse},
)
async def get_item_by_id(
    db_session: DatabaseReadSession,
    item_id: int,
):
    pass


@router.patch(
    "/items/{item_id}",
    response_model=ItemRead,
    responses={404: ResourceNotFoundResponse},
)
async def patch_item_by_id(
    db_session: DatabaseWriteSession,
    item_id: int,
    item_patch: ItemPatch,
):
    pass


@router.delete(
    "/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    responses={404: ResourceNotFoundResponse},
)
async def delete_item_by_id(
    db_session: DatabaseWriteSession,
    item_id: int,
):
    pass
