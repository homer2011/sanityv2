from fastapi import APIRouter
from sqlalchemy import select

from sanity.db.deps import DatabaseReadSession
from sanity.errors.exceptions import ServiceUnavailable
from sanity.errors.schemas import ServiceUnavailableResponse

router = APIRouter(prefix="/health", tags=["Health Check"])


@router.get("", responses={503: ServiceUnavailableResponse})
async def health_check(
    db_session: DatabaseReadSession,
) -> dict[str, str]:
    try:
        await db_session.execute(select(1))
    except Exception as ex:
        raise ServiceUnavailable("Postgres database unavailable") from ex

    return {"status": "OK"}
