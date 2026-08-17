import httpx
import pytest
from fastapi.testclient import TestClient

from .app import app, erp, settings


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(settings, "service_token", "test-token")
    return TestClient(app)


def test_live(client):
    assert client.get("/health/live").json() == {"status": "alive"}


def test_ready_requires_service_token(client, monkeypatch):
    monkeypatch.setattr(settings, "service_token", "")
    assert client.get("/health/ready").status_code == 503


@pytest.mark.asyncio
async def test_adapter_uses_contract_only(monkeypatch):
    class Transport:
        async def request(self, method, url, **kwargs):
            assert method == "GET"
            assert url.endswith("/erp/purchase-orders/7")
            assert kwargs["headers"]["Authorization"] == "Bearer token"
            return httpx.Response(200, json={"id": 7, "po_number": "PO-7", "status": "APPROVED", "amount": 10, "currency_code": "USD"})
        async def aclose(self):
            pass

    from .config import RuntimeSettings
    from .erp_client import ErpClient
    result = await ErpClient(RuntimeSettings(service_token="token"), Transport()).get_purchase_order(7, "corr-1")
    assert result["id"] == 7


def test_command_schema_is_bounded(client):
    response = client.post(
        "/v1/commands",
        headers={"Idempotency-Key": "0123456789abcdef", "X-Correlation-ID": "corr-1"},
        json={"command_id": "550e8400-e29b-41d4-a716-446655440000", "command_type": "delete_database", "requested_by": "ai", "payload": {}},
    )
    assert response.status_code == 422
