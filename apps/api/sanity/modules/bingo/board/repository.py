from sanity.db.repository import RepositoryBase

from .model import Board


class BoardRepository(RepositoryBase[Board]):
    model = Board
