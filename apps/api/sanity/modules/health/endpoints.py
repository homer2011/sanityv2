from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from sanity.db.deps import DatabaseSession

router = APIRouter(prefix="/health")


@router.get("")
async def health_check(
    session: DatabaseSession,
) -> dict[str, str]:
    try:
        await session.execute(select(1))
    except Exception as ex:
        raise HTTPException(status_code=503, detail="Postgres database is not available") from ex

    return {"status": "OK"}
