from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from sanity.common.utils import utc_now
from sanity.exceptions import SanityException


def utc_now_z():
    return utc_now().isoformat().replace("+00:00", "Z")


async def sanity_exception_handler(request: Request, ex: SanityException) -> JSONResponse:
    return JSONResponse(
        status_code=ex.status_code,
        content={
            "timestamp": utc_now_z(),
            "code": ex.status_code,
            "message": ex.message,
            "path": request.url.path,
        },
    )


async def unhandled_exception_handler(request: Request, ex: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "timestamp": utc_now_z(),
            "code": 500,
            "message": "something unexpected went wrong",
            "path": request.url.path,
        },
    )


def add_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(
        SanityException,
        sanity_exception_handler,  # type: ignore
    )

    app.add_exception_handler(
        Exception,
        unhandled_exception_handler,  # type: ignore
    )
