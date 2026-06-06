"""FastAPI application entry point."""

from __future__ import annotations

import uvicorn
from fastapi import FastAPI

from app.config import SERVICE_NAME, SERVICE_VERSION, get_settings
from app.routes.health import router as health_router


app = FastAPI(
    title=SERVICE_NAME,
    version=SERVICE_VERSION,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)
app.include_router(health_router)


def run() -> None:
    settings = get_settings()
    uvicorn.run(app, host=settings.app_host, port=settings.app_port)


if __name__ == "__main__":
    run()
