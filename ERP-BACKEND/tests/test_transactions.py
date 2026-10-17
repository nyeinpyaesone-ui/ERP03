import threading
from uuid import uuid4

import pytest
from app.api.transactions import store
from app.core.security import current_claims
from app.main import app
from fastapi.testclient import TestClient

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
    # Unique key per run: the journal file outlives the process, so a fixed
    # key would replay a stale entry from an earlier run and break assertions.
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
    key = f"stock-reserve-concurrent-{uuid4().hex}"
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


def test_failed_write_rolls_back_and_key_can_be_retried():
    key = f"rollback-retry-{uuid4().hex}"
    try:
        store.execute(
            transaction_id=f"failed-write-{uuid4().hex}",
            business_id="test-business",
            idempotency_key=key,
            operation="finance.post",
            amount="10.00",
            currency="MMK",
            metadata={"invalid": object()},
        )
    except TypeError:
        pass
    else:
        raise AssertionError("Expected metadata serialization to fail")

    result = store.execute(
        transaction_id=f"successful-retry-{uuid4().hex}",
        business_id="test-business",
        idempotency_key=key,
        operation="finance.post",
        amount="10.00",
        currency="MMK",
        metadata={"retry": True},
    )
    assert not result.idempotent_replay
    assert result.metadata == {"retry": True}


def test_transaction_survives_store_reinitialization(tmp_path):
    from app.core.transaction_store import TransactionStore

    database = str(tmp_path / "transactions.sqlite3")
    first_store = TransactionStore(database)
    created = first_store.execute(
        transaction_id="persistent-001",
        business_id="business-a",
        idempotency_key="persistent-key-001",
        operation="order.create",
        amount="25.00",
        currency="MMK",
        metadata={"order": "ORD-001"},
    )

    second_store = TransactionStore(database)
    loaded = second_store.get(created.transaction_id, business_id="business-a")
    assert loaded is not None
    assert loaded.transaction_id == created.transaction_id
    assert loaded.metadata == {"order": "ORD-001"}
    # Foreign tenants cannot read the entry even when they know its ID.
    assert second_store.get(created.transaction_id, business_id="business-b") is None
