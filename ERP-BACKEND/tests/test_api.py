import pytest
from fastapi.testclient import TestClient

from app.main import app


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
