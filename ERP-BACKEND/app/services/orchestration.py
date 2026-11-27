"""Cross-module transaction orchestration service.

Recovers operations that cross the journal (SQLite) and domain
(PostgreSQL) transaction boundaries. An operation is *committed* only
when its domain transaction commits; the operation row and the domain
mutations are updated in the same database transaction so either both
succeed or neither does.

The reconciliation service is safe under multiple replicas: PostgreSQL row
claims use SELECT FOR UPDATE SKIP LOCKED, and completion/failure paths fence
stale workers by reloading and locking the current lease owner.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError
from app.core.operation_metrics import record_operation_retry, record_operation_transition
from app.models.operations import (
    Operation,
    OperationState,
)


logger = logging.getLogger(__name__)


class OperationService:
    """Coordinates durable cross-module operations with bounded retries."""

    def __init__(self, session: AsyncSession, worker_id: str | None = None) -> None:
        self.session = session
        self.worker_id = worker_id or f"worker-{id(self)}"

    def _record_transition(
        self, operation: Operation, from_state: str, to_state: str
    ) -> None:
        record_operation_transition(operation.operation_type, from_state, to_state)
        fields = {
            "operation_id": operation.operation_id,
            "operation_type": operation.operation_type,
            "business_id": str(operation.business_id),
            "branch_id": str(operation.branch_id) if operation.branch_id else None,
            "from_state": from_state,
            "to_state": to_state,
            "worker_id": self.worker_id,
        }
        request_id = operation.payload_json.get("request_id")
        if isinstance(request_id, str):
            fields["request_id"] = request_id
        logger.info("operation_state_transition", extra=fields)

    # ------------------------------------------------------------------ create

    @staticmethod
    def _canonical_payload(payload: dict[str, Any]) -> str:
        """Serialize a command deterministically for idempotency comparison."""
        return json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )

    @staticmethod
    def _verify_replay(
        existing: Operation,
        *,
        operation_type: str,
        business_id: UUID,
        branch_id: UUID | None,
        canonical_payload: str,
    ) -> None:
        """Reject an operation ID reused across tenants or for another command."""
        same_command = (
            existing.operation_type == operation_type
            and existing.business_id == business_id
            and existing.branch_id == branch_id
            and OperationService._canonical_payload(existing.payload_json) == canonical_payload
        )
        if not same_command:
            raise ConflictError("Operation ID was already used for a different command")

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
        """Create a pending operation with command- and tenant-safe replay.

        Reusing an operation ID is idempotent only when tenant, branch, type,
        and canonical payload all match. A uniqueness race is resolved by
        re-reading the winner inside the caller's still-active transaction.
        """
        canonical_payload = self._canonical_payload(payload)
        existing = await self.get_operation(operation_id)
        if existing is not None:
            self._verify_replay(
                existing,
                operation_type=operation_type,
                business_id=business_id,
                branch_id=branch_id,
                canonical_payload=canonical_payload,
            )
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
        try:
            # Savepoint keeps the outer business transaction usable if another
            # replica inserts this unique operation_id concurrently.
            async with self.session.begin_nested():
                self.session.add(operation)
                await self.session.flush()
        except IntegrityError:
            existing = await self.get_operation(operation_id)
            if existing is None:
                raise
            self._verify_replay(
                existing,
                operation_type=operation_type,
                business_id=business_id,
                branch_id=branch_id,
                canonical_payload=canonical_payload,
            )
            return existing
        self._record_transition(operation, "new", OperationState.PENDING.value)
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

        previous_state = operation.state.value
        operation.state = OperationState.PROCESSING
        operation.claimed_at = datetime.now(UTC)
        operation.claimed_by = self.worker_id
        operation.updated_at = datetime.now(UTC)
        await self.session.flush()
        self._record_transition(operation, previous_state, OperationState.PROCESSING.value)
        return operation

    async def start_operation(self, operation: Operation) -> Operation:
        """Move a durable operation into PROCESSING within its caller transaction.

        Synchronous domain handlers call this after creating the operation and
        commit the state together with the domain mutation. Background workers
        should continue to use claim_next() so row-level leases are respected.
        """
        if not operation.is_claimable or not operation.can_transition_to(OperationState.PROCESSING):
            raise ConflictError(
                f"Operation {operation.operation_id} cannot transition to processing"
            )
        previous_state = operation.state.value
        now = datetime.now(UTC)
        operation.state = OperationState.PROCESSING
        operation.claimed_at = now
        operation.claimed_by = self.worker_id
        operation.updated_at = now
        await self.session.flush()
        self._record_transition(operation, previous_state, OperationState.PROCESSING.value)
        return operation

    async def _lock_processing_operation(self, operation: Operation) -> Operation:
        """Reload and lock an operation, enforcing the current worker lease."""
        current = await self.session.scalar(
            select(Operation)
            .where(Operation.id == operation.id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        if (
            current is None
            or current.state != OperationState.PROCESSING
            or current.claimed_by != self.worker_id
        ):
            raise ConflictError(
                f"Worker {self.worker_id} no longer owns operation {operation.operation_id}"
            )
        return current

    async def heartbeat(self, operation_id: str) -> Operation:
        """Renew the processing lease only while this worker still owns it."""
        operation = await self.session.scalar(
            select(Operation)
            .where(Operation.operation_id == operation_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        if (
            operation is None
            or operation.state != OperationState.PROCESSING
            or operation.claimed_by != self.worker_id
        ):
            raise ConflictError(f"Worker {self.worker_id} no longer owns operation {operation_id}")
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
        operation = await self._lock_processing_operation(operation)
        if not operation.can_transition_to(OperationState.COMMITTED):
            raise ConflictError(
                f"Operation {operation.operation_id} cannot transition to committed"
            )
        previous_state = operation.state.value
        operation.state = OperationState.COMMITTED
        operation.result_json = result
        operation.committed_at = datetime.now(UTC)
        operation.updated_at = datetime.now(UTC)
        operation.claimed_at = None
        operation.claimed_by = None
        await self.session.flush()
        self._record_transition(operation, previous_state, OperationState.COMMITTED.value)

    async def fail_operation(
        self,
        operation: Operation,
        *,
        error_code: str,
        error_message: str,
    ) -> None:
        """Record a failed attempt and either schedule retry or escalate."""
        operation = await self._lock_processing_operation(operation)
        if not operation.can_transition_to(OperationState.FAILED):
            raise ConflictError(f"Operation {operation.operation_id} cannot transition to failed")
        previous_state = operation.state.value
        operation.retry_count += 1
        operation.error_code = error_code
        operation.error_message = error_message
        operation.claimed_at = None
        operation.claimed_by = None
        operation.updated_at = datetime.now(UTC)

        if operation.retry_count >= operation.max_retries:
            operation.state = OperationState.RECONCILIATION_REQUIRED
        else:
            # Exponential backoff: 2^retry_count seconds, capped at 1 hour.
            backoff_seconds = min(2**operation.retry_count, 3600)
            operation.backoff_until = datetime.now(UTC) + timedelta(seconds=backoff_seconds)
            operation.state = OperationState.FAILED
        await self.session.flush()
        self._record_transition(operation, previous_state, operation.state.value)
        record_operation_retry(operation.operation_type, error_code)

    async def cancel_operation(self, operation: Operation) -> None:
        """Cancel a non-terminal operation for controlled manual recovery."""
        if not operation.can_transition_to(OperationState.CANCELLED):
            raise ConflictError(
                f"Operation {operation.operation_id} cannot transition to cancelled"
            )
        previous_state = operation.state.value
        operation.state = OperationState.CANCELLED
        operation.claimed_at = None
        operation.claimed_by = None
        operation.updated_at = datetime.now(UTC)
        await self.session.flush()
        self._record_transition(operation, previous_state, OperationState.CANCELLED.value)

    # ------------------------------------------------------------------ reconcile

    async def reconcile_stale(self, *, stale_after_seconds: int = 300) -> list[Operation]:
        """Reclaim operations stuck in PROCESSING (worker died mid-flight).

        Returns the list of operations reset to PENDING so another worker
        can pick them up. Safe under multiple replicas via the same
        conditional-claim pattern.
        """
        cutoff = datetime.now(UTC) - timedelta(seconds=stale_after_seconds)
        bind = self.session.get_bind()
        dialect = bind.dialect.name if bind is not None else "sqlite"
        result = await self.session.execute(
            select(Operation.id)
            .where(
                Operation.state == OperationState.PROCESSING,
                Operation.updated_at < cutoff,
            )
            .order_by(Operation.created_at.asc())
            .limit(50)
            .with_for_update(skip_locked=dialect != "sqlite"),
        )
        ids = [row[0] for row in result.all()]
        recovered: list[Operation] = []
        for op_id in ids:
            operation = await self.session.get(Operation, op_id)
            if operation is None:
                continue
            previous_state = operation.state.value
            operation.state = OperationState.PENDING
            operation.claimed_at = None
            operation.claimed_by = None
            operation.updated_at = datetime.now(UTC)
            recovered.append(operation)
        await self.session.flush()
        for operation in recovered:
            self._record_transition(
                operation, OperationState.PROCESSING.value, OperationState.PENDING.value
            )
        return recovered
