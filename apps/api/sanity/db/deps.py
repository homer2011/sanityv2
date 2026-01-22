from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession as AsyncSession

from sanity.db.core import async_session_factory


async def get_db_read_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Generates a new async db session scoped to a single request; consumed as a dependency
    within a service layer.

    Intended to be used in a read-only manner, and does not auto-commit.

    docs: https://docs.sqlalchemy.org/en/20/orm/session_api.html#sqlalchemy.orm.sessionmaker
    """

    async with async_session_factory() as session:
        yield session


async def get_db_write_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Generates a new async db session scoped to a single request; consumed as a dependency
    within a service layer.

    Intended to be used in a read-write manner, and includes auto-commit.

    docs: https://docs.sqlalchemy.org/en/20/orm/session_api.html#sqlalchemy.orm.sessionmaker
    """

    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()

        except Exception:
            await session.rollback()  # a'la Spring Boot @Transactional
            raise


DatabaseReadSession = Annotated[AsyncSession, Depends(get_db_read_session)]  # type alias
DatabaseWriteSession = Annotated[AsyncSession, Depends(get_db_write_session)]  # type alias
