import logging
import time
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.auth import router as auth_router
from app.api.catalog import router as catalog_router
from app.api.health import router as health_router
from app.api.purchasing import router as purchasing_router
from app.api.sales import router as sales_router
from app.api.transactions import router as transactions_router
from app.core.config import settings
from app.core.errors import AppError
from app.core.metrics import REQUEST_COUNT, REQUEST_LATENCY, metrics_app
from app.core.typesafe import typesafe

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("erp03")

app = FastAPI(
    title=settings.app_name, version=settings.version, docs_url="/docs", redoc_url="/redoc"
)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Map typed domain errors to the stable error envelope exactly once."""
    request_id = request.headers.get("X-Request-ID") or uuid4().hex

    # Classify error via TypeSafe for retry/routing decisions (non-blocking).
    classification = None
    if settings.typesafe_enabled:
        classification = await typesafe.classify_error(
            error_code=exc.code,
            error_message=exc.message,
            endpoint=str(request.url.path),
            method=request.method,
            request_id=request_id,
        )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "request_id": request_id,
                "typesafe": classification,
            },
        },
    )


app.mount("/metrics", metrics_app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-Idempotency-Key"],
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or uuid4().hex
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            "Unhandled request error request_id=%s path=%s", request_id, request.url.path
        )
        response = JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Internal server error",
                    "request_id": request_id,
                }
            },
        )
    duration = time.perf_counter() - started
    route = request.scope.get("route")
    route_name = getattr(route, "path", request.url.path)
    REQUEST_COUNT.labels(request.method, route_name, str(response.status_code)).inc()
    REQUEST_LATENCY.labels(request.method, route_name).observe(duration)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    logger.info(
        "request method=%s path=%s status=%s duration_ms=%.2f request_id=%s",
        request.method,
        request.url.path,
        response.status_code,
        duration * 1000,
        request_id,
    )
    return response


@app.get("/api/v1", tags=["system"])
async def api_root() -> dict[str, str]:
    return {"service": "erp03", "status": "ready", "version": settings.version}


app.include_router(health_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(sales_router, prefix="/api/v1")
app.include_router(catalog_router, prefix="/api/v1")
app.include_router(purchasing_router, prefix="/api/v1")
app.include_router(transactions_router, prefix="/api/v1")
