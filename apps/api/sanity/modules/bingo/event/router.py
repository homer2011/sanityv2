from typing import Sequence

from fastapi import APIRouter, HTTPException, status

from sanity.db.core import DatabaseSession

from ..board.model import Board
from ..board.repository import BoardRepository
from .model import Event
from .repository import EventRepository
from .schemas import EventCreate, EventRead, EventReadList, EventReadWithBoard, EventUpdate

router = APIRouter(prefix="/events", tags=["Bingo Events"])


@router.get(
    "",
    response_model=EventReadList,
)
async def list_events(
    db_session: DatabaseSession,
):
    repo = EventRepository(db_session)
    events = await repo.get_all()

    return EventReadList(
        total=len(events),
        items=[EventRead.model_validate(e) for e in events],
    )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=EventReadWithBoard,
)
async def create_event(
    db_session: DatabaseSession,
    body: EventCreate,
):
    event_repo = EventRepository(db_session)

    event = Event(
        name=body.name,
        type=body.type,
        starts_at=body.starts_at,
        ends_at=body.ends_at,
        board=Board(),
    )
    event = await event_repo.create(event, flush=True)

    await db_session.commit()
    await db_session.refresh(event)
    return event


@router.get(
    "/{event_id}",
    response_model=EventReadWithBoard,
)
async def get_event_by_id(
    db_session: DatabaseSession,
    event_id: int,
):
    repo = EventRepository(db_session)
    event = await repo.get_one_or_none_with_board(event_id)
    if event is None:
        raise HTTPException(404, "Event not found")

    return event


@router.patch(
    "/{event_id}",
    response_model=EventReadWithBoard,
)
async def update_event_by_id(
    db_session: DatabaseSession,
    event_id: int,
    body: EventUpdate,
):
    repo = EventRepository(db_session)
    event = await repo.get_one_or_none(event_id)
    if event is None:
        raise HTTPException(404, "Event not found")

    event = await repo.update(event, update_dict=body.model_dump(exclude_unset=True))
    await db_session.commit()
    return event


@router.delete(
    "/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_event_by_id(
    db_session: DatabaseSession,
    event_id: int,
):
    repo = EventRepository(db_session)
    event = await repo.get_one_or_none(event_id)
    if event is None:
        raise HTTPException(404, "Event not found")

    return await repo.delete(event)
