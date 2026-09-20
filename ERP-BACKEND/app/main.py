import logging
import time
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.health import router as health_router
from app.core.config import settings

logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO), format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("erp03")

app = FastAPI(title=settings.app_name, version=settings.version, docs_url="/docs", redoc_url="/redoc")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or uuid4().hex
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("Unhandled request error request_id=%s path=%s", request_id, request.url.path)
        response = JSONResponse(status_code=500, content={"error": {"code": "INTERNAL_ERROR", "message": "Internal server error", "request_id": request_id}})
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    logger.info("request method=%s path=%s status=%s duration_ms=%.2f request_id=%s", request.method, request.url.path, response.status_code, (time.perf_counter() - started) * 1000, request_id)
    return response


@app.get("/api/v1", tags=["system"])
async def api_root() -> dict[str, str]:
    return {"service": "erp03", "status": "ready", "version": settings.version}


app.include_router(health_router, prefix="/api/v1")
