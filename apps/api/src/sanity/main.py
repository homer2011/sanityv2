from fastapi import FastAPI

from src.sanity.router import api_router

app = FastAPI(
    title="Sanity API",
    version="0.1.0",
)

app.include_router(api_router)
