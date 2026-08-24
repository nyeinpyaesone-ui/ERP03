"""
Unit tests for the main application module (app/main.py).

Covers the application factory (create_app), route/middleware registration,
the observability middleware, CORS configuration, the lifespan handler, and
the structured JSON log formatter.
"""
import json
import logging
import sys
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.config import settings
from app.main import (
    JsonFormatter,
    IS_TEST_MODE,
    lifespan,
    create_app,
    app as main_app,
)


class TestJsonFormatter:
    """Tests for the JsonFormatter logging formatter."""

    def _make_record(self, level=logging.INFO, msg="Test message", exc_info=None):
        return logging.LogRecord(
            name="test.logger",
            level=level,
            pathname=__file__,
            lineno=42,
            msg=msg,
            args=(),
            exc_info=exc_info,
        )

    def test_format_returns_valid_json(self):
        """format() should return a JSON-encoded string."""
        formatter = JsonFormatter()
        record = self._make_record()

        result = formatter.format(record)
        data = json.loads(result)

        assert data["level"] == "INFO"
        assert data["logger"] == "test.logger"
        assert data["message"] == "Test message"
        assert "timestamp" in data

    def test_format_omits_missing_optional_fields(self):
        """Optional context fields should not appear when not set on the record."""
        formatter = JsonFormatter()
        record = self._make_record()

        data = json.loads(formatter.format(record))

        for key in ("request_id", "method", "path", "status", "duration_ms"):
            assert key not in data

    def test_format_includes_request_context_when_present(self):
        """Optional context fields should be included when set on the record."""
        formatter = JsonFormatter()
        record = self._make_record(msg="HTTP request")
        record.request_id = "req-123"
        record.method = "GET"
        record.path = "/health"
        record.status = 200
        record.duration_ms = 12.34

        data = json.loads(formatter.format(record))

        assert data["request_id"] == "req-123"
        assert data["method"] == "GET"
        assert data["path"] == "/health"
        assert data["status"] == 200
        assert data["duration_ms"] == 12.34

    def test_format_includes_exception_traceback(self):
        """When exc_info is present, a formatted exception string should be included."""
        formatter = JsonFormatter()
        try:
            raise ValueError("boom")
        except ValueError:
            exc_info = sys.exc_info()
        record = self._make_record(level=logging.ERROR, msg="Error occurred", exc_info=exc_info)

        data = json.loads(formatter.format(record))

        assert "exception" in data
        assert "ValueError" in data["exception"]
        assert "boom" in data["exception"]

    def test_format_zero_status_is_included(self):
        """A falsy-but-not-None value like status=0 should still be serialized."""
        formatter = JsonFormatter()
        record = self._make_record()
        record.status = 0

        data = json.loads(formatter.format(record))

        assert data["status"] == 0


class TestLifespan:
    """Tests for the application lifespan context manager."""

    @pytest.mark.asyncio
    async def test_lifespan_skips_create_all_in_test_mode(self):
        """In test mode, Base.metadata.create_all should not be invoked."""
        assert IS_TEST_MODE is True
        with patch('app.main.Base') as mock_base:
            async with lifespan(main_app):
                pass
            mock_base.metadata.create_all.assert_not_called()

    @pytest.mark.asyncio
    async def test_lifespan_creates_tables_when_not_test_mode(self):
        """Outside of test mode, tables should be created against the configured engine."""
        with patch('app.main.IS_TEST_MODE', False), \
             patch('app.main.Base') as mock_base, \
             patch('app.main.engine') as mock_engine:
            async with lifespan(main_app):
                pass
            mock_base.metadata.create_all.assert_called_once_with(bind=mock_engine)


class TestCreateApp:
    """Tests for the create_app application factory."""

    def test_create_app_returns_fastapi_instance(self):
        """create_app should build a FastAPI app with settings-derived metadata."""
        app = create_app()

        assert isinstance(app, FastAPI)
        assert app.title == settings.APP_NAME
        assert app.version == settings.APP_VERSION
        assert app.description == "Enterprise Resource Planning system of record"

    def test_create_app_registers_expected_router_prefixes(self):
        """All configured routers should be mounted under their expected prefixes."""
        app = create_app()
        paths = [route.path for route in app.routes]

        expected_prefixes = [
            "/api/v1/auth",
            "/api/v1/crm",
            "/api/v1/hr",
            "/api/v1/inventory",
            "/api/v1/finance",
            "/api/v1/projects",
            "/api/v1/documents",
            "/api/v1/reports",
            "/api/v1/workflows",
            "/api/v1/payments",
            "/api/v1/integrations",
            "/api/v1/analytics",
            "/api/v1/admin",
            "/api/v1/ws",
        ]
        for prefix in expected_prefixes:
            assert any(p.startswith(prefix) for p in paths), f"No route found for prefix {prefix}"

    def test_create_app_registers_root_health_and_metrics_routes(self):
        """The factory should register the root, health, and metrics endpoints."""
        app = create_app()
        paths = {route.path for route in app.routes}

        assert "/" in paths
        assert "/health" in paths
        assert "/metrics" in paths

    def test_create_app_produces_independent_instances(self):
        """Calling create_app twice should yield two distinct FastAPI app objects."""
        app1 = create_app()
        app2 = create_app()
        assert app1 is not app2


class TestRootRoutes:
    """Tests for the root, health, and metrics endpoints via the module-level app."""

    def test_root_endpoint_payload(self):
        with TestClient(main_app) as client:
            response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == settings.APP_NAME
        assert data["version"] == settings.APP_VERSION
        assert data["status"] == "running"
        assert data["ai_boundary"] == "external"
        assert isinstance(data["features"], list)
        assert len(data["features"]) > 0

    def test_health_endpoint_payload(self):
        with TestClient(main_app) as client:
            response = client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "healthy", "service": "erp-backend"}

    def test_metrics_endpoint_returns_prometheus_text(self):
        with TestClient(main_app) as client:
            response = client.get("/metrics")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/plain")

    def test_metrics_endpoint_excluded_from_openapi_schema(self):
        schema = main_app.openapi()
        assert "/metrics" not in schema.get("paths", {})


class TestObservabilityMiddleware:
    """Tests for the request-id / metrics observability middleware."""

    def test_response_includes_generated_request_id(self):
        with TestClient(main_app) as client:
            response = client.get("/health")

        assert "x-request-id" in response.headers
        assert len(response.headers["x-request-id"]) > 0

    def test_client_supplied_request_id_is_echoed(self):
        with TestClient(main_app) as client:
            response = client.get("/health", headers={"X-Request-ID": "custom-request-id"})

        assert response.headers["x-request-id"] == "custom-request-id"

    def test_different_requests_get_different_generated_ids(self):
        with TestClient(main_app) as client:
            response1 = client.get("/health")
            response2 = client.get("/health")

        assert response1.headers["x-request-id"] != response2.headers["x-request-id"]


class TestCORSConfiguration:
    """Tests for the CORS middleware configuration derived from settings."""

    def test_configured_origin_is_allowed(self):
        origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
        assert origins, "Expected at least one configured CORS origin"
        origin = origins[0]

        with TestClient(main_app) as client:
            response = client.get("/health", headers={"Origin": origin})

        assert response.headers.get("access-control-allow-origin") == origin

    def test_unconfigured_origin_is_not_reflected(self):
        with TestClient(main_app) as client:
            response = client.get("/health", headers={"Origin": "https://not-allowed.example.com"})

        assert response.headers.get("access-control-allow-origin") is None