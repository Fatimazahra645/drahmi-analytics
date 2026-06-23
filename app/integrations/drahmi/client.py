"""HTTP client for the Drahmi market data API (same contract as eco-ai)."""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Any
from urllib.parse import urlencode

import httpx

from app.core.drahmi_limiter import get_drahmi_semaphore
from app.core.http import get_http_client
from app.integrations.drahmi.cache import get_cached, set_cached
from app.integrations.drahmi.exceptions import DrahmiApiError, DrahmiError
from app.settings import Settings, get_settings

_TICKER_RE = re.compile(r"^[A-Z0-9][A-Z0-9._-]{0,11}$")
_API_PREFIX = "/api/v1"
_DEFAULT_BASE_URL = "https://api.drahmi.app"


def normalize_ticker(symbol: str) -> str:
    ticker = (symbol or "").strip().upper()
    if not _TICKER_RE.fullmatch(ticker):
        raise DrahmiError(
            f"Invalid stock ticker '{symbol}'. Use an uppercase symbol like ATW or BCP."
        )
    return ticker


class DrahmiClient:
    """Thin async wrapper around Drahmi REST endpoints."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = _DEFAULT_BASE_URL,
        timeout_seconds: float = 30.0,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        if not api_key:
            raise DrahmiError(
                "DRAHMI_API_KEY is required. Set it in .env to use market data."
            )
        self._base_url = base_url.rstrip("/")
        self._headers = {"X-API-Key": api_key, "Accept": "application/json"}
        self._timeout = httpx.Timeout(timeout_seconds)
        self._http = http_client or get_http_client()

    async def list_stocks(self, *, limit: int = 100) -> Any:
        if limit < 1 or limit > 500:
            raise DrahmiError("limit must be between 1 and 500.")
        return await self._get("/api/v1/stocks", params={"limit": limit})

    async def get_stock_history(self, symbol: str, *, range: str = "1M") -> Any:
        return await self._get(
            f"/api/v1/stocks/{normalize_ticker(symbol)}/history",
            params={"range": range},
        )

    async def get_dividends(self, symbol: str) -> Any:
        return await self._get(f"/api/v1/stocks/{normalize_ticker(symbol)}/dividends")

    async def get_technicals(self, symbol: str, *, range: str = "3M") -> Any:
        return await self._get(
            f"/api/v1/intelligence/stocks/{normalize_ticker(symbol)}/technicals",
            params={"range": range},
        )

    async def get_risk(
        self,
        symbol: str,
        *,
        range: str = "6M",
        benchmark: str = "MASI",
    ) -> Any:
        return await self._get(
            f"/api/v1/intelligence/stocks/{normalize_ticker(symbol)}/risk",
            params={"range": range, "benchmark": benchmark.strip().upper()},
        )

    async def get_liquidity(self, symbol: str) -> Any:
        return await self._get(
            f"/api/v1/intelligence/stocks/{normalize_ticker(symbol)}/liquidity",
        )

    async def get_signals(self, symbol: str) -> Any:
        return await self._get(
            f"/api/v1/intelligence/stocks/{normalize_ticker(symbol)}/signals",
        )

    async def proxy_get(
        self,
        path: str,
        *,
        params: list[tuple[str, str]] | None = None,
    ) -> httpx.Response:
        """Pass-through GET for browser proxy — returns raw upstream response."""
        cached = get_cached(path, params)
        if cached is not None:
            return cached

        url = f"{self._base_url}{_API_PREFIX}/{path.lstrip('/')}"
        try:
            async with get_drahmi_semaphore():
                response = await self._http.get(
                    url,
                    params=params or None,
                    headers=self._headers,
                    timeout=self._timeout,
                )
        except httpx.TimeoutException as exc:
            raise DrahmiApiError("Drahmi API request timed out.") from exc
        except httpx.HTTPError as exc:
            raise DrahmiApiError(f"Drahmi API request failed: {exc}") from exc

        set_cached(path, params, response)
        return response

    async def _get(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        url = f"{self._base_url}{path}"
        try:
            response = await self._http.get(
                url,
                params=params or None,
                headers=self._headers,
                timeout=self._timeout,
            )
        except httpx.TimeoutException as exc:
            raise DrahmiApiError("Drahmi API request timed out.") from exc
        except httpx.HTTPError as exc:
            raise DrahmiApiError(f"Drahmi API request failed: {exc}") from exc

        if response.status_code >= 400:
            detail = _extract_error_detail(response)
            raise DrahmiApiError(
                f"Drahmi API error {response.status_code} for {path}?{urlencode(params or {})}: {detail}",
                status_code=response.status_code,
            )

        if not response.content:
            return {}
        try:
            return response.json()
        except ValueError as exc:
            raise DrahmiApiError("Drahmi API returned non-JSON response.") from exc


def _extract_error_detail(response: httpx.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        text = response.text.strip()
        return text[:500] if text else response.reason_phrase
    if isinstance(body, dict):
        for key in ("message", "detail", "error"):
            if key in body:
                return str(body[key])
        return str(body)[:500]
    return str(body)[:500]


def create_drahmi_client(settings: Settings | None = None) -> DrahmiClient:
    settings = settings or get_settings()
    return DrahmiClient(
        api_key=settings.drahmi_api_key,
        base_url=settings.drahmi_base_url,
        timeout_seconds=settings.drahmi_timeout_seconds,
    )


@lru_cache
def get_drahmi_client() -> DrahmiClient:
    return create_drahmi_client()
