"""Audit logging middleware.

Captures business operations for tamper-evident traceability. Logs are
written asynchronously (fire-and-forget) so they never block the request
path. The middleware extracts business context from JWT claims when
available.
"""

from __future__ import annotations

import time
from typing import Callable
from uuid import UUID

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.models.audit import AuditLog, AuditAction
from app.core.config import settings
from app.db.session import SessionFactory


# Paths that generate audit entries (method, path_pattern) -> action
AUDIT_ROUTES = {
    ("POST", "/api/v1/auth/login"): AuditAction.AUTH_LOGIN,
    ("POST", "/api/v1/auth/register"): AuditAction.AUTH_REGISTER,
    ("POST", "/api/v1/sales"): AuditAction.SALE_CREATE,
    ("POST", "/api/v1/products"): AuditAction.PRODUCT_CREATE,
    ("PUT", "/api/v1/products"): AuditAction.PRODUCT_UPDATE,
    ("DELETE", "/api/v1/products"): AuditAction.PRODUCT_DELETE,
    ("POST", "/api/v1/customers"): AuditAction.CUSTOMER_CREATE,
    ("PUT", "/api/v1/customers"): AuditAction.CUSTOMER_UPDATE,
}


def _extract_business_id(request: Request) -> UUID | None:
    """Best-effort extraction of business_id from JWT without verifying."""
    try:
        import jwt as pyjwt
        auth = request.headers.get("authorization", "")
        if auth.startswith("Bearer "):
            token = auth.split(" ", 1)[1]
            payload = pyjwt.decode(
                token,
                settings.secret_key.get_secret_value(),
                algorithms=["HS256"],
                options={"verify_exp": False, "verify_signature": False},
            )
            bid = payload.get("business_id")
            return UUID(bid) if bid else None
    except Exception:
        pass
    return None


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        started = time.time()
        response = await call_next(request)
        duration_ms = int((time.time() - started) * 1000)

        # Only audit state-changing requests that succeeded
        if request.method not in {"POST", "PUT", "PATCH", "DELETE"}:
            return response
        if response.status_code not in {200, 201, 202, 204}:
            return response

        action = AUDIT_ROUTES.get(
            (request.method, request.url.path),
            AuditAction.SYSTEM_CONFIG_CHANGE,
        )

        # Fire-and-forget audit write (non-blocking)
        import asyncio

        asyncio.create_task(
            self._write_audit(
                request=request,
                response=response,
                action=action,
                duration_ms=duration_ms,
            )
        )

        return response

    async def _write_audit(
        self,
        request: Request,
        response: Response,
        action: AuditAction,
        duration_ms: int,
    ) -> None:
        try:
            async with SessionFactory() as session:
                business_id = _extract_business_id(request)
                entry = AuditLog(
                    business_id=business_id,
                    action=action,
                    resource_type=request.url.path.strip("/").split("/")[-1] or "system",
                    request_id=request.headers.get("x-request-id"),
                    ip_address=request.client.host if request.client else None,
                    user_agent=request.headers.get("user-agent"),
                    metadata_json={
                        "method": request.method,
                        "path": request.url.path,
                        "status_code": response.status_code,
                        "duration_ms": duration_ms,
                    },
                )
                session.add(entry)
                await session.commit()
        except Exception:
            # Never let audit failures break the request path
            pass
