"""Browser-facing proxy to Drahmi — uses the same client as eco-ai."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, Response

from app.integrations.drahmi.client import get_drahmi_client
from app.integrations.drahmi.exceptions import DrahmiApiError, DrahmiError
from app.settings import get_settings

router = APIRouter(tags=["drahmi"])


@router.api_route("/{path:path}", methods=["GET"])
async def proxy_drahmi(path: str, request: Request) -> Response:
    settings = get_settings()
    if not settings.drahmi_api_key:
        raise HTTPException(
            status_code=503,
            detail="DRAHMI_API_KEY is not configured. Set it in .env and restart the server.",
        )

    client = get_drahmi_client()
    try:
        upstream = await client.proxy_get(
            path,
            params=list(request.query_params.multi_items()),
        )
    except DrahmiApiError as exc:
        status = 504 if "timed out" in str(exc).lower() else 502
        raise HTTPException(status_code=status, detail=str(exc)) from exc
    except DrahmiError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return Response(
        content=upstream.content,
        status_code=upstream.status_code,
        media_type=upstream.headers.get("content-type", "application/json"),
    )
