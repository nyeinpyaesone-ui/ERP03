import json
import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


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
    """Durable transaction journal with atomic idempotency and tenant isolation."""

    def __init__(self, database_path: str) -> None:
        """Initialize the journal and migrate legacy databases in place."""
        self.database_path = database_path
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        """Open a connection; callers are responsible for closing it."""
        connection = sqlite3.connect(
            self.database_path,
            timeout=10,
            isolation_level=None,
            check_same_thread=False,
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def _initialize(self) -> None:
        """Create the journal and apply a serialized, backward-compatible migration."""
        connection = self._connect()
        try:
            # WAL is persistent database configuration; do not repeat it on each request.
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS transactions (
                    transaction_id TEXT PRIMARY KEY,
                    idempotency_key TEXT NOT NULL UNIQUE,
                    business_id TEXT NOT NULL DEFAULT '',
                    operation TEXT NOT NULL,
                    amount TEXT NOT NULL,
                    currency TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            columns = {
                column["name"]
                for column in connection.execute("PRAGMA table_info(transactions)")
            }
            if "business_id" not in columns:
                connection.execute(
                    "ALTER TABLE transactions ADD COLUMN business_id TEXT NOT NULL DEFAULT ''"
                )

            # Older API records encoded tenant ownership in "business_id:key".
            # Recover that tenant marker once so legacy records remain accessible only
            # to the business that originally submitted them.
            connection.execute(
                """
                UPDATE transactions
                SET business_id = substr(idempotency_key, 1, instr(idempotency_key, ':') - 1)
                WHERE business_id = '' AND instr(idempotency_key, ':') > 0
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_transactions_business_transaction
                ON transactions (business_id, transaction_id)
                """
            )
            connection.execute("COMMIT")
        except Exception:
            try:
                connection.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            raise
        finally:
            connection.close()

    def execute(
        self,
        *,
        transaction_id: str,
        idempotency_key: str,
        operation: str,
        amount: str,
        currency: str,
        metadata: dict[str, Any],
        business_id: str = "",
    ) -> TransactionResult:
        """Atomically persist a journal entry or replay the existing entry for a key.

        This records a transaction-journal entry; it does not execute the named
        business operation. The caller must execute domain mutations in their own
        database transaction and must not treat this journal entry alone as proof
        that an invoice, payment, or inventory mutation was performed.
        """
        with self._lock:
            connection = self._connect()
            try:
                connection.execute("BEGIN IMMEDIATE")
                existing = connection.execute(
                    "SELECT * FROM transactions WHERE idempotency_key = ?",
                    (idempotency_key,),
                ).fetchone()
                if existing:
                    connection.execute("COMMIT")
                    return self._result(existing, replay=True)

                connection.execute(
                    """
                    INSERT INTO transactions
                    (transaction_id, idempotency_key, business_id, operation, amount,
                     currency, metadata_json, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'committed', ?)
                    """,
                    (
                        transaction_id,
                        idempotency_key,
                        business_id,
                        operation,
                        amount,
                        currency,
                        json.dumps(metadata, sort_keys=True, separators=(",", ":")),
                        datetime.now(timezone.utc).isoformat(),
                    ),
                )
                connection.execute("COMMIT")
                row = connection.execute(
                    "SELECT * FROM transactions WHERE transaction_id = ?",
                    (transaction_id,),
                ).fetchone()
                if row is None:
                    raise RuntimeError("Transaction committed but could not be reloaded")
                return self._result(row, replay=False)
            except Exception:
                try:
                    connection.execute("ROLLBACK")
                except sqlite3.Error:
                    pass
                raise
            finally:
                connection.close()

    @staticmethod
    def _result(row: sqlite3.Row, *, replay: bool) -> TransactionResult:
        """Decode a journal row and set its replay flag."""
        return TransactionResult(
            transaction_id=row["transaction_id"],
            status=row["status"],
            operation=row["operation"],
            amount=row["amount"],
            currency=row["currency"],
            metadata=json.loads(row["metadata_json"]),
            idempotent_replay=replay,
        )

    def get(
        self,
        transaction_id: str,
        *,
        business_id: str | None = None,
    ) -> TransactionResult | None:
        """Return a journal entry, optionally requiring an exact tenant match.

        API handlers must always supply business_id. The unscoped form remains
        available for trusted internal maintenance and backward-compatible tests.
        """
        connection = self._connect()
        try:
            if business_id is None:
                row = connection.execute(
                    "SELECT * FROM transactions WHERE transaction_id = ?",
                    (transaction_id,),
                ).fetchone()
            else:
                row = connection.execute(
                    """
                    SELECT * FROM transactions
                    WHERE transaction_id = ? AND business_id = ?
                    """,
                    (transaction_id, business_id),
                ).fetchone()
            return self._result(row, replay=False) if row else None
        finally:
            connection.close()
