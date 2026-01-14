from sanity.db.repository import RepositoryBase

from .model import Boss


class BossRepository(RepositoryBase[Boss]):
    model = Boss
