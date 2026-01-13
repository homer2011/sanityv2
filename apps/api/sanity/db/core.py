from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from sanity.config import settings

# Create async database engine (connection factory)
engine = create_async_engine(
    settings.DB_URL,
    echo=True,
)

# Create async sessionmaker (session factory)
async_session_factory = async_sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Generate a new async db session scoped to a single request; consumed as a dependency
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
