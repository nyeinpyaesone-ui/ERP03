"""
Unit tests for AuthRateLimitMiddleware (app/middleware/rate_limiter.py).
"""
from unittest.mock import patch

import pytest
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from app.middleware.rate_limiter import AuthRateLimitMiddleware


async def _ok_endpoint(request):
    """Simple Starlette endpoint used to exercise the middleware."""
    return JSONResponse({"ok": True})


def _build_app(requests_per_minute=10, auth_path="/api/auth/login"):
    """Build a minimal Starlette app protected by AuthRateLimitMiddleware."""
    routes = [
        Route(auth_path, _ok_endpoint, methods=["GET", "POST"]),
        Route("/api/other", _ok_endpoint, methods=["GET"]),
    ]
    app = Starlette(routes=routes)
    app.add_middleware(AuthRateLimitMiddleware, requests_per_minute=requests_per_minute)
    return app


class TestAuthRateLimitMiddlewareConstruction:
    """Tests for middleware initialization."""

    def test_default_requests_per_minute(self):
        app = Starlette()
        middleware = AuthRateLimitMiddleware(app)
        assert middleware.requests_per_minute == 10
        assert middleware.request_history == {}

    def test_custom_requests_per_minute(self):
        app = Starlette()
        middleware = AuthRateLimitMiddleware(app, requests_per_minute=5)
        assert middleware.requests_per_minute == 5


class TestAuthRateLimitMiddlewareDispatch:
    """Tests for the dispatch behavior of AuthRateLimitMiddleware."""

    def test_non_auth_path_bypasses_rate_limiting(self):
        """Requests to non-auth paths should never be rate limited, regardless of volume."""
        app = _build_app(requests_per_minute=1)
        client = TestClient(app)

        for _ in range(5):
            response = client.get("/api/other")
            assert response.status_code == 200
            assert response.json() == {"ok": True}

    def test_auth_path_allows_requests_within_limit(self):
        """Requests up to the configured limit should succeed."""
        app = _build_app(requests_per_minute=3)
        client = TestClient(app)

        for _ in range(3):
            response = client.get("/api/auth/login")
            assert response.status_code == 200

    def test_auth_path_blocks_requests_exceeding_limit(self):
        """Requests beyond the configured limit should be rejected with 429."""
        app = _build_app(requests_per_minute=2)
        client = TestClient(app)

        assert client.get("/api/auth/login").status_code == 200
        assert client.get("/api/auth/login").status_code == 200
        blocked = client.get("/api/auth/login")

        assert blocked.status_code == 429
        assert "Too many authentication attempts" in blocked.json()["detail"]

    def test_zero_limit_blocks_first_request(self):
        """A limit of zero should reject every request to a protected path."""
        app = _build_app(requests_per_minute=0)
        client = TestClient(app)

        response = client.get("/api/auth/login")

        assert response.status_code == 429

    def test_post_requests_are_also_rate_limited(self):
        """The rate limit should apply regardless of HTTP method."""
        app = _build_app(requests_per_minute=1)
        client = TestClient(app)

        assert client.post("/api/auth/login").status_code == 200
        assert client.post("/api/auth/login").status_code == 429

    def test_sliding_window_expires_old_requests(self):
        """Requests older than the 60 second window should no longer count against the limit."""
        app = _build_app(requests_per_minute=1)
        client = TestClient(app)

        with patch('app.middleware.rate_limiter.time.time', return_value=1_000.0):
            assert client.get("/api/auth/login").status_code == 200

        with patch('app.middleware.rate_limiter.time.time', return_value=1_000.0):
            # Same instant, still within window -> limit exceeded
            assert client.get("/api/auth/login").status_code == 429

        with patch('app.middleware.rate_limiter.time.time', return_value=1_070.0):
            # 70 seconds later, outside the 60s window -> allowed again
            assert client.get("/api/auth/login").status_code == 200

    def test_path_prefix_match_is_exact_not_versioned(self):
        """
        Only paths starting with '/api/auth' are rate limited; the application's
        actual versioned prefix '/api/v1/auth' does not match this check.
        """
        app = _build_app(requests_per_minute=1, auth_path="/api/v1/auth/login")
        client = TestClient(app)

        for _ in range(5):
            response = client.get("/api/v1/auth/login")
            assert response.status_code == 200

    def test_rate_limit_state_persists_across_requests_from_same_client(self):
        """The middleware should track request counts cumulatively per client IP."""
        app = _build_app(requests_per_minute=2)
        client = TestClient(app)

        client.get("/api/auth/login")
        client.get("/api/other")  # unrelated path, should not consume the auth quota
        client.get("/api/auth/login")
        third = client.get("/api/auth/login")

        assert third.status_code == 429