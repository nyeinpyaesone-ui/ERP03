"""
Enterprise Resource Planning System - Main Application Entry Point

This module initializes the FastAPI application with:
- Database setup and migrations
- Router registration for all API endpoints
- Middleware for observability, CORS, and error handling
- Prometheus metrics endpoints
"""
import json
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from time import perf_counter
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from app.database import engine, Base
from app.routers import (
    auth, crm, hr, inventory, finance, projects,
    documents, reports, workflows, payments,
    integrations, integration_v1, analytics, admin, websocket, health
)
from app.config import settings
from app.integration_runtime import models as integration_runtime_models  # noqa: F401
from app.middleware.error_handler import register_exception_handlers


IS_TEST_MODE = os.getenv("TESTING", "false").lower() == "true" or os.getenv("TEST_MODE", "false").lower() == "true"


class JsonFormatter(logging.Formatter):
    """Custom JSON log formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON with optional request context."""
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

# Prometheus metrics
HTTP_REQUESTS = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"]
)
HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"]
)


class JsonFormatter(logging.Formatter):
    """Custom JSON log formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON with optional request context."""
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


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan manager for startup/shutdown events."""
    if not IS_TEST_MODE:
        Base.metadata.create_all(bind=engine)
    yield


def create_app() -> FastAPI:
    """Application factory for creating the FastAPI instance."""
    app = FastAPI(
        title=settings.APP_NAME,
        description="Enterprise Resource Planning system of record",
        version=settings.APP_VERSION,
        lifespan=lifespan,
    )

    # Add middleware
    _add_middleware(app)

    # Register routers
    _register_routers(app)

    # Register exception handlers
    register_exception_handlers(app)

    # Register additional routes
    _register_routes(app)

    return app


def _add_middleware(app: FastAPI) -> None:
    """Add middleware to the application."""
    # Observability middleware
    @app.middleware("http")
    async def observability_middleware(request: Request, call_next):
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
                extra={"request_id": request_id, "method": request.method, "path": request.url.path}
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
                    "duration_ms": round(duration * 1000, 2)
                }
            )

    # CORS middleware
    cors_origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def _register_routers(app: FastAPI) -> None:
    """Register all API routers."""
    router_config = [
        (auth.router, "/api/v1/auth", "Authentication"),
        (crm.router, "/api/v1/crm", "CRM"),
        (hr.router, "/api/v1/hr", "HR"),
        (inventory.router, "/api/v1/inventory", "Inventory"),
        (finance.router, "/api/v1/finance", "Finance"),
        (projects.router, "/api/v1/projects", "Projects"),
        (documents.router, "/api/v1/documents", "Documents"),
        (reports.router, "/api/v1/reports", "Reports"),
        (workflows.router, "/api/v1/workflows", "Workflows"),
        (payments.router, "/api/v1/payments", "Payments"),
        (integrations.router, "/api/v1/integrations", "Integrations"),
        (integration_v1.router, None, None),  # No prefix/tags for v1 integration
        (analytics.router, "/api/v1/analytics", "Analytics"),
        (admin.router, "/api/v1/admin", "Admin"),
        (websocket.router, "/api/v1/ws", "WebSocket"),
        (health.router, "/api/v1", "Health Checks"),
    ]

    for router, prefix, tags in router_config:
        if prefix and tags:
            app.include_router(router, prefix=prefix, tags=[tags])
        else:
            app.include_router(router)


def _register_routes(app: FastAPI) -> None:
    """Register additional application routes."""

    @app.get("/")
    async def root():
        return {
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
                "Versioned ERP-AI Integration",
            ],
        }

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "erp-backend"}

    @app.get("/metrics", include_in_schema=False)
    async def metrics():
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# Create application instance
app = create_app()
