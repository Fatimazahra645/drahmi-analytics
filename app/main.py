"""FastAPI app: static dashboard + Drahmi API proxy."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.drahmi_limiter import build_drahmi_semaphore, clear_drahmi_semaphore, install_drahmi_semaphore
from app.core.http import build_http_client, install_http_client, shutdown_http_client
from app.integrations.drahmi.client import get_drahmi_client
from app.routes.drahmi import router as drahmi_router
from app.settings import get_settings

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    install_http_client(build_http_client(settings))
    install_drahmi_semaphore(build_drahmi_semaphore(settings))
    get_drahmi_client.cache_clear()
    try:
        yield
    finally:
        get_drahmi_client.cache_clear()
        clear_drahmi_semaphore()
        await shutdown_http_client()


def create_app() -> FastAPI:
    app = FastAPI(title="Drahmi BVC Dashboard", version="1.0.0", lifespan=lifespan)

    app.include_router(drahmi_router, prefix="/api/drahmi")
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

    return app


app = create_app()


def run() -> None:
    import uvicorn

    settings = get_settings()
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)
