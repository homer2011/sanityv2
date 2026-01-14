from sqlalchemy.orm import joinedload

from sanity.db.repository import RepositoryBase

from ..board.model import Board
from .model import Event


class EventRepository(RepositoryBase[Event]):
    model = Event

    async def get_one_or_none_with_board(self, id_: int) -> Event | None:
        return await self.get_one_or_none(
            id_,
            options=[joinedload(Event.board).joinedload(Board.tiles)],
        )
