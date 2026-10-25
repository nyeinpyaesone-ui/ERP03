import pytest
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    return TestClient(app)


def test_api_root(client):
    response = client.get("/api/v1")
    assert response.status_code == 200
    assert response.json()["service"] == "erp03"


def test_healthz(client):
    response = client.get("/api/v1/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.headers["X-Request-ID"]


def test_unknown_route_is_404(client):
    response = client.get("/api/v1/does-not-exist")
    assert response.status_code == 404


def test_metrics_requires_authentication(client):
    """Without a bearer token, /metrics must return 401."""
    response = client.get("/metrics")
    assert response.status_code == 401
    assert "Authentication required" in response.json()["detail"]


def test_metrics_rejects_invalid_bearer_token(client):
    """An invalid bearer token must not grant access to /metrics."""
    response = client.get(
        "/metrics",
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert response.status_code == 401
    assert "Invalid or expired access token" in response.json()["detail"]
