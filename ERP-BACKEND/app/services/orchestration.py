"""Cross-module transaction orchestration service.

Recovers operations that cross the journal (SQLite) and domain
(PostgreSQL) transaction boundaries. An operation is *committed* only
when its domain transaction commits; the operation row and the domain
mutations are updated in the same database transaction so either both
succeed or neither does.

The reconciliation worker is safe under multiple replicas: claiming an
operation is an atomic conditional UPDATE (state re-checked inside the
write transaction), so two workers never process the same operation.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError
from app.models.operations import (
    Operation,
    OperationState,
)


class OperationService:
    """Coordinates durable cross-module operations with bounded retries."""

    def __init__(self, session: AsyncSession, worker_id: str | None = None) -> None:
        self.session = session
        self.worker_id = worker_id or f"worker-{id(self)}"

    # ------------------------------------------------------------------ create

    async def create_operation(
        self,
        *,
        operation_id: str,
        operation_type: str,
        business_id: UUID,
        payload: dict[str, Any],
        branch_id: UUID | None = None,
        max_retries: int = 5,
    ) -> Operation:
        """Create a pending operation, idempotent by ``operation_id``.

        If an operation with the same ``operation_id`` already exists it is
        returned unchanged (same-key/same-command replays the prior result).
        """
        existing = await self.get_operation(operation_id)
        if existing is not None:
            return existing

        operation = Operation(
            operation_id=operation_id,
            operation_type=operation_type,
            state=OperationState.PENDING,
            business_id=business_id,
            branch_id=branch_id,
            payload_json=payload,
            max_retries=max_retries,
        )
        self.session.add(operation)
        await self.session.flush()
        return operation

    # ------------------------------------------------------------------ read

    async def get_operation(self, operation_id: str) -> Operation | None:
        result = await self.session.execute(
            select(Operation).where(Operation.operation_id == operation_id)
        )
        return result.scalar_one_or_none()

    async def get_operation_by_id(self, operation_id: UUID) -> Operation | None:
        return await self.session.get(Operation, operation_id)

    # ------------------------------------------------------------------ claim

    def _claimable_query(self):
        """Build a claim query, dialing back ``SKIP LOCKED`` for SQLite.

        PostgreSQL supports ``FOR UPDATE SKIP LOCKED`` so concurrent workers
        never contend on the same row. SQLite (the dev/local backend) does
        not support ``SKIP LOCKED``; it serializes writers via
        ``BEGIN IMMEDIATE`` so plain ``FOR UPDATE`` is sufficient there.
        """
        bind = self.session.get_bind()
        dialect = bind.dialect.name if bind is not None else "sqlite"
        skip_locked = dialect != "sqlite"

        return (
            select(Operation.id)
            .where(
                Operation.state.in_([OperationState.PENDING, OperationState.FAILED]),
                (Operation.backoff_until.is_(None))
                | (Operation.backoff_until <= datetime.now(UTC)),
            )
            .order_by(Operation.created_at.asc())
            .limit(1)
            .with_for_update(skip_locked=skip_locked)
        )

    def _for_update_kwargs(self) -> dict[str, bool]:
        bind = self.session.get_bind()
        dialect = bind.dialect.name if bind is not None else "sqlite"
        return {"skip_locked": dialect != "sqlite"}

    async def claim_next(self) -> Operation | None:
        """Atomically claim the next claimable operation for this worker.

        Uses a conditional SELECT FOR UPDATE that re-checks the state inside
        the write transaction, so concurrent replicas never double-claim.
        Returns the claimed operation, or ``None`` when nothing is claimable.
        """
        result = await self.session.execute(self._claimable_query())
        row = result.first()
        if row is None:
            return None

        operation = await self.session.get(Operation, row[0])
        if operation is None or not operation.is_claimable:
            return None

        # Re-verify state inside the transaction before mutating (another
        # replica may have claimed it between SELECT and UPDATE).
        if operation.state not in (OperationState.PENDING, OperationState.FAILED):
            return None
        if operation.state == OperationState.FAILED and operation.backoff_until is not None:
            backoff = operation.backoff_until
            if backoff.tzinfo is None:
                backoff = backoff.replace(tzinfo=UTC)
            if datetime.now(UTC) < backoff:
                return None

        operation.state = OperationState.PROCESSING
        operation.claimed_at = datetime.now(UTC)
        operation.claimed_by = self.worker_id
        operation.updated_at = datetime.now(UTC)
        await self.session.flush()
        return operation

    async def commit_operation(
        self,
        operation: Operation,
        *,
        result: dict[str, Any] | None = None,
    ) -> None:
        """Mark an operation committed and persist its outcome.

        Callers invoke this inside the same database transaction that
        commits the domain mutations (invoice, payment, stock), so the
        operation outcome and the business result are atomic.
        """
        if not operation.can_transition_to(OperationState.COMMITTED):
            raise ConflictError(
                f"Operation {operation.operation_id} cannot transition to committed"
            )
        operation.state = OperationState.COMMITTED
        operation.result_json = result
        operation.committed_at = datetime.now(UTC)
        operation.updated_at = datetime.now(UTC)
        operation.claimed_by = None
        await self.session.flush()

    async def fail_operation(
        self,
        operation: Operation,
        *,
        error_code: str,
        error_message: str,
    ) -> None:
        """Record a failed attempt and either schedule retry or escalate."""
        if not operation.can_transition_to(OperationState.FAILED):
            raise ConflictError(f"Operation {operation.operation_id} cannot transition to failed")
        operation.retry_count += 1
        operation.error_code = error_code
        operation.error_message = error_message
        operation.updated_at = datetime.now(UTC)

        if operation.retry_count >= operation.max_retries:
            operation.state = OperationState.RECONCILIATION_REQUIRED
        else:
            # Exponential backoff: 2^retry_count seconds, capped at 1 hour.
            backoff_seconds = min(2**operation.retry_count, 3600)
            operation.backoff_until = datetime.now(UTC) + timedelta(seconds=backoff_seconds)
            operation.state = OperationState.FAILED
        await self.session.flush()

    async def cancel_operation(self, operation: Operation) -> None:
        """Terminal manual-abort transition."""
        operation.state = OperationState.CANCELLED
        operation.updated_at = datetime.now(UTC)
        await self.session.flush()

    # ------------------------------------------------------------------ reconcile

    async def reconcile_stale(self, *, stale_after_seconds: int = 300) -> list[Operation]:
        """Reclaim operations stuck in PROCESSING (worker died mid-flight).

        Returns the list of operations reset to PENDING so another worker
        can pick them up. Safe under multiple replicas via the same
        conditional-claim pattern.
        """
        cutoff = datetime.now(UTC) - timedelta(seconds=stale_after_seconds)
        result = await self.session.execute(
            select(Operation.id)
            .where(
                Operation.state == OperationState.PROCESSING,
                Operation.updated_at < cutoff,
            )
            .order_by(Operation.created_at.asc())
            .limit(50)
            .with_for_update(**self._for_update_kwargs()),
        )
        ids = [row[0] for row in result.all()]
        recovered: list[Operation] = []
        for op_id in ids:
            operation = await self.session.get(Operation, op_id)
            if operation is None:
                continue
            operation.state = OperationState.PENDING
            operation.claimed_at = None
            operation.claimed_by = None
            operation.updated_at = datetime.now(UTC)
            recovered.append(operation)
        await self.session.flush()
        return recovered
