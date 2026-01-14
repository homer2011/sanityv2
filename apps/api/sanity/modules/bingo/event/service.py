from sqlalchemy.ext.asyncio import AsyncSession

from .model import Event
from .repository import EventRepository
from .schemas import EventCreate, EventUpdate


class EventService:
    async def list(self, *, db: AsyncSession, offset: int, limit: int):
        repository = EventRepository(db)
        return await repository.paginate(order_by=None, offset=offset, limit=limit)

    async def create(self, *, db: AsyncSession, body: EventCreate):
        repository = EventRepository(db)

        event = Event(
            name=body.name,
            type=body.type,
        )

        # return await repository.create()

    async def get_by_id(self, *, db: AsyncSession, event_id: int):
        repository = EventRepository(db)

    async def update_by_id(self, *, db: AsyncSession, event_id: int, body: EventUpdate):
        repository = EventRepository(db)

    async def delete_by_id(self, *, db: AsyncSession, event_id: int):
        repository = EventRepository(db)


event_service = EventService()
