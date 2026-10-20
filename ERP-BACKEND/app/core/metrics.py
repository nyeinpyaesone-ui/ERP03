from fastapi import status
from prometheus_client import Counter, Histogram, make_asgi_app
from starlette.responses import JSONResponse

from app.core.security import decode_access_token

REQUEST_COUNT = Counter(
    "erp03_http_requests_total",
    "Total HTTP requests handled by ERP03",
    ("method", "route", "status"),
)
REQUEST_LATENCY = Histogram(
    "erp03_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ("method", "route"),
)


def _metrics_auth_middleware(app):
    """Wrap the Prometheus ASGI app so /metrics requires authentication.

    Extracts the bearer token from the ASGI scope headers directly (without
    consuming the receive channel) and validates it before forwarding to the
    metrics app.
    """

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
