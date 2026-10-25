"""PostgreSQL/SQLite-backed durable transaction journal with atomic idempotency."""

import json
from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(frozen=True)
class TransactionResult:
    transaction_id: str
    status: str
    operation: str
    amount: str
    currency: str
    metadata: dict[str, Any]
    idempotent_replay: bool = False


class TransactionStore:
    """Durable transaction journal with atomic idempotency and tenant isolation.

    Works with both PostgreSQL and SQLite backends through SQLAlchemy ORM.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def execute(
        self,
        *,
        transaction_id: str,
        idempotency_key: str,
        operation: str,
        amount: str,
        currency: str,
        metadata: dict[str, Any],
    ) -> TransactionResult:
        """Atomically record a committed entry or replay an existing key's entry.

        Uses a transaction-bound SELECT-then-INSERT pattern that is safe
        under concurrent access because the database serializes writers.
        Returns ``idempotent_replay=True`` when the key already existed.
        """
        async with self.session.begin():
            # Check if the idempotency key already exists.
            from sqlalchemy import text as sa_text

            existing = await self.session.execute(
                sa_text("""
                    SELECT transaction_id, status, operation, amount, currency, metadata_json
                    FROM transaction_journal
                    WHERE idempotency_key = :idem_key
                """),
                {"idem_key": idempotency_key},
            )
            existing_row = existing.first()
            if existing_row is not None:
                return TransactionResult(
                    transaction_id=existing_row.transaction_id,
                    status=existing_row.status,
                    operation=existing_row.operation,
                    amount=str(existing_row.amount),
                    currency=existing_row.currency,
                    metadata=json.loads(existing_row.metadata_json),
                    idempotent_replay=True,
                )

            # Insert the new journal entry.
            result = await self.session.execute(
                sa_text("""
                    INSERT INTO transaction_journal
                        (transaction_id, idempotency_key, operation, amount, currency,
                         metadata_json, status, created_at)
                    VALUES (:tx_id, :idem_key, :op, :amt, :curr, :meta,
                            'committed', CURRENT_TIMESTAMP)
                    ON CONFLICT (idempotency_key) DO NOTHING
                    RETURNING transaction_id, status, operation, amount, currency,
                              metadata_json
                """),
                {
                    "tx_id": transaction_id,
                    "idem_key": idempotency_key,
                    "op": operation,
                    "amt": str(amount),
                    "curr": currency,
                    "meta": json.dumps(metadata, sort_keys=True, separators=(",", ":")),
                },
            )
            insert_row = result.first()
            if insert_row is not None:
                return TransactionResult(
                    transaction_id=insert_row.transaction_id,
                    status=insert_row.status,
                    operation=insert_row.operation,
                    amount=str(insert_row.amount),
                    currency=insert_row.currency,
                    metadata=json.loads(insert_row.metadata_json),
                    idempotent_replay=False,
                )

            # Key already existed — return the original entry.
            existing = await self.session.execute(
                sa_text("""
                    SELECT transaction_id, status, operation, amount, currency, metadata_json
                    FROM transaction_journal
                    WHERE idempotency_key = :idem_key
                """),
                {"idem_key": idempotency_key},
            )
            existing_row = existing.first()
            if existing_row is None:
                raise RuntimeError(
                    "Idempotency key conflict but no existing row found "
                    f"for key {idempotency_key!r}"
                )
            return TransactionResult(
                transaction_id=existing_row.transaction_id,
                status=existing_row.status,
                operation=existing_row.operation,
                amount=str(existing_row.amount),
                currency=existing_row.currency,
                metadata=json.loads(existing_row.metadata_json),
                idempotent_replay=True,
            )

    async def get(
        self,
        transaction_id: str,
        business_id: str | None = None,
    ) -> TransactionResult | None:
        """Return the entry by transaction ID, optionally filtering by business."""
        from sqlalchemy import text as sa_text

        if business_id is not None:
            result = await self.session.execute(
                sa_text("""
                    SELECT transaction_id, status, operation, amount, currency, metadata_json
                    FROM transaction_journal
                    WHERE transaction_id = :tx_id AND idempotency_key LIKE :business_prefix
                """),
                {
                    "tx_id": transaction_id,
                    "business_prefix": f"{business_id}:%",
                },
            )
        else:
            result = await self.session.execute(
                sa_text("""
                    SELECT transaction_id, status, operation, amount, currency, metadata_json
                    FROM transaction_journal
                    WHERE transaction_id = :tx_id
                """),
                {"tx_id": transaction_id},
            )
        row = result.first()
        if row is None:
            return None
        return TransactionResult(
            transaction_id=row.transaction_id,
            status=row.status,
            operation=row.operation,
            amount=str(row.amount),
            currency=row.currency,
            metadata=json.loads(row.metadata_json),
            idempotent_replay=False,
        )
