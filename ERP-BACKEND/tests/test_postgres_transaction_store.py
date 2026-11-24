"""Tests for the shared PostgreSQL transaction journal."""

import asyncio
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.transactions import get_db_session
from app.core.config import settings
from app.core.postgres_transaction_store import PostgresTransactionStore
from app.core.security import current_claims
from app.core.transaction_store import IdempotencyConflict
from app.db.session import SessionFactory, engine
from app.main import app
from app.models.transaction_journal import TransactionJournal

pytestmark = pytest.mark.requires_database


@pytest.mark.asyncio
async def test_shared_journal_replay_conflict_and_tenant_isolation():
    business_a = f"business-{uuid4()}"
    business_b = f"business-{uuid4()}"
    key = f"invoice-{uuid4()}"
    payload = {"invoice": "INV-001", "source": "pos"}

    async with SessionFactory() as session:
        first = await PostgresTransactionStore(session).execute(
            transaction_id=uuid4().hex,
            business_id=business_a,
            idempotency_key=key,
            operation="invoice.create",
            amount="100.00",
            currency="MMK",
            metadata=payload,
        )
        await session.commit()

    async with SessionFactory() as session:
        replay = await PostgresTransactionStore(session).execute(
            transaction_id=uuid4().hex,
            business_id=business_a,
            idempotency_key=key,
            operation="invoice.create",
            amount="100.00",
            currency="MMK",
            metadata={"source": "pos", "invoice": "INV-001"},
        )
        await session.commit()

    assert replay.transaction_id == first.transaction_id
    assert replay.idempotent_replay is True
    assert replay.status == "accepted"

    async with SessionFactory() as session:
        with pytest.raises(IdempotencyConflict) as conflict:
            await PostgresTransactionStore(session).execute(
                transaction_id=uuid4().hex,
                business_id=business_a,
                idempotency_key=key,
                operation="invoice.create",
                amount="101.00",
                currency="MMK",
                metadata=payload,
            )
        await session.rollback()

    assert conflict.value.code == "IDEMPOTENCY_PAYLOAD_MISMATCH"

    async with SessionFactory() as session:
        other_tenant = await PostgresTransactionStore(session).execute(
            transaction_id=uuid4().hex,
            business_id=business_b,
            idempotency_key=key,
            operation="invoice.create",
            amount="101.00",
            currency="MMK",
            metadata=payload,
        )
        hidden = await PostgresTransactionStore(session).get(
            first.transaction_id,
            business_id=business_b,
        )
        await session.commit()

    assert other_tenant.transaction_id != first.transaction_id
    assert hidden is None


@pytest.mark.asyncio
async def test_shared_journal_rejects_replay_of_fingerprintless_legacy_row():
    business_id = f"legacy-business-{uuid4()}"
    key = f"legacy-key-{uuid4()}"
    transaction_id = uuid4().hex

    async with SessionFactory() as session:
        session.add(
            TransactionJournal(
                transaction_id=transaction_id,
                business_id=business_id,
                idempotency_key=key,
                operation="invoice.create",
                amount="10.00",
                currency="MMK",
                metadata_json={"invoice": "INV-OLD"},
                request_fingerprint=None,
                status="accepted",
            )
        )
        await session.commit()

    async with SessionFactory() as session:
        with pytest.raises(IdempotencyConflict) as conflict:
            await PostgresTransactionStore(session).execute(
                transaction_id=uuid4().hex,
                business_id=business_id,
                idempotency_key=key,
                operation="invoice.create",
                amount="10.00",
                currency="MMK",
                metadata={"invoice": "INV-OLD"},
            )
        await session.rollback()

    assert conflict.value.code == "IDEMPOTENCY_KEY_REUSED"


@pytest.mark.asyncio
@pytest.mark.skipif(
    engine.dialect.name != "postgresql",
    reason="Concurrent uniqueness race requires PostgreSQL semantics",
)
async def test_concurrent_shared_journal_requests_create_one_record():
    business_id = f"concurrent-business-{uuid4()}"
    key = f"concurrent-key-{uuid4()}"
    payload = {"sku": "SKU-001", "quantity": 2}

    async def submit():
        async with SessionFactory() as session:
            result = await PostgresTransactionStore(session).execute(
                transaction_id=uuid4().hex,
                business_id=business_id,
                idempotency_key=key,
                operation="stock.reserve",
                amount="2.00",
                currency="MMK",
                metadata=payload,
            )
            await session.commit()
            return result

    results = await asyncio.gather(*(submit() for _ in range(8)))
    transaction_ids = {result.transaction_id for result in results}

    assert len(transaction_ids) == 1
    assert sum(result.idempotent_replay for result in results) == 7


@pytest.mark.asyncio
async def test_staging_transaction_api_uses_shared_postgres_journal(monkeypatch):
    monkeypatch.setattr(settings, "environment", "staging")
    monkeypatch.setattr(settings, "database_url", "postgresql+asyncpg://test-target")

    async def session_override():
        async with SessionFactory() as session:
            yield session

    business_id = f"staging-business-{uuid4()}"
    app.dependency_overrides[get_db_session] = session_override
    app.dependency_overrides[current_claims] = lambda: {
        "sub": "staging-test-user",
        "business_id": business_id,
    }
    try:
        key = f"staging-key-{uuid4()}"
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            created = await client.post(
                "/api/v1/transactions",
                headers={"X-Idempotency-Key": key},
                json={
                    "operation": "invoice.create",
                    "amount": "10.00",
                    "currency": "MMK",
                },
            )
            assert created.status_code == 201, created.text
            loaded = await client.get(
                f"/api/v1/transactions/{created.json()['transaction_id']}"
            )

        assert loaded.status_code == 200
        assert loaded.json()["status"] == "accepted"
        assert loaded.json()["transaction_id"] == created.json()["transaction_id"]
    finally:
        app.dependency_overrides.pop(get_db_session, None)
        app.dependency_overrides.pop(current_claims, None)
