"""FastAPI application entry point."""

from fastapi import FastAPI

from app.config import SERVICE_NAME, SERVICE_VERSION
from app.routes.health import router as health_router


app = FastAPI(
    title=SERVICE_NAME,
    version=SERVICE_VERSION,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)
app.include_router(health_router)
