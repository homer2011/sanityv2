from fastapi import APIRouter
from sqlalchemy import select

from sanity.db.deps import DatabaseSession
from sanity.errors.exceptions import ServiceUnavailable
from sanity.errors.schemas import ServiceUnavailableResponse

router = APIRouter(prefix="/health")


@router.get("", responses={503: ServiceUnavailableResponse})
async def health_check(
    session: DatabaseSession,
) -> dict[str, str]:
    try:
        await session.execute(select(1))
    except Exception as ex:
        raise ServiceUnavailable("Postgres database unavailable") from ex

    return {"status": "OK"}
