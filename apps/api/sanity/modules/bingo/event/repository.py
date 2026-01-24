from apps.api.sanity.db.repository import RepositoryBase

from .model import Event


class EventRepository(RepositoryBase[Event]):
    model = Event
