from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from sanity.db.core import async_session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Generates a new async db session scoped to a single request; consumed as a dependency
    within a service layer.

    docs: https://docs.sqlalchemy.org/en/20/orm/session_api.html#sqlalchemy.orm.sessionmaker
    """

    async with async_session_factory() as session:
        try:
            yield session

        except Exception:
            await session.rollback()  # a'la Spring Boot @Transactional
            raise

        finally:
            await session.close()


DatabaseSession = Annotated[AsyncSession, Depends(get_db_session)]  # type alias
