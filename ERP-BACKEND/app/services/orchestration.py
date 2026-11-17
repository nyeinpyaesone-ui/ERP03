"""Cross-module transaction orchestration with bounded retries and fenced leases.

Operation state and domain mutations live in the same SQLAlchemy transaction.
PostgreSQL row locks allow independent backend replicas to claim distinct work.
A persisted claim token fences out workers whose leases expired or were reclaimed.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import and_, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError
from app.models.operations import Operation, OperationState


class OperationService:
    """Coordinates durable cross-module operations with bounded retries.

    A caller must commit the session after claiming work. Domain handlers must
    perform their business writes and call `commit_operation` in one shared
    session transaction. Claim tokens prevent an expired worker from committing
    after another worker has reclaimed the operation.
    """

    def __init__(
        self,
        session: AsyncSession,
        worker_id: str | None = None,
        *,
        lease_seconds: int = 300,
    ) -> None:
        if lease_seconds < 1:
            raise ValueError("lease_seconds must be at least one")
        self.session = session
        self.worker_id = worker_id or f"worker-{uuid4().hex}"
        self.lease_seconds = lease_seconds

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
        """Reject an operation ID reused for another tenant or command.

        A null branch on a migrated legacy operation means its original branch
        context was not recorded; preserve replay compatibility in that case.
        Once a branch is recorded, a replay from another branch is rejected.
        """
        same_command = (
            existing.operation_type == operation_type
            and existing.business_id == business_id
            and (existing.branch_id is None or existing.branch_id == branch_id)
            and OperationService._canonical_payload(existing.payload_json) == canonical_payload
        )
        if not same_command:
            raise ConflictError("Operation ID was already used for a different command")

    async def create_operation_with_replay(
        self,
        *,
        operation_id: str,
        operation_type: str,
        business_id: UUID,
        payload: dict[str, Any],
        branch_id: UUID | None = None,
        max_retries: int = 5,
    ) -> tuple[Operation, bool]:
        """Create a pending operation and report whether this call replayed it.

        The unique operation_id constraint arbitrates cross-replica races.
        The nested transaction keeps the caller's outer transaction usable
        when another request inserts the same operation concurrently.
        """
        if not operation_id or len(operation_id) > 255:
            raise ValueError("operation_id must contain 1..255 characters")
        if not operation_type or len(operation_type) > 100:
            raise ValueError("operation_type must contain 1..100 characters")
        if max_retries < 1:
            raise ValueError("max_retries must be at least one")

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
            return existing, True

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
            return existing, True
        return operation, False

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
        """Compatibility wrapper for callers that do not need replay metadata."""
        operation, _replayed = await self.create_operation_with_replay(
            operation_id=operation_id,
            operation_type=operation_type,
            business_id=business_id,
            branch_id=branch_id,
            payload=payload,
            max_retries=max_retries,
        )
        return operation

    async def get_operation(self, operation_id: str) -> Operation | None:
        result = await self.session.execute(
            select(Operation).where(Operation.operation_id == operation_id)
        )
        return result.scalar_one_or_none()

    async def get_operation_by_id(self, operation_id: UUID) -> Operation | None:
        return await self.session.get(Operation, operation_id)

    def _claimable_query(self):
        """Build a row-locking query appropriate to the configured dialect."""
        bind = self.session.get_bind()
        dialect = bind.dialect.name if bind is not None else "sqlite"
        return (
            select(Operation.id)
            .where(
                Operation.state.in_([OperationState.PENDING, OperationState.FAILED]),
                or_(
                    Operation.backoff_until.is_(None),
                    Operation.backoff_until <= datetime.now(UTC),
                ),
            )
            .order_by(Operation.created_at.asc())
            .limit(1)
            .with_for_update(skip_locked=dialect != "sqlite")
        )

    async def claim_next(self) -> Operation | None:
        """Claim one available operation using a unique, expiring fencing token."""
        result = await self.session.execute(self._claimable_query())
        row = result.first()
        if row is None:
            return None

        operation = await self.session.get(Operation, row[0])
        if operation is None or not operation.is_claimable:
            return None
        if operation.state not in (OperationState.PENDING, OperationState.FAILED):
            return None

        now = datetime.now(UTC)
        token = uuid4().hex
        operation.state = OperationState.PROCESSING
        operation.claimed_at = now
        operation.claimed_by = self.worker_id
        operation.claim_token = token
        operation.lease_expires_at = now + timedelta(seconds=self.lease_seconds)
        operation.backoff_until = None
        operation.updated_at = now
        await self.session.flush()
        return operation

    def _assert_claimed_by_this_worker(self, operation: Operation) -> str:
        if (
            operation.state != OperationState.PROCESSING
            or operation.claimed_by != self.worker_id
            or not operation.claim_token
        ):
            raise ConflictError(
                f"Worker {self.worker_id} does not own operation {operation.operation_id}"
            )
        return operation.claim_token

    async def renew_lease(self, operation: Operation) -> bool:
        """Extend a live claim; an expired or superseded token cannot be revived."""
        token = self._assert_claimed_by_this_worker(operation)
        now = datetime.now(UTC)
        new_expiry = now + timedelta(seconds=self.lease_seconds)
        result = await self.session.execute(
            update(Operation)
            .where(
                Operation.id == operation.id,
                Operation.state == OperationState.PROCESSING,
                Operation.claimed_by == self.worker_id,
                Operation.claim_token == token,
                Operation.lease_expires_at > now,
            )
            .values(lease_expires_at=new_expiry, updated_at=now)
            .execution_options(synchronize_session=False)
        )
        if result.rowcount != 1:
            return False
        operation.lease_expires_at = new_expiry
        operation.updated_at = now
        return True

    async def commit_operation(
        self,
        operation: Operation,
        *,
        result: dict[str, Any] | None = None,
    ) -> None:
        """Commit operation state in the same DB transaction as domain writes."""
        token = self._assert_claimed_by_this_worker(operation)
        now = datetime.now(UTC)
        updated = await self.session.execute(
            update(Operation)
            .where(
                Operation.id == operation.id,
                Operation.state == OperationState.PROCESSING,
                Operation.claimed_by == self.worker_id,
                Operation.claim_token == token,
                Operation.lease_expires_at > now,
            )
            .values(
                state=OperationState.COMMITTED,
                result_json=result,
                committed_at=now,
                updated_at=now,
                claimed_at=None,
                claimed_by=None,
                claim_token=None,
                lease_expires_at=None,
            )
            .execution_options(synchronize_session=False)
        )
        if updated.rowcount != 1:
            raise ConflictError(
                f"Operation {operation.operation_id} lease was lost; refusing stale commit"
            )
        operation.state = OperationState.COMMITTED
        operation.result_json = result
        operation.committed_at = now
        operation.updated_at = now
        operation.claimed_at = None
        operation.claimed_by = None
        operation.claim_token = None
        operation.lease_expires_at = None

    @staticmethod
    def _safe_error_message(_value: str) -> str:
        """Persist a safe summary; raw exception text may contain credentials or PII."""
        return "Operation failed; inspect sanitized application logs using the operation ID."

    async def fail_operation(
        self,
        operation: Operation,
        *,
        error_code: str,
        error_message: str,
    ) -> None:
        """Record a failed attempt, retry with backoff, or request reconciliation."""
        token = self._assert_claimed_by_this_worker(operation)
        if not error_code or len(error_code) > 64:
            raise ValueError("error_code must contain 1..64 characters")

        now = datetime.now(UTC)
        next_retry = operation.retry_count + 1
        exhausted = next_retry >= operation.max_retries
        backoff = None if exhausted else now + timedelta(seconds=min(2**next_retry, 3600))
        next_state = (
            OperationState.RECONCILIATION_REQUIRED if exhausted else OperationState.FAILED
        )
        updated = await self.session.execute(
            update(Operation)
            .where(
                Operation.id == operation.id,
                Operation.state == OperationState.PROCESSING,
                Operation.claimed_by == self.worker_id,
                Operation.claim_token == token,
                Operation.lease_expires_at > now,
            )
            .values(
                state=next_state,
                retry_count=next_retry,
                error_code=error_code,
                error_message=self._safe_error_message(error_message),
                backoff_until=backoff,
                claimed_at=None,
                claimed_by=None,
                claim_token=None,
                lease_expires_at=None,
                updated_at=now,
            )
            .execution_options(synchronize_session=False)
        )
        if updated.rowcount != 1:
            raise ConflictError(
                f"Operation {operation.operation_id} lease was lost; refusing stale failure"
            )

        operation.state = next_state
        operation.retry_count = next_retry
        operation.error_code = error_code
        operation.error_message = self._safe_error_message(error_message)
        operation.backoff_until = backoff
        operation.claimed_at = None
        operation.claimed_by = None
        operation.claim_token = None
        operation.lease_expires_at = None
        operation.updated_at = now

    async def cancel_operation(self, operation: Operation) -> None:
        """Cancel a non-terminal operation and invalidate any outstanding lease."""
        if not operation.can_transition_to(OperationState.CANCELLED):
            raise ConflictError(
                f"Operation {operation.operation_id} cannot transition to cancelled"
            )
        now = datetime.now(UTC)
        updated = await self.session.execute(
            update(Operation)
            .where(
                Operation.id == operation.id,
                Operation.state.not_in(
                    [OperationState.COMMITTED, OperationState.CANCELLED]
                ),
            )
            .values(
                state=OperationState.CANCELLED,
                claimed_at=None,
                claimed_by=None,
                claim_token=None,
                lease_expires_at=None,
                updated_at=now,
            )
            .execution_options(synchronize_session=False)
        )
        if updated.rowcount != 1:
            raise ConflictError(
                f"Operation {operation.operation_id} is already terminal or no longer exists"
            )
        operation.state = OperationState.CANCELLED
        operation.claimed_at = None
        operation.claimed_by = None
        operation.claim_token = None
        operation.lease_expires_at = None
        operation.updated_at = now

    async def reconcile_stale(self, *, stale_after_seconds: int = 300) -> list[Operation]:
        """Return expired processing claims to PENDING for safe re-claiming.

        Rows from the pre-lease schema are also recovered after their updated_at
        timestamp exceeds the compatibility cutoff.
        """
        if stale_after_seconds < 1:
            raise ValueError("stale_after_seconds must be at least one")
        now = datetime.now(UTC)
        cutoff = now - timedelta(seconds=stale_after_seconds)
        bind = self.session.get_bind()
        dialect = bind.dialect.name if bind is not None else "sqlite"
        result = await self.session.execute(
            select(Operation.id)
            .where(
                Operation.state == OperationState.PROCESSING,
                or_(
                    Operation.lease_expires_at <= now,
                    and_(
                        Operation.lease_expires_at.is_(None),
                        Operation.updated_at < cutoff,
                    ),
                ),
            )
            .order_by(Operation.created_at.asc())
            .limit(50)
            .with_for_update(skip_locked=dialect != "sqlite"),
        )
        ids = [row[0] for row in result.all()]
        recovered: list[Operation] = []
        for operation_id in ids:
            operation = await self.session.get(Operation, operation_id)
            if operation is None or operation.state != OperationState.PROCESSING:
                continue
            operation.state = OperationState.PENDING
            operation.claimed_at = None
            operation.claimed_by = None
            operation.claim_token = None
            operation.lease_expires_at = None
            operation.updated_at = now
            recovered.append(operation)
        await self.session.flush()
        return recovered
