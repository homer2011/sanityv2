from typing import Sequence

from sanity.db.deps import AsyncSession
from sanity.errors.exceptions import ResourceAlreadyExists, ResourceNotFound

from .model import Event
from .repository import EventRepository
from .schemas import EventCreate, EventPatch


class EventService:
    async def create_event(self, *, session: AsyncSession, event_create: EventCreate) -> Event:
        repository = EventRepository(session)

        event_exists = await repository.exists_by_name(event_create.name)
        if event_exists:
            raise ResourceAlreadyExists(f"event already exists with name {event_create.name}")

        return await repository.create(
            Event(name=event_create.name),
            flush=True,
        )

    async def list_events(self, *, session: AsyncSession) -> Sequence[Event]:
        repository = EventRepository(session)
        statement = repository.get_base_statement()

        return await repository.get_all(statement)

    async def get_event(self, *, session: AsyncSession, event_id: int) -> Event:
        repository = EventRepository(session)

        return await self._get_event_by_id_or_raise(
            repository=repository,
            event_id=event_id,
        )

    async def patch_event(
        self, *, session: AsyncSession, event_id: int, event_patch: EventPatch
    ) -> Event:
        repository = EventRepository(session)

        event = await self._get_event_by_id_or_raise(
            repository=repository,
            event_id=event_id,
        )

        return await repository.update(
            event,
            update_dict=event_patch.model_dump(exclude_unset=True),
            flush=True,
        )

    async def delete_event(self, *, session: AsyncSession, event_id: int) -> None:
        repository = EventRepository(session)

        event = await self._get_event_by_id_or_raise(
            repository=repository,
            event_id=event_id,
        )

        await repository.delete(event)

    # --------------
    # helper methods
    # --------------

    async def _get_event_by_id_or_raise(
        self, *, repository: EventRepository, event_id: int
    ) -> Event:
        statement = repository.get_base_statement().where(Event.id == event_id)

        event = await repository.get_one_or_none(statement)
        if event is None:
            raise ResourceNotFound(f"Event not found with ID {event_id}")

        return event


event_service = EventService()
