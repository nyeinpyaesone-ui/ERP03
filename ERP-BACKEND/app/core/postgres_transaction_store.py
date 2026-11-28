"""Async SQLAlchemy store for the shared PostgreSQL transaction journal."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.transaction_store import IdempotencyConflict, TransactionResult, TransactionStore
from app.models.transaction_journal import TransactionJournal


class PostgresTransactionStore:
    """Persist accepted journal entries with tenant-scoped database uniqueness.

    The caller owns the outer transaction and must commit after execute().
    The savepoint isolates an idempotency uniqueness race without invalidating
    the caller's session.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def execute(
        self,
        *,
        transaction_id: str,
        business_id: str,
        idempotency_key: str,
        operation: str,
        amount: str,
        currency: str,
        metadata: dict[str, Any],
    ) -> TransactionResult:
        fingerprint = TransactionStore._fingerprint(operation, amount, currency, metadata)
        entry = TransactionJournal(
            transaction_id=transaction_id,
            business_id=business_id,
            idempotency_key=idempotency_key,
            operation=operation,
            amount=amount,
            currency=currency,
            metadata_json=metadata,
            request_fingerprint=fingerprint,
            status="accepted",
        )

        try:
            async with self.session.begin_nested():
                self.session.add(entry)
                await self.session.flush()
        except IntegrityError:
            existing = await self.session.scalar(
                select(TransactionJournal).where(
                    TransactionJournal.business_id == business_id,
                    TransactionJournal.idempotency_key == idempotency_key,
                )
            )
            if existing is None:
                # A transaction_id collision or another unexpected constraint
                # violation is not an idempotent replay.
                raise
            self._verify_replay(existing, fingerprint)
            return self._to_result(existing, replay=True)

        return self._to_result(entry, replay=False)

    async def get(
        self,
        transaction_id: str,
        *,
        business_id: str,
    ) -> TransactionResult | None:
        entry = await self.session.scalar(
            select(TransactionJournal).where(
                TransactionJournal.transaction_id == transaction_id,
                TransactionJournal.business_id == business_id,
            )
        )
        return self._to_result(entry, replay=False) if entry is not None else None

    @staticmethod
    def _verify_replay(entry: TransactionJournal, fingerprint: str) -> None:
        if entry.request_fingerprint is None:
            raise IdempotencyConflict(
                "Idempotency key was already used without a fingerprint; "
                "payload equality cannot be verified",
                code="IDEMPOTENCY_KEY_REUSED",
            )
        if entry.request_fingerprint != fingerprint:
            raise IdempotencyConflict(
                "Idempotency key was already used for a different request",
                code="IDEMPOTENCY_PAYLOAD_MISMATCH",
            )

    @staticmethod
    def _to_result(entry: TransactionJournal, *, replay: bool) -> TransactionResult:
        return TransactionResult(
            transaction_id=entry.transaction_id,
            status=entry.status,
            operation=entry.operation,
            amount=entry.amount,
            currency=entry.currency,
            metadata=entry.metadata_json,
            idempotent_replay=replay,
        )
