"""Prometheus metrics for ERP03 backend.

Adds database pool gauges so pool exhaustion is detectable at scrape time.
"""

from __future__ import annotations

from fastapi import status
from prometheus_client import Counter, Gauge, Histogram, make_asgi_app
from starlette.responses import JSONResponse

from app.core.security import decode_access_token

REQUEST_COUNT = Counter(
    "erp03_http_requests_total",
    "Total HTTP requests",
    ["method", "route", "status_code"],
)
REQUEST_LATENCY = Histogram(
    "erp03_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "route"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
)

# Task 4.1: Database pool gauges
DB_POOL_ACTIVE = Gauge(
    "erp03_db_pool_active_connections",
    "Number of actively used database connections in the pool",
)
DB_POOL_IDLE = Gauge(
    "erp03_db_pool_idle_connections",
    "Number of idle database connections in the pool",
)
DB_POOL_OVERFLOW = Gauge(
    "erp03_db_pool_overflow_connections",
    "Number of overflow database connections beyond pool size",
)


def _metrics_auth_middleware(app):
    """Wrap the Prometheus ASGI app so /metrics requires authentication."""

    async def middleware(scope, receive, send):
        if scope["type"] == "http":
            headers = dict(scope.get("headers", []))
            auth_header = headers.get(b"authorization", b"").decode()
            if not auth_header.startswith("Bearer "):
                response = JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Authentication required"},
                )
                await response(scope, receive, send)
                return
            token = auth_header.split(" ", 1)[1]
            try:
                decode_access_token(token)
            except Exception:
                response = JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid or expired access token"},
                )
                await response(scope, receive, send)
                return
        await app(scope, receive, send)

    return middleware


metrics_app = _metrics_auth_middleware(make_asgi_app())


def update_pool_metrics(pool) -> None:
    """Update DB pool gauges from a SQLAlchemy pool object."""
    try:
        DB_POOL_ACTIVE.set(pool.size() - pool.checkedin() if hasattr(pool, "size") else 0)
        DB_POOL_IDLE.set(pool.checkedin() if hasattr(pool, "checkedin") else 0)
        DB_POOL_OVERFLOW.set(pool.overflow() if hasattr(pool, "overflow") else 0)
    except Exception:
        pass
