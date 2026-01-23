from typing import Sequence

from sqlalchemy.orm import joinedload

from sanity.db.deps import AsyncSession
from sanity.errors.exceptions import ResourceAlreadyExists, ResourceNotFound

from ..boss.model import Boss
from ..boss.repository import BossRepository
from ..boss.schemas import BossCreate, BossPatch
from ..item.model import Item
from ..item.repository import ItemRepository
from ..item.schemas import ItemCreate, ItemPatch


class CatalogueService:
    async def create_boss(self, *, session: AsyncSession, boss_create: BossCreate) -> Boss:
        repository = BossRepository(session)

        boss_exists = await repository.exists_by_name(boss_create.name)
        if boss_exists:
            raise ResourceAlreadyExists(f"Boss already exists with name {boss_create.name}")

        return await repository.create(
            Boss(
                name=boss_create.name,
                ehb=boss_create.ehb,
            ),
            flush=True,
        )

    async def list_bosses_with_items(self, *, session: AsyncSession) -> Sequence[Boss]:
        repository = BossRepository(session)
        statement = repository.get_base_statement().options(joinedload(Boss.items))

        return await repository.get_all(statement)

    async def get_boss_with_items(self, *, session: AsyncSession, boss_id: int) -> Boss:
        repository = BossRepository(session)

        return await self._get_boss_by_id_or_raise(
            repository=repository,
            boss_id=boss_id,
            include_relationships=True,
        )

    async def patch_boss(
        self, *, session: AsyncSession, boss_id: int, boss_patch: BossPatch
    ) -> Boss:
        repository = BossRepository(session)

        boss = await self._get_boss_by_id_or_raise(
            repository=repository,
            boss_id=boss_id,
        )

        return await repository.update(
            boss,
            update_dict=boss_patch.model_dump(exclude_unset=True),
        )

    async def delete_boss(self, *, session: AsyncSession, boss_id: int) -> None:
        repository = BossRepository(session)

        boss = await self._get_boss_by_id_or_raise(
            repository=repository,
            boss_id=boss_id,
        )

        await repository.delete(boss)

    async def create_item(
        self, *, session: AsyncSession, boss_id: int, item_create: ItemCreate
    ) -> Item:
        boss_repository = BossRepository(session)
        item_repository = ItemRepository(session)

        boss = await self._get_boss_by_id_or_raise(
            repository=boss_repository,
            boss_id=boss_id,
        )

        item_exists = await item_repository.exists_by_boss_id_and_name(boss_id, item_create.name)
        if item_exists:
            raise ResourceAlreadyExists(
                f"Item already exists for this boss with name {item_create.name}"
            )

        return await item_repository.create(
            Item(
                boss_id=boss.id,
                name=item_create.name,
                drop_rate=item_create.drop_rate,
                point_value=item_create.point_value,
            ),
            flush=True,
        )

    async def list_items_for_boss(self, *, session: AsyncSession, boss_id: int) -> Sequence[Item]:
        boss_repository = BossRepository(session)
        item_repository = ItemRepository(session)

        await self._get_boss_by_id_or_raise(
            repository=boss_repository,
            boss_id=boss_id,
        )

        statement = (
            item_repository.get_base_statement()
            .where(Item.boss_id == boss_id)
            .options(joinedload(Item.boss))
        )

        return await item_repository.get_all(statement)

    async def get_item_with_boss(self, *, session: AsyncSession, item_id: int) -> Item:
        repository = ItemRepository(session)

        return await self._get_item_by_id_or_raise(
            repository=repository,
            item_id=item_id,
            include_relationships=True,
        )

    async def patch_item(
        self, *, session: AsyncSession, item_id: int, item_patch: ItemPatch
    ) -> Item:
        repository = ItemRepository(session)

        item = await self._get_item_by_id_or_raise(
            repository=repository,
            item_id=item_id,
        )

        return await repository.update(
            item,
            update_dict=item_patch.model_dump(exclude_unset=True),
        )

    async def delete_item(self, *, session: AsyncSession, item_id: int) -> None:
        repository = ItemRepository(session)

        item = await self._get_item_by_id_or_raise(
            repository=repository,
            item_id=item_id,
        )

        await repository.delete(item)

    # --------------
    # helper methods
    # --------------

    async def _get_boss_by_id_or_raise(
        self, *, repository: BossRepository, boss_id: int, include_relationships: bool = False
    ) -> Boss:
        statement = repository.get_base_statement().where(Boss.id == boss_id)

        if include_relationships:
            statement = statement.options(joinedload(Boss.items))

        boss = await repository.get_one_or_none(statement)
        if boss is None:
            raise ResourceNotFound(f"Boss not found with ID {boss_id}")

        return boss

    async def _get_item_by_id_or_raise(
        self, *, repository: ItemRepository, item_id: int, include_relationships: bool = False
    ) -> Item:
        statement = repository.get_base_statement().where(Item.id == item_id)

        if include_relationships:
            statement = statement.options(joinedload(Item.boss))

        item = await repository.get_one_or_none(statement)
        if item is None:
            raise ResourceNotFound(f"Item not found with ID {item_id}")

        return item


catalogue_service = CatalogueService()
