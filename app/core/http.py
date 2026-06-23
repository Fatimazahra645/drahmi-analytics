"""Process-wide HTTP connection pool for outbound API calls."""

from __future__ import annotations

import httpx

from app.settings import Settings, get_settings

_installed: httpx.AsyncClient | None = None


def build_http_client(settings: Settings | None = None) -> httpx.AsyncClient:
    settings = settings or get_settings()
    return httpx.AsyncClient(
        timeout=httpx.Timeout(settings.drahmi_timeout_seconds),
        follow_redirects=True,
    )


def get_http_client() -> httpx.AsyncClient:
    if _installed is not None:
        return _installed
    return build_http_client()


def install_http_client(client: httpx.AsyncClient) -> None:
    global _installed
    _installed = client


async def shutdown_http_client() -> None:
    global _installed
    client = _installed
    _installed = None
    if client is not None:
        await client.aclose()
