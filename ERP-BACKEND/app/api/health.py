from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.config import settings
from app.db.session import get_db_session

router = APIRouter(tags=["health"])


@router.get("/healthz", summary="Liveness probe")
async def healthz() -> dict[str, str]:
    return {"status": "ok", "service": "erp03-api", "version": settings.version}


@router.get("/readyz", summary="Transactional readiness probe")
async def readyz() -> JSONResponse:
    try:
        async for session in get_db_session():
            await session.execute(text("SELECT 1"))
    except Exception as exc:
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "service": "erp03-api",
                "dependency": "postgresql",
                "error": type(exc).__name__,
            },
        )

    return JSONResponse(
        status_code=200,
        content={"status": "ready", "service": "erp03-api", "ai_dependency": "optional"},
    )
