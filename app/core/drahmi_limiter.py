"""Limits concurrent outbound calls to the Drahmi API."""

from __future__ import annotations

import asyncio

from app.settings import Settings, get_settings

_installed: asyncio.Semaphore | None = None


def build_drahmi_semaphore(settings: Settings | None = None) -> asyncio.Semaphore:
    settings = settings or get_settings()
    return asyncio.Semaphore(max(1, settings.drahmi_max_concurrent))


def get_drahmi_semaphore() -> asyncio.Semaphore:
    if _installed is not None:
        return _installed
    return build_drahmi_semaphore()


def install_drahmi_semaphore(semaphore: asyncio.Semaphore) -> None:
    global _installed
    _installed = semaphore


def clear_drahmi_semaphore() -> None:
    global _installed
    _installed = None
