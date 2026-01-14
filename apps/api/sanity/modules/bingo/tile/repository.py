from sanity.db.repository import RepositoryBase

from .model import Tile


class TileRepository(RepositoryBase[Tile]):
    model = Tile
