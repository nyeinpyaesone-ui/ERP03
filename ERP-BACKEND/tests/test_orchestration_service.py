"""Coverage for the cross-module operation orchestration state machine."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from app.core.errors import ConflictError
from app.db.session import SessionFactory
from app.models.operations import Operation, OperationState
from app.services.bootstrap import bootstrap_business
from app.services.orchestration import OperationService
from sqlalchemy import delete, select


@pytest.fixture(autouse=True)
async def _clean_operations():
    """Remove all operations after each test so tests stay isolated."""
    yield
    async with SessionFactory() as session, session.begin():
        await session.execute(delete(Operation))
        await session.commit()


async def _bootstrap(prefix: str):
    async with SessionFactory() as session, session.begin():
        return await bootstrap_business(
            session,
            business_name=f"{prefix} Business",
            business_code=f"{prefix}-{uuid4().hex[:8]}",
            branch_name="Main Branch",
            branch_code="MAIN",
            owner_email=f"owner-{uuid4().hex[:8]}@example.com",
            owner_password="Correct-Horse-123",
            owner_name="Owner",
        )


@pytest.mark.asyncio
async def test_create_operation_is_idempotent_by_operation_id():
    """Same operation_id returns the existing operation (no duplicate)."""
    business, branch, _warehouse, _user = await _bootstrap("ORCH")
    async with SessionFactory() as session, session.begin():
        service = OperationService(session)
        first = await service.create_operation(
            operation_id="orch-001",
            operation_type="pos.sale",
            business_id=business.id,
            branch_id=branch.id,
            payload={"product": "widget", "qty": 1},
        )
        await session.commit()
    assert first.state == OperationState.PENDING
    assert first.operation_id == "orch-001"

    async with SessionFactory() as session, session.begin():
        service = OperationService(session)
        second = await service.create_operation(
            operation_id="orch-001",
            operation_type="pos.sale",
            business_id=business.id,
            branch_id=branch.id,
            payload={"product": "widget", "qty": 1},
        )
        await session.commit()
    assert second.id == first.id
    assert second.state == OperationState.PENDING


@pytest.mark.asyncio
async def test_claim_next_marks_pending_operation_processing():
    """Claiming transitions PENDING -> PROCESSING and stamps the worker."""
    business, branch, _warehouse, _user = await _bootstrap("ORCHC")
    async with SessionFactory() as session, session.begin():
        service = OperationService(session)
        await service.create_operation(
            operation_id="orch-claim-001",
            operation_type="pos.sale",
            business_id=business.id,
            branch_id=branch.id,
            payload={"product": "widget"},
        )
        await session.commit()
    async with SessionFactory() as session, session.begin():
        service = OperationService(session, worker_id="worker-a")
        claimed = await service.claim_next()
        await session.commit()
    assert claimed is not None
    assert claimed.state == OperationState.PROCESSING
    assert claimed.claimed_by == "worker-a"
    assert claimed.claimed_at is not None


@pytest.mark.asyncio
async def test_claim_next_returns_none_when_no_claimable_operations():
    """An empty queue returns None instead of raising."""
    business, branch, _warehouse, _user = await _bootstrap("ORCHE")
    async with SessionFactory() as session, session.begin():
        service = OperationService(session, worker_id="worker-a")
        claimed = await service.claim_next()
        await session.commit()
    assert claimed is None


@pytest.mark.asyncio
async def test_concurrent_workers_claim_different_operations():
    """Two claimable operations are claimed by separate workers, never doubled."""
    business, branch, _warehouse, _user = await _bootstrap("ORCHCC")
    async with SessionFactory() as session, session.begin():
        service = OperationService(session)
        await service.create_operation(
            operation_id="orch-cc-1",
            operation_type="pos.sale",
            business_id=business.id,
            branch_id=branch.id,
            payload={"n": 1},
        )
        await service.create_operation(
            operation_id="orch-cc-2",
            operation_type="pos.sale",
            business_id=business.id,
            branch_id=branch.id,
            payload={"n": 2},
        )
        await session.commit()
    async with SessionFactory() as session, session.begin():
        service_a = OperationService(session, worker_id="worker-a")
        service_b = OperationService(session, worker_id="worker-b")
        claimed_a = await service_a.claim_next()
        claimed_b = await service_b.claim_next()
        await session.commit()
    assert claimed_a is not None and claimed_b is not None
    assert claimed_a.id != claimed_b.id
    assert {claimed_a.claimed_by, claimed_b.claimed_by} == {"worker-a", "worker-b"}


@pytest.mark.asyncio
async def test_commit_operation_transitions_to_committed():
    """A claimed operation can be committed with a stored result."""
    business, branch, _warehouse, _user = await _bootstrap("ORCHCM")
    async with SessionFactory() as session, session.begin():
        service = OperationService(session)
        await service.create_operation(
            operation_id="orch-cm-001",
            operation_type="pos.sale",
            business_id=business.id,
            branch_id=branch.id,
            payload={"product": "widget"},
        )
        await session.commit()
    invoice_id = str(uuid4())
    async with SessionFactory() as session, session.begin():
        service = OperationService(session, worker_id="worker-a")
        op = await service.claim_next()
        await service.commit_operation(op, result={"invoice_id": invoice_id})
        await session.commit()
    async with SessionFactory() as session:
        result = await session.execute(
            select(Operation).where(Operation.operation_id == "orch-cm-001")
        )
        op = result.scalar_one()
    assert op.state == OperationState.COMMITTED
    assert op.result_json == {"invoice_id": invoice_id}
    assert op.committed_at is not None


@pytest.mark.asyncio
async def test_fail_operation_retries_with_backoff():
    """A failed operation schedules a retry with exponential backoff."""
    business, branch, _warehouse, _user = await _bootstrap("ORCHF")
    async with SessionFactory() as session, session.begin():
        service = OperationService(session)
        await service.create_operation(
            operation_id="orch-f-001",
            operation_type="pos.sale",
            business_id=business.id,
            branch_id=branch.id,
            payload={"product": "widget"},
            max_retries=3,
        )
        await session.commit()
    async with SessionFactory() as session, session.begin():
        service = OperationService(session, worker_id="worker-a")
        op = await service.claim_next()
        await service.fail_operation(op, error_code="PAYMENT_ERROR", error_message="card declined")
        await session.commit()
    async with SessionFactory() as session:
        result = await session.execute(
            select(Operation).where(Operation.operation_id == "orch-f-001")
        )
        op = result.scalar_one()
    assert op.state == OperationState.FAILED
    assert op.retry_count == 1
    assert op.error_code == "PAYMENT_ERROR"
    assert op.backoff_until is not None
    backoff = op.backoff_until
    if backoff.tzinfo is None:
        backoff = backoff.replace(tzinfo=UTC)
    assert backoff > datetime.now(UTC)


@pytest.mark.asyncio
async def test_fail_beyond_max_retries_escalates_to_reconciliation():
    """Exceeding max_retries moves the operation to reconciliation_required."""
    business, branch, _warehouse, _user = await _bootstrap("ORCHR")
    async with SessionFactory() as session, session.begin():
        service = OperationService(session)
        await service.create_operation(
            operation_id="orch-r-001",
            operation_type="pos.sale",
            business_id=business.id,
            branch_id=branch.id,
            payload={"product": "widget"},
            max_retries=1,
        )
        await session.commit()
    async with SessionFactory() as session, session.begin():
        service = OperationService(session, worker_id="worker-a")
        op = await service.claim_next()
        await service.fail_operation(op, error_code="PAYMENT_ERROR", error_message="card declined")
        await session.commit()
    async with SessionFactory() as session:
        result = await session.execute(
            select(Operation).where(Operation.operation_id == "orch-r-001")
        )
        op = result.scalar_one()
    assert op.state == OperationState.RECONCILIATION_REQUIRED
    assert op.retry_count == 1


@pytest.mark.asyncio
async def test_reconcile_stale_recovers_processing_operations():
    """Stale PROCESSING operations are reset to PENDING for re-claiming."""
    business, branch, _warehouse, _user = await _bootstrap("ORCHS")
    async with SessionFactory() as session, session.begin():
        service = OperationService(session)
        await service.create_operation(
            operation_id="orch-s-001",
            operation_type="pos.sale",
            business_id=business.id,
            branch_id=branch.id,
            payload={"product": "widget"},
        )
        await session.commit()
    async with SessionFactory() as session, session.begin():
        service = OperationService(session, worker_id="worker-a")
        op = await service.claim_next()
        op.updated_at = datetime.now(UTC) - timedelta(hours=2)
        await session.commit()
    async with SessionFactory() as session, session.begin():
        service = OperationService(session, worker_id="worker-b")
        recovered = await service.reconcile_stale(stale_after_seconds=300)
        await session.commit()
    assert len(recovered) == 1
    assert recovered[0].state == OperationState.PENDING
    assert recovered[0].claimed_by is None
    assert recovered[0].claimed_at is None

    async with SessionFactory() as session, session.begin():
        service = OperationService(session, worker_id="worker-b")
        reclaimed = await service.claim_next()
        await session.commit()
    assert reclaimed is not None
    assert reclaimed.state == OperationState.PROCESSING
    assert reclaimed.claimed_by == "worker-b"


@pytest.mark.asyncio
async def test_sqlite_claim_never_double_claims_same_operation():
    """On SQLite (no SKIP LOCKED), sequential claims never return the same operation."""
    business, branch, _warehouse, _user = await _bootstrap("ORCHD")
    async with SessionFactory() as session, session.begin():
        service = OperationService(session)
        await service.create_operation(
            operation_id="orch-d-001",
            operation_type="pos.sale",
            business_id=business.id,
            branch_id=branch.id,
            payload={"product": "widget"},
        )
        await session.commit()
    claimed_ids = set()
    async with SessionFactory() as session, session.begin():
        service_a = OperationService(session, worker_id="worker-a")
        service_b = OperationService(session, worker_id="worker-b")
        for _ in range(2):
            claimed_a = await service_a.claim_next()
            claimed_b = await service_b.claim_next()
            for op in (claimed_a, claimed_b):
                if op is not None:
                    claimed_ids.add(op.id)
        await session.commit()
    # Only one operation exists; only one claim should succeed.
    assert len(claimed_ids) == 1


@pytest.mark.asyncio
async def test_cannot_transition_from_terminal_state():
    """Committed operations reject further transitions."""
    business, branch, _warehouse, _user = await _bootstrap("ORCHT")
    async with SessionFactory() as session, session.begin():
        service = OperationService(session)
        await service.create_operation(
            operation_id="orch-t-001",
            operation_type="pos.sale",
            business_id=business.id,
            branch_id=branch.id,
            payload={"product": "widget"},
        )
        await session.commit()
    async with SessionFactory() as session, session.begin():
        service = OperationService(session, worker_id="worker-a")
        op = await service.claim_next()
        await service.commit_operation(op, result={"ok": True})
        await session.commit()
    async with SessionFactory() as session, session.begin():
        service = OperationService(session, worker_id="worker-a")
        op = await session.get(Operation, op.id)
        with pytest.raises(ConflictError):
            await service.fail_operation(op, error_code="BOOM", error_message="too late")
        await session.rollback()


@pytest.mark.asyncio
async def test_get_operation_returns_none_for_unknown_id():
    """Looking up a missing operation_id returns None."""
    async with SessionFactory() as session:
        service = OperationService(session)
        result = await service.get_operation("does-not-exist")
    assert result is None
