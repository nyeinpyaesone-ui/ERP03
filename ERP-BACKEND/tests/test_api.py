from uuid import UUID, uuid4

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


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/context",
        "/api/v1/inventory/stock",
        "/api/v1/sales",
        "/api/v1/dashboard/summary",
    ],
)
def test_operational_read_models_require_authentication(client, path):
    response = client.get(path)
    assert response.status_code == 401


def test_unified_erp_onboarding_catalog_inventory_and_pos(client):
    suffix = uuid4().hex[:12]
    business_code = f"TEST-{suffix}"
    email = f"erp-{suffix}@example.com"

    registered = client.post(
        "/api/v1/auth/register",
        json={
            "business_code": business_code,
            "business_name": "Integration Test Shop",
            "email": email,
            "password": "LocalTestPass-123",
            "display_name": "Integration Owner",
            "default_currency": "MMK",
            "timezone": "Asia/Yangon",
            "locale": "my-MM",
        },
    )
    assert registered.status_code == 200, registered.text

    logged_in = client.post(
        "/api/v1/auth/login",
        json={
            "business_code": business_code,
            "email": email,
            "password": "LocalTestPass-123",
        },
    )
    assert logged_in.status_code == 200, logged_in.text
    headers = {"Authorization": f"Bearer {logged_in.json()['access_token']}"}

    context = client.get("/api/v1/context", headers=headers)
    assert context.status_code == 200, context.text
    branch = context.json()["branches"][0]
    warehouse = context.json()["warehouses"][0]
    assert branch["code"] == "MAIN"
    assert warehouse["code"] == "MAIN"

    product_response = client.post(
        "/api/v1/products",
        headers=headers,
        json={
            "branch_id": branch["id"],
            "sku": f"SKU-{suffix}",
            "name": "Myanmar Rice 5kg",
            "unit": "bag",
            "sale_price": "1200.00",
            "cost_price": "800.00",
            "min_stock": "2.000",
        },
    )
    assert product_response.status_code == 201, product_response.text
    product = product_response.json()

    customer_response = client.post(
        "/api/v1/customers",
        headers=headers,
        json={
            "branch_id": branch["id"],
            "code": f"CUS-{suffix}",
            "name": "Walk-in Customer",
            "phone": "09-00000000",
            "credit_limit": "50000.00",
        },
    )
    assert customer_response.status_code == 201, customer_response.text
    customer = customer_response.json()

    receipt = client.post(
        "/api/v1/purchases/receipts",
        headers=headers,
        json={
            "branch_id": branch["id"],
            "warehouse_id": warehouse["id"],
            "lines": [
                {
                    "product_id": product["id"],
                    "quantity": "10.000",
                    "unit_cost": "800.00",
                }
            ],
        },
    )
    assert receipt.status_code == 201, receipt.text

    stock = client.get("/api/v1/inventory/stock", headers=headers)
    assert stock.status_code == 200, stock.text
    assert stock.json()["items"][0]["quantity"] == "10.000"

    sale = client.post(
        "/api/v1/sales",
        headers={**headers, "X-Idempotency-Key": f"sale-{suffix}"},
        json={
            "branch_id": branch["id"],
            "warehouse_id": warehouse["id"],
            "customer_id": customer["id"],
            "currency": "MMK",
            "lines": [
                {
                    "product_id": product["id"],
                    "quantity": "2.000",
                    "unit_price": "1200.00",
                }
            ],
            "payments": [
                {"method": "cash", "amount": "1000.00", "currency": "MMK"}
            ],
        },
    )
    assert sale.status_code == 201, sale.text
    assert sale.json()["total"] == "2400.00"
    assert sale.json()["paid"] == "1000.00"
    assert sale.json()["balance"] == "1400.00"

    sales = client.get("/api/v1/sales?limit=10", headers=headers)
    assert sales.status_code == 200, sales.text
    assert sales.json()["total"] == 1
    assert sales.json()["items"][0]["customer_name"] == "Walk-in Customer"

    summary = client.get("/api/v1/dashboard/summary", headers=headers)
    assert summary.status_code == 200, summary.text
    assert summary.json()["currency"] == "MMK"
    assert summary.json()["orders_count"] == 1
    assert summary.json()["outstanding_balance"] == "1400.00"

    final_stock = client.get("/api/v1/inventory/stock", headers=headers)
    assert final_stock.status_code == 200, final_stock.text
    assert final_stock.json()["items"][0]["quantity"] == "8.000"
