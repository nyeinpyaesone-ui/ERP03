from fastapi import APIRouter
from fastapi.responses import JSONResponse
import httpx

from app.core.config import settings

router = APIRouter(tags=["health"])


@router.get("/healthz", summary="Liveness probe")
async def healthz() -> dict[str, str]:
    return {"status": "ok", "service": "erp03-api", "version": settings.version}


@router.get("/readyz", summary="Readiness probe")
async def readyz() -> JSONResponse:
    try:
        async with httpx.AsyncClient(timeout=settings.ollama_timeout_seconds) as client:
            response = await client.get(f"{settings.ollama_base_url.rstrip('/')}/api/tags")
            response.raise_for_status()
    except (httpx.HTTPError, ValueError) as exc:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "service": "erp03-api", "dependency": "ollama", "error": type(exc).__name__},
        )
    return JSONResponse(status_code=200, content={"status": "ready", "service": "erp03-api"})
