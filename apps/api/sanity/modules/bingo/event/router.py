from fastapi import APIRouter, status

from sanity.db.core import DatabaseSession

from .schemas import EventCreate, EventReadList, EventReadWithBoard, EventUpdate

router = APIRouter(prefix="/events", tags=["Bingo Events"])


@router.get(
    "",
    response_model=EventReadList,
)
async def list_events(
    db_session: DatabaseSession,
):
    pass


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=EventReadWithBoard,
)
async def create_event(
    db_session: DatabaseSession,
    body: EventCreate,
):
    pass


@router.get(
    "/{event_id}",
    response_model=EventReadWithBoard,
)
async def get_event_by_id(
    db_session: DatabaseSession,
    event_id: int,
):
    pass


@router.patch(
    "/{event_id}",
    response_model=EventReadWithBoard,
)
async def update_event_by_id(
    db_session: DatabaseSession,
    event_id: int,
    body: EventUpdate,
):
    pass


@router.delete(
    "/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_event_by_id(
    db_session: DatabaseSession,
    event_id: int,
):
    pass
