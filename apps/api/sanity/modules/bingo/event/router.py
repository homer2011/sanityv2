from fastapi import APIRouter, status

from sanity.common.pagination.deps import PageDependency
from sanity.db.deps import DatabaseDependency

from .schema import EventCreate, EventRead, EventReadList, EventReadWithBoard, EventUpdate

router = APIRouter(prefix="/events", tags=["Bingo Events"])


@router.get("", response_model=EventReadList)
async def list_events(
    db_session: DatabaseDependency,
    page: PageDependency,
):
    pass


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=EventRead,
)
async def create_event(
    db_session: DatabaseDependency,
    body: EventCreate,
):
    pass


@router.get("/{event_id}", response_model=EventReadWithBoard)
async def get_event_by_id(
    db_session: DatabaseDependency,
    event_id: int,
):
    pass


@router.patch("/{event_id}", response_model=EventRead)
async def update_event_by_id(
    db_session: DatabaseDependency,
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
    db_session: DatabaseDependency,
    event_id: int,
):
    pass
