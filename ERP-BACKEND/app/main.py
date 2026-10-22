"""ERP03 FastAPI application with TypeSafe System One judgment integration.

Code owns the workflow; TypeSafe supplies programmable common sense:
- Error classification drives retry-after headers (code decision, model annotation).
- Transaction risk scoring gates high-risk sales (code decision, model annotation).
- TypeSafe client lifecycle is bound to the app lifespan.
"""

import logging
import time
from contextlib import asynccontextmanager
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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Bind TypeSafe client lifecycle to the app.

    ``close()`` is guaranteed to run on shutdown so the SDK's HTTP client
    and any buffered judgments are flushed cleanly.

    OpenTelemetry tracing/metrics are initialized on startup when
    ``settings.telemetry_enabled`` is true, exporting to
    ``settings.otlp_endpoint``.
    """
    if settings.telemetry_enabled:
        try:
            from app.core.telemetry import init_telemetry, instrument_app
        except ImportError as exc:
            raise RuntimeError(
                "telemetry_enabled=true but opentelemetry is not installed; "
                "install the opentelemetry extras or set TELEMETRY_ENABLED=false"
            ) from exc
        init_telemetry(
            service_name=settings.app_name.lower().replace(" ", "-"),
            otlp_endpoint=settings.otlp_endpoint,
        )
        instrument_app(app)
    yield
    if settings.typesafe_enabled:
        await typesafe.close()


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Map typed domain errors to the stable error envelope exactly once.

    TypeSafe classification is non-blocking: if it is unavailable or slow,
    the HTTP error is still returned. When available and confident,
    ``Retry-After`` is derived from the classification (code-owned decision).
    """
    request_id = request.headers.get("X-Request-ID") or uuid4().hex
    headers = {"X-Request-ID": request_id}

    classification = None
    if settings.typesafe_enabled:
        classification = await typesafe.classify_error(
            error_code=exc.code,
            error_message=exc.message,
            endpoint=str(request.url.path),
            method=request.method,
            request_id=request_id,
        )
        if classification is not None:
            # Confidence gates acting on the judgment.
            if classification.confidence < 0.40:
                logger.warning(
                    "Low-confidence error classification request_id=%s "
                    "selected=%s confidence=%.2f escalate=True",
                    request_id,
                    classification.selected,
                    classification.confidence,
                )
            if classification.is_retryable and classification.retry_after_seconds is not None:
                headers["Retry-After"] = str(classification.retry_after_seconds)

    return JSONResponse(
        status_code=exc.status_code,
        headers=headers,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "request_id": request_id,
                "typesafe": (
                    {
                        "selected": classification.selected,
                        "probability": classification.probability,
                        "confidence": classification.confidence,
                        "escalate": classification.escalate,
                    }
                    if classification is not None
                    else None
                ),
            },
        },
    )


app.mount("/metrics", metrics_app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Request-ID",
        "X-Idempotency-Key",
        "Retry-After",
    ],
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
            headers={"X-Request-ID": request_id},
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
