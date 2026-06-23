"""ponytail: assert-based check — proxy paths map to eco-ai /api/v1 routes."""

from app.integrations.drahmi.client import _API_PREFIX


def _upstream(path: str) -> str:
    return f"{_API_PREFIX}/{path.lstrip('/')}"


assert _upstream("stocks") == "/api/v1/stocks"
assert _upstream("stocks/ATW/history") == "/api/v1/stocks/ATW/history"
assert _upstream("intelligence/stocks/ATW/risk") == "/api/v1/intelligence/stocks/ATW/risk"
