from typing import Any, List, Sequence

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.interfaces import ORMOption


class RepositoryBase[T]:
    """
    Base respository for a single ORM model, a 'la Spring JPA repository interfaces.

    - Owns queries + persistence staging
    - Does not commit or rollback; service needs to control transactions

    inspiration: https://github.com/polarsource/polar/blob/main/server/polar/kit/repository/base.py
    """

    model: type[T]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

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

    async def get_one(
        self,
        id: Any,
        options: Sequence[ORMOption] | None = None,
    ) -> T:
        """
        Fetch exactly one row by primary key; raises an exception if not found.
        """
        query = select(self.model).filter_by(id=id)

        if options:
            query = query.options(*options)

        result = await self.session.execute(query)
        return result.unique().scalars().one()

    async def get_one_or_none(
        self,
        id: Any,
        options: Sequence[ORMOption] | None = None,
    ) -> T | None:
        """
        Fetch at most one row by primary key; return None if missing.
        """
        query = select(self.model).filter_by(id=id)

        if options:
            query = query.options(*options)

        result = await self.session.execute(query)
        return result.unique().scalars().one_or_none()

    async def get_all(self) -> Sequence[T]:
        """
        Fetches all rows.
        """
        query = select(self.model)
        result = await self.session.execute(query)
        return result.unique().scalars().all()

    async def paginate(
        self,
        *,
        order_by: List[ColumnElement] | None = None,
        offset: int,
        limit: int,
    ) -> tuple[list[T], int]:
        """
        Fetch a page of rows, plus the total row count in a single query.

        - `order_by` accepts ordering params e.g. created_at desc

        Returns (items, total)
        """
        query = select(self.model)

        if order_by:
            query = query.order_by(*order_by)

        # include count(*) over() for total rows of filtered result set
        query = query.add_columns(func.count().over().label("total"))

        # obtain paged result set
        query = query.offset(offset).limit(limit)

        result = await self.session.execute(query)

        items: list[T] = []
        total: int = 0
        for row in result.unique().all():
            item, total = row._tuple()
            items.append(item)

        return (items, total)

    async def update(
        self,
        obj: T,
        *,
        update_dict: dict[str, Any],
        flush: bool = False,
    ) -> T:
        """
        Apply a partial update (patch) to an existing row.

        This does NOT validate fields.
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
