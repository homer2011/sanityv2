from fastapi import APIRouter, status

from sanity.common.pagination import ListResponse
from sanity.db.deps import DatabaseReadSession, DatabaseWriteSession
from sanity.errors.schemas import ResourceAlreadyExistsResponse, ResourceNotFoundResponse

from .schemas import EventCreate, EventPatch, EventRead

router = APIRouter(prefix="/events", tags=["Bingo Events"])


@router.get(
    "",
    response_model=ListResponse[EventRead],
)
def list_events(
    db_session: DatabaseReadSession,
):
    pass


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=EventRead,
    responses={409: ResourceAlreadyExistsResponse},
)
def create_event(
    db_session: DatabaseWriteSession,
    event_create: EventCreate,
):
    pass


@router.get(
    "/{event_id}",
    response_model=EventRead,
    responses={404: ResourceNotFoundResponse},
)
def get_event_by_id(
    db_session: DatabaseReadSession,
    event_id: int,
):
    pass


@router.patch(
    "/{event_id}",
    response_model=EventRead,
    responses={404: ResourceNotFoundResponse},
)
def patch_event_by_id(
    db_session: DatabaseWriteSession,
    event_id: int,
    event_patch: EventPatch,
):
    pass


@router.delete(
    "/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    responses={404: ResourceNotFoundResponse},
)
def delete_event_by_id(
    db_session: DatabaseWriteSession,
    event_id: int,
):
    pass
