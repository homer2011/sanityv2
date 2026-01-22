from sanity.db.repository import RepositoryBase

from .model import Item


class ItemRepository(RepositoryBase[Item]):
    model = Item

    async def exists_by_boss_id_and_name(self, boss_id: int, name: str) -> bool:
        stmt = (
            self.get_base_statement()
            .where(self.model.boss_id == boss_id)
            .where(self.model.name == name)
        )

        result = await self.get_one_or_none(stmt)
        return result is not None
