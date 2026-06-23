"""In-memory TTL cache for Drahmi proxy GET responses."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass

import httpx

STOCK_LIST_TTL_SECONDS = 15 * 60
HISTORY_TTL_SECONDS = 10 * 60
RISK_TTL_SECONDS = 10 * 60

_HISTORY_RE = re.compile(r"^stocks/[A-Z0-9][A-Z0-9._-]{0,11}/history$", re.I)
_RISK_RE = re.compile(r"^intelligence/stocks/[A-Z0-9][A-Z0-9._-]{0,11}/risk$", re.I)


@dataclass(frozen=True)
class _CacheKey:
    path: str
    params: tuple[tuple[str, str], ...]


@dataclass
class _CacheEntry:
    fetched_at: float
    status_code: int
    content: bytes
    media_type: str


_cache: dict[_CacheKey, _CacheEntry] = {}


def cache_ttl_seconds(path: str) -> float | None:
    normalized = path.strip("/")
    if normalized == "stocks":
        return STOCK_LIST_TTL_SECONDS
    if _HISTORY_RE.match(normalized):
        return HISTORY_TTL_SECONDS
    if _RISK_RE.match(normalized):
        return RISK_TTL_SECONDS
    return None


def _make_key(path: str, params: list[tuple[str, str]] | None) -> _CacheKey:
    return _CacheKey(path=path.strip("/"), params=tuple(sorted(params or ())))


def get_cached(path: str, params: list[tuple[str, str]] | None) -> httpx.Response | None:
    ttl = cache_ttl_seconds(path)
    if ttl is None:
        return None
    entry = _cache.get(_make_key(path, params))
    if entry is None:
        return None
    if time.monotonic() - entry.fetched_at >= ttl:
        del _cache[_make_key(path, params)]
        return None
    return httpx.Response(
        status_code=entry.status_code,
        content=entry.content,
        headers={"content-type": entry.media_type},
    )


def set_cached(path: str, params: list[tuple[str, str]] | None, response: httpx.Response) -> None:
    if cache_ttl_seconds(path) is None or response.status_code != 200:
        return
    _cache[_make_key(path, params)] = _CacheEntry(
        fetched_at=time.monotonic(),
        status_code=response.status_code,
        content=response.content,
        media_type=response.headers.get("content-type", "application/json"),
    )


def clear_cache() -> None:
    """Test helper — drop all cached proxy responses."""
    _cache.clear()
