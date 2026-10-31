from uuid import UUID

import pytest
from app.core.security import create_access_token
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
    """METRICS-1: /metrics must not be served unauthenticated."""
    response = client.get("/metrics")
    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"


def test_metrics_rejects_invalid_token(client):
    response = client.get("/metrics", headers={"Authorization": "Bearer not-a-valid-token"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired access token"


def test_metrics_accepts_valid_token(client):
    token = create_access_token(
        user_id=UUID("12345678-1234-1234-1234-123456789abc"),
        business_id=UUID("12345678-1234-1234-1234-123456789abd"),
        branch_id=None,
        expires_minutes=30,
    )
    response = client.get("/metrics", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
