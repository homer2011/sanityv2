from sanity.db.repository import RepositoryBase

from .model import Item


class ItemRepository(RepositoryBase[Item]):
    model = Item
