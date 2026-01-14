from sqlalchemy.ext.asyncio import AsyncSession

from ..boss.schemas import BossCreate, BossUpdate
from ..item.schemas import ItemCreate, ItemUpdate


class CatalogueService:
    async def list_bosses(self, *, db: AsyncSession, offset: int, limit: int):
        pass

    async def create_boss(self, *, db: AsyncSession, body: BossCreate):
        pass

    async def get_boss_by_id(self, *, db: AsyncSession, boss_id: int):
        pass

    async def update_boss_by_id(self, *, db: AsyncSession, boss_id: int, body: BossUpdate):
        pass

    async def delete_boss_by_id(self, *, db: AsyncSession, boss_id: int):
        pass

    async def create_item_by_boss_id(self, *, db: AsyncSession, boss_id: int, body: ItemCreate):
        pass

    async def get_item_by_id(self, *, db: AsyncSession, item_id: int):
        pass

    async def update_item_by_id(self, *, db: AsyncSession, item_id: int, body: ItemUpdate):
        pass

    async def delete_item_by_id(self, *, db: AsyncSession, item_id: int):
        pass


catalogue_service = CatalogueService()
