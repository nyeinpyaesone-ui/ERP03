"""Authenticated transaction journal endpoint tests.

Tests the /api/v1/transactions endpoints through the FastAPI test client,
using the async PostgreSQL/SQLite-backed TransactionStore.
"""

import asyncio
from uuid import uuid4

import pytest
from app.core.security import current_claims
from app.db.session import SessionFactory, get_db_session  # noqa: F401
from app.main import app
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

pytestmark = (
    pytest.mark.requires_database
)  # durable SQLite journal under /tmp, no PostgreSQL needed


@pytest.fixture(autouse=True)
def authenticated_transaction_requests():
    app.dependency_overrides[current_claims] = lambda: {
        "sub": "test-user",
        "business_id": "test-business",
    }
    yield
    app.dependency_overrides.pop(current_claims, None)


def test_transaction_requires_idempotency_key():
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/transactions",
            json={"operation": "invoice.create", "amount": "100.00", "currency": "mmk"},
        )
    assert response.status_code == 400


def test_transaction_is_idempotent():
    payload = {
        "operation": "invoice.create",
        "amount": "100.00",
        "currency": "mmk",
        "metadata": {"invoice": "INV-001"},
    }
    headers = {"X-Idempotency-Key": f"invoice-create-{uuid4().hex}"}

    with TestClient(app) as client:
        first = client.post("/api/v1/transactions", json=payload, headers=headers)
        second = client.post("/api/v1/transactions", json=payload, headers=headers)

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["transaction_id"] == second.json()["transaction_id"]
    assert first.json()["idempotent_replay"] is False
    assert second.json()["idempotent_replay"] is True


@pytest.mark.asyncio
async def test_concurrent_same_key_commits_once():
    payload = {
        "operation": "stock.reserve",
        "amount": "1.00",
        "currency": "MMK",
        "metadata": {"sku": "SKU-001"},
    }
    key = f"stock-reserve-{uuid4().hex}"

    async def make_request():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/transactions",
                json=payload,
                headers={"X-Idempotency-Key": key},
            )
            return response

    responses = await asyncio.gather(*[make_request() for _ in range(8)])

    assert len(responses) == 8
    assert all(response.status_code == 201 for response in responses)
    transaction_ids = {response.json()["transaction_id"] for response in responses}
    assert len(transaction_ids) == 1
    assert sum(response.json()["idempotent_replay"] for response in responses) == 7


def test_transaction_lookup_is_authenticated_and_tenant_scoped():
    original_override = app.dependency_overrides[current_claims]
    try:
        # Authentication is enforced by the route when no test identity is present.
        app.dependency_overrides.pop(current_claims, None)
        with TestClient(app) as client:
            unauthenticated_create = client.post(
                "/api/v1/transactions",
                headers={"X-Idempotency-Key": f"auth-check-{uuid4().hex}"},
                json={"operation": "invoice.create", "amount": "10.00", "currency": "MMK"},
            )
            unauthenticated_lookup = client.get("/api/v1/transactions/not-a-real-id")
        assert unauthenticated_create.status_code == 401
        assert unauthenticated_lookup.status_code == 401

        app.dependency_overrides[current_claims] = lambda: {
            "sub": "tenant-a-user",
            "business_id": "tenant-a",
        }
        key = f"tenant-scope-{uuid4().hex}"
        with TestClient(app) as client:
            created = client.post(
                "/api/v1/transactions",
                headers={"X-Idempotency-Key": key},
                json={"operation": "invoice.create", "amount": "10.00", "currency": "MMK"},
            )
            assert created.status_code == 201, created.text
            transaction_id = created.json()["transaction_id"]

            app.dependency_overrides[current_claims] = lambda: {
                "sub": "tenant-b-user",
                "business_id": "tenant-b",
            }
            cross_tenant_lookup = client.get(f"/api/v1/transactions/{transaction_id}")
            same_raw_key_other_tenant = client.post(
                "/api/v1/transactions",
                headers={"X-Idempotency-Key": key},
                json={"operation": "invoice.create", "amount": "99.00", "currency": "MMK"},
            )

        assert cross_tenant_lookup.status_code == 404
        assert same_raw_key_other_tenant.status_code == 201
        assert same_raw_key_other_tenant.json()["transaction_id"] != transaction_id
    finally:
        app.dependency_overrides[current_claims] = original_override


def test_amount_that_rounds_to_zero_is_rejected():
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/transactions",
            headers={"X-Idempotency-Key": f"tiny-amount-{uuid4().hex}"},
            json={"operation": "invoice.create", "amount": "0.004", "currency": "MMK"},
        )
    assert response.status_code == 422


def test_transaction_get_returns_stored_entry():
    """GET /transactions/{id} returns the stored entry with idempotent_replay=False."""
    payload = {
        "operation": "order.create",
        "amount": "25.00",
        "currency": "MMK",
        "metadata": {"order": "ORD-001"},
    }
    headers = {"X-Idempotency-Key": f"get-test-{uuid4().hex}"}

    with TestClient(app) as client:
        created = client.post("/api/v1/transactions", json=payload, headers=headers)
        assert created.status_code == 201
        transaction_id = created.json()["transaction_id"]

        fetched = client.get(f"/api/v1/transactions/{transaction_id}")
        assert fetched.status_code == 200
        assert fetched.json()["transaction_id"] == transaction_id
        assert fetched.json()["idempotent_replay"] is False
        assert fetched.json()["metadata"] == {"order": "ORD-001"}


def test_transaction_get_missing_returns_404():
    with TestClient(app) as client:
        response = client.get("/api/v1/transactions/nonexistent-id")
    assert response.status_code == 404


def test_idempotency_fingerprint_ignores_metadata_key_order():
    """Replaying the same key with differently-ordered metadata keys replays."""
    payload1 = {
        "operation": "invoice.create",
        "amount": "10.00",
        "currency": "MMK",
        "metadata": {"invoice": "INV-A", "source": "pos"},
    }
    payload2 = {
        "operation": "invoice.create",
        "amount": "10.00",
        "currency": "MMK",
        "metadata": {"source": "pos", "invoice": "INV-A"},
    }
    headers = {"X-Idempotency-Key": f"canonical-{uuid4().hex}"}

    with TestClient(app) as client:
        first = client.post("/api/v1/transactions", json=payload1, headers=headers)
        replay = client.post("/api/v1/transactions", json=payload2, headers=headers)

    assert first.status_code == 201
    assert replay.status_code == 201
    assert replay.json()["transaction_id"] == first.json()["transaction_id"]
    assert replay.json()["idempotent_replay"] is True
