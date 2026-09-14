import json
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from time import perf_counter

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from app.config import settings
from app.middleware.rate_limiter import RateLimiter, AuthRateLimitMiddleware
from app.middleware.error_handler import register_exception_handlers, error_handler_middleware

# Import plugin system
try:
    from app.plugins import setup_plugins, CORE_MODULES
    PLUGINS_AVAILABLE = True
except ImportError:
    PLUGINS_AVAILABLE = False
    CORE_MODULES = []

# Import domain modules (feat branch structure)
from app.domains.auth import auth, user
from app.domains.users import users
from app.domains.permissions import permissions
from app.domains.crm import crm
from app.domains.hr import hr
from app.domains.finance import finance
from app.domains.inventory import inventory
from app.domains.projects import projects
from app.domains.documents import documents
from app.domains.workflows import workflows
from app.domains.payments import payments
from app.domains.analytics import analytics
from app.domains.search import search
from app.domains.integrations import integrations
from app.domains.websocket import websocket
from app.domains.admin import admin
from app.domains.health import health

from app.routers import reports, integration_v1

try:
    from app.ai.assistant import build_router as build_ai_router
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False


class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created)),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key in ("request_id", "method", "path", "status", "duration_ms"):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


logger = logging.getLogger("erp03.api")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
logger.setLevel(logging.INFO)
logger.propagate = False

HTTP_REQUESTS = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)
HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle without mutating the database schema."""
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.APP_VERSION,
    description="ERP03 Production System with Plugin Architecture and Security Hardening",
    lifespan=lifespan,
)

rate_limiter = RateLimiter(default_limit="100/minute")
app.state.limiter = rate_limiter.limiter
rate_limiter.setup_exception_handler(app)
app.add_middleware(AuthRateLimitMiddleware, max_attempts=5, window_seconds=60)
register_exception_handlers(app)
app.middleware("http")(error_handler_middleware)


@app.middleware("http")
async def observability_middleware(request, call_next):
    """Track request metrics and attach a request identifier to the response."""
    start = perf_counter()
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        response.headers["X-Request-ID"] = request_id
        return response
    except Exception:
        logger.exception(
            "Unhandled request exception",
            extra={"request_id": request_id, "method": request.method, "path": request.url.path},
        )
        raise
    finally:
        duration = perf_counter() - start
        path = request.url.path
        HTTP_REQUESTS.labels(request.method, path, str(status_code)).inc()
        HTTP_REQUEST_DURATION.labels(request.method, path).observe(duration)
        logger.info(
            "HTTP request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": path,
                "status": status_code,
                "duration_ms": round(duration * 1000, 2),
            },
        )


cors_origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()] or ["http://localhost:3000", "http://localhost:8080"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With", "X-Request-ID"],
    expose_headers=["X-Request-ID", "Content-Length"],
    max_age=600,
)

if PLUGINS_AVAILABLE:
    app.state.core_modules = CORE_MODULES
    plugin_manager = setup_plugins(app)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(permissions.router, prefix="/api/v1/permissions", tags=["Permissions"])
app.include_router(crm.router, prefix="/api/v1/crm", tags=["CRM"])
app.include_router(hr.router, prefix="/api/v1/hr", tags=["HR"])
app.include_router(finance.router, prefix="/api/v1/finance", tags=["Finance"])
app.include_router(inventory.router, prefix="/api/v1/inventory", tags=["Inventory"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["Projects"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["Documents"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["Reports"])
app.include_router(workflows.router, prefix="/api/v1/workflows", tags=["Workflows"])
app.include_router(payments.router, prefix="/api/v1/payments", tags=["Payments"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(search.router, prefix="/api/v1/search", tags=["Search"])
app.include_router(integrations.router, prefix="/api/v1/integrations", tags=["Integrations"])
app.include_router(integration_v1.router, tags=["Integration v1"])
app.include_router(websocket.router, prefix="/api/v1/ws", tags=["WebSocket"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(health.router, prefix="/api/v1", tags=["Health"])

if AI_AVAILABLE:
    app.include_router(build_ai_router(), prefix="/api/v1/ai", tags=["AI Assistant"])


@app.get("/")
async def root():
    response = {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "system": "ERP System of Record",
        "ai_boundary": "external",
        "features": [
            "Core ERP (CRM, HR, Inventory, Finance, Projects)",
            "Document Management",
            "Reports & Analytics",
            "Workflow Automation",
            "Payments",
            "WebSocket Real-time",
            "PWA with Offline Support",
            "Bulk Import/Export",
            "Alembic Migrations",
        ],
    }
    if PLUGINS_AVAILABLE:
        response["core_modules"] = len(CORE_MODULES)
        response["plugins_enabled"] = True
    return response


@app.get("/")
async def root_duplicate_guard():
    # This route is replaced by the canonical root handler above if FastAPI detects duplicates.
    return {"status": "running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "erp-backend"}


@app.get("/metrics", include_in_schema=False)
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/api/v1/plugins")
async def list_plugins():
    """List all loaded plugins."""
    if PLUGINS_AVAILABLE:
        return {"plugins": plugin_manager.list_plugins()}
    return {"plugins": [], "message": "Plugin system not available"}
