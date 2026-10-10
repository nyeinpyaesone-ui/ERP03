import sqlite3
import threading
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.transactions import store
from app.core.security import current_claims
from app.core.transaction_store import TransactionStore
from app.main import app


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


def test_concurrent_same_key_commits_once():
    payload = {
        "operation": "stock.reserve",
        "amount": "1.00",
        "currency": "MMK",
        "metadata": {"sku": "SKU-001"},
    }
    key = f"stock-reserve-{uuid4().hex}"
    responses = []

    def request():
        with TestClient(app) as client:
            responses.append(
                client.post(
                    "/api/v1/transactions",
                    json=payload,
                    headers={"X-Idempotency-Key": key},
                )
            )

    threads = [threading.Thread(target=request) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

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


def test_failed_write_rolls_back_and_key_can_be_retried():
    key = f"rollback-retry-{uuid4().hex}"
    with pytest.raises(TypeError):
        store.execute(
            transaction_id="failed-write-001",
            idempotency_key=key,
            operation="finance.post",
            amount="10.00",
            currency="MMK",
            metadata={"invalid": object()},
        )

    result = store.execute(
        transaction_id="successful-retry-001",
        idempotency_key=key,
        operation="finance.post",
        amount="10.00",
        currency="MMK",
        metadata={"retry": True},
    )
    assert result.transaction_id == "successful-retry-001"
    assert result.idempotent_replay is False


def test_transaction_survives_store_reinitialization(tmp_path):
    database = str(tmp_path / "transactions.sqlite3")
    first_store = TransactionStore(database)
    created = first_store.execute(
        transaction_id="persistent-001",
        idempotency_key="persistent-key-001",
        operation="order.create",
        amount="25.00",
        currency="MMK",
        metadata={"order": "ORD-001"},
        business_id="persistent-business",
    )

    second_store = TransactionStore(database)
    loaded = second_store.get(
        created.transaction_id,
        business_id="persistent-business",
    )
    assert loaded is not None
    assert loaded.transaction_id == created.transaction_id
    assert loaded.metadata == {"order": "ORD-001"}
    assert second_store.get(created.transaction_id, business_id="another-business") is None


def test_existing_journal_is_migrated_and_legacy_tenant_is_recovered(tmp_path):
    database = tmp_path / "legacy.sqlite3"
    connection = sqlite3.connect(database)
    try:
        connection.execute(
            """
            CREATE TABLE transactions (
                transaction_id TEXT PRIMARY KEY,
                idempotency_key TEXT NOT NULL UNIQUE,
                operation TEXT NOT NULL,
                amount TEXT NOT NULL,
                currency TEXT NOT NULL,
                metadata_json TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            INSERT INTO transactions
            (transaction_id, idempotency_key, operation, amount, currency,
             metadata_json, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "legacy-transaction-001",
                "legacy-business:legacy-key",
                "invoice.create",
                "15.00",
                "MMK",
                '{"invoice":"LEGACY-001"}',
                "committed",
                "2026-01-01T00:00:00+00:00",
            ),
        )
        connection.commit()
    finally:
        connection.close()

    migrated_store = TransactionStore(str(database))
    owned = migrated_store.get("legacy-transaction-001", business_id="legacy-business")
    foreign = migrated_store.get("legacy-transaction-001", business_id="other-business")

    assert owned is not None
    assert owned.metadata == {"invoice": "LEGACY-001"}
    assert foreign is None
