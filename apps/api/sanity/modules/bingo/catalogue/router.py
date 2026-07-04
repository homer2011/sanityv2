from fastapi import APIRouter, status

from sanity.common.pagination import ListResponse
from sanity.db.deps import DatabaseReadSession, DatabaseWriteSession
from sanity.errors.schemas import ResourceAlreadyExistsResponse, ResourceNotFoundResponse

from ..boss.schemas import BossCreate, BossPatch, BossRead, BossReadWithItems
from ..item.schemas import ItemCreate, ItemPatch, ItemRead, ItemReadWithCtx
from .service import catalogue_service

router = APIRouter(prefix="/catalogue", tags=["Bingo Catalogue"])


@router.get(
    "/bosses",
    response_model=ListResponse[BossRead],
)
async def list_bosses(
    db_session: DatabaseReadSession,
):
    bosses = await catalogue_service.list_bosses(
        session=db_session,
    )

    return ListResponse(
        total=len(bosses),
        items=bosses,
    )


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
    return await catalogue_service.create_boss(
        session=db_session,
        boss_create=boss_create,
    )


@router.get(
    "/bosses/{boss_id}",
    response_model=BossReadWithItems,
    responses={404: ResourceNotFoundResponse},
)
async def get_boss_by_id(
    db_session: DatabaseReadSession,
    boss_id: int,
):
    return await catalogue_service.get_boss_with_items(
        session=db_session,
        boss_id=boss_id,
    )


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
    return await catalogue_service.patch_boss(
        session=db_session,
        boss_id=boss_id,
        boss_patch=boss_patch,
    )


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
    await catalogue_service.delete_boss(
        session=db_session,
        boss_id=boss_id,
    )


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
    return await catalogue_service.create_item(
        session=db_session,
        boss_id=boss_id,
        item_create=item_create,
    )


@router.get(
    "/bosses/{boss_id}/items",
    response_model=ListResponse[ItemReadWithCtx],
    responses={404: ResourceNotFoundResponse},
)
async def list_items_by_boss_id(
    db_session: DatabaseReadSession,
    boss_id: int,
):
    items = await catalogue_service.list_items_with_context_for_boss(
        session=db_session,
        boss_id=boss_id,
    )

    return ListResponse(
        total=len(items),
        items=items,
    )


@router.get(
    "/items/{item_id}",
    response_model=ItemReadWithCtx,
    responses={404: ResourceNotFoundResponse},
)
async def get_item_by_id(
    db_session: DatabaseReadSession,
    item_id: int,
):
    return await catalogue_service.get_item_with_context(
        session=db_session,
        item_id=item_id,
    )


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
    return await catalogue_service.patch_item(
        session=db_session,
        item_id=item_id,
        item_patch=item_patch,
    )


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
    await catalogue_service.delete_item(
        session=db_session,
        item_id=item_id,
    )
