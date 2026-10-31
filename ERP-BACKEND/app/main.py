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

import redis.asyncio as redis
from fastapi import FastAPI, Request, status
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


class RedisRateLimitMiddleware:
    """Redis-backed sliding window rate limiter.

    Uses Redis sorted sets for distributed rate limiting across workers.
    Honours ``X-Forwarded-For`` only when the immediate peer is in
    ``trusted_proxies`` (prevents spoofing).
    """

    def __init__(
        self,
        app,
        redis_url: str,
        requests_per_window: int = 100,
        window_seconds: int = 60,
        trusted_proxies: set[str] | None = None,
    ):
        self.app = app
        self.requests_per_window = requests_per_window
        self.window_seconds = window_seconds
        self.trusted_proxies = trusted_proxies or set()

        # Handle fakeredis URL scheme for tests
        if redis_url.startswith("fakeredis://"):
            import fakeredis.aioredis

            self.redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
        else:
            self.redis = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Get client IP, honouring X-Forwarded-For only from trusted peers.
        peer_ip = scope.get("client", ("unknown", 0))[0] or "unknown"
        client_ip = peer_ip
        if peer_ip in self.trusted_proxies:
            headers = dict(scope.get("headers", []))
            forwarded = headers.get(b"x-forwarded-for", b"").decode().strip()
            if forwarded:
                client_ip = forwarded.split(",")[0].strip() or peer_ip

        now = time.time()
        key = f"ratelimit:{client_ip}"

        # Sliding window using Redis sorted set
        pipe = await self.redis.pipeline()
        await pipe.zremrangebyscore(key, 0, now - self.window_seconds)
        await pipe.zcard(key)
        await pipe.zadd(key, {str(now): now})
        await pipe.expire(key, self.window_seconds)
        results = await pipe.execute()

        current_count = results[1]

        # Check rate limit
        if current_count >= self.requests_per_window:
            response = JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded"},
                headers={"Retry-After": str(self.window_seconds)},
            )
            await response(scope, receive, send)
            return

        # Record request
        await self.redis.zadd(f"ratelimit:{client_ip}", {str(time.time()): time.time()})
        await self.redis.expire(f"ratelimit:{client_ip}", self.window_seconds)

        await self.app(scope, receive, send)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Bind TypeSafe client lifecycle to the app.

    ``close()`` is guaranteed to run on shutdown so the SDK's HTTP client
    and any buffered judgments are flushed cleanly.
    """
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

# Rate limiting middleware (respects settings.rate_limit_enabled)
if settings.rate_limit_enabled:
    app.add_middleware(
        RedisRateLimitMiddleware,
        redis_url=settings.redis_url or "redis://localhost:6379/0",
        requests_per_window=settings.rate_limit_requests,
        window_seconds=settings.rate_limit_window,
        trusted_proxies={ip.strip() for ip in settings.trusted_proxies.split(",") if ip.strip()},
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
