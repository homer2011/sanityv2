from fastapi import FastAPI

from sanity.exception_handlers import add_exception_handlers
from sanity.router import api_router

app = FastAPI(
    title="Sanity API",
    version="0.1.0",
)

app.include_router(api_router)

add_exception_handlers(app)
