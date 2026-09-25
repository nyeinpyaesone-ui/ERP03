import threading

from fastapi.testclient import TestClient

from app.api.transactions import store
from app.main import app


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
    headers = {"X-Idempotency-Key": "invoice-create-001"}

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
    key = "stock-reserve-concurrent-001"
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
