from typing import Any, Sequence

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession


class RepositoryBase[T]:
    """
    Base respository for a single ORM model, à la Spring JPA repository interfaces.

    - Owns queries + persistence staging
    - Does not commit or rollback; service needs to control transactions

    inspiration: https://github.com/polarsource/polar/blob/main/server/polar/kit/repository/base.py
    """

    model: type[T]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ------------------
    # Statement builders
    # ------------------

    def get_base_statement(self) -> Select[tuple[T]]:
        return select(self.model)

    # ------------
    # Read methods
    # ------------

    async def get_one(self, stmt: Select[tuple[T]]) -> T:
        result = await self.session.execute(stmt)
        return result.unique().scalar_one()

    async def get_one_or_none(self, stmt: Select[tuple[T]]) -> T | None:
        result = await self.session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_all(self, stmt: Select[tuple[T]]) -> Sequence[T]:
        result = await self.session.execute(stmt)
        return result.unique().scalars().all()

    async def paginate(
        self, stmt: Select[tuple[T]], *, offset: int, limit: int
    ) -> tuple[list[T], int]:
        # include count(*) over() for total rows of result set before obtaining the page
        paginate_statement: Select[tuple[T, int]] = (
            stmt.add_columns(func.count().over().label("total")).offset(offset).limit(limit)
        )

        result = await self.session.execute(paginate_statement)

        items: list[T] = []
        total: int = 0
        for row in result.unique().all():
            item, total = row._tuple()
            items.append(item)

        return (items, total)

    # -------------
    # Write methods
    # -------------

    async def create(
        self,
        obj: T,
        *,
        flush: bool = False,
    ) -> T:
        """
        Stage a new row for INSERT.
        """
        self.session.add(obj)

        if flush:
            await self.session.flush()

        return obj

    async def update(
        self,
        obj: T,
        *,
        update_dict: dict[str, Any],
        flush: bool = False,
    ) -> T:
        """
        Apply a partial update (patch) to an existing row.
        """
        for k, v in update_dict.items():
            setattr(obj, k, v)

        self.session.add(obj)

        if flush:
            await self.session.flush()

        return obj

    async def delete(self, obj: T) -> None:
        """
        Stage an existing row for DELETE.
        """
        await self.session.delete(obj)
