from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from sanity.db.deps import AsyncSession, get_db_session

router = APIRouter(prefix="/health")


@router.get("")
async def health_check(
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, str]:
    try:
        await session.execute(select(1))
    except SQLAlchemyError as ex:
        raise HTTPException(status_code=503, detail="Postgres database is not available") from ex

    return {"status": "OK"}
