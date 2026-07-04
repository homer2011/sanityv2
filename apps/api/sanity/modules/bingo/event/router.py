from fastapi import APIRouter, status

from sanity.common.pagination import ListResponse
from sanity.db.deps import DatabaseReadSession, DatabaseWriteSession
from sanity.errors.schemas import ResourceAlreadyExistsResponse, ResourceNotFoundResponse

from .schemas import EventCreate, EventPatch, EventRead
from .service import event_service

router = APIRouter(prefix="/events", tags=["Bingo Events"])


@router.get(
    "",
    response_model=ListResponse[EventRead],
)
async def list_events(
    db_session: DatabaseReadSession,
):
    events = await event_service.list_events(
        session=db_session,
    )

    return ListResponse(
        total=len(events),
        items=events,
    )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=EventRead,
    responses={409: ResourceAlreadyExistsResponse},
)
async def create_event(
    db_session: DatabaseWriteSession,
    event_create: EventCreate,
):
    return await event_service.create_event(
        session=db_session,
        event_create=event_create,
    )


@router.get(
    "/{event_id}",
    response_model=EventRead,
    responses={404: ResourceNotFoundResponse},
)
async def get_event_by_id(
    db_session: DatabaseReadSession,
    event_id: int,
):
    return await event_service.get_event(
        session=db_session,
        event_id=event_id,
    )


@router.patch(
    "/{event_id}",
    response_model=EventRead,
    responses={404: ResourceNotFoundResponse},
)
async def patch_event_by_id(
    db_session: DatabaseWriteSession,
    event_id: int,
    event_patch: EventPatch,
):
    return await event_service.patch_event(
        session=db_session,
        event_id=event_id,
        event_patch=event_patch,
    )


@router.delete(
    "/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    responses={404: ResourceNotFoundResponse},
)
async def delete_event_by_id(
    db_session: DatabaseWriteSession,
    event_id: int,
):
    return await event_service.delete_event(
        session=db_session,
        event_id=event_id,
    )
