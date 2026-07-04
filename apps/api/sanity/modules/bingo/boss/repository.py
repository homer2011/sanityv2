from sanity.db.repository import RepositoryBase

from .model import Boss


class BossRepository(RepositoryBase[Boss]):
    model = Boss

    async def exists_by_name(self, name: str) -> bool:
        stmt = self.get_base_statement().where(self.model.name == name)

        result = await self.get_one_or_none(stmt)
        return result is not None
