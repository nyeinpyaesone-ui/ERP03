import hashlib
import json
import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class IdempotencyConflict(ValueError):
    """Raised when a key is reused for a different canonical command."""


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
        self.database_path = database_path
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
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
        connection = self._connect()
        try:
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
                    request_fingerprint TEXT,
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
            if "request_fingerprint" not in columns:
                connection.execute(
                    "ALTER TABLE transactions ADD COLUMN request_fingerprint TEXT"
                )
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

    @staticmethod
    def _fingerprint(
        operation: str,
        amount: str,
        currency: str,
        metadata: dict[str, Any],
    ) -> str:
        canonical = json.dumps(
            {
                "operation": operation,
                "amount": amount,
                "currency": currency,
                "metadata": metadata,
            },
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

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
        """Atomically persist a journal entry or replay an identical command.

        This records a journal entry; it does not execute the named domain
        operation. Legacy records without a fingerprint are replayed unchanged
        for compatibility, but cannot be checked for payload equality.
        """
        fingerprint = self._fingerprint(operation, amount, currency, metadata)
        with self._lock:
            connection = self._connect()
            try:
                connection.execute("BEGIN IMMEDIATE")
                existing = connection.execute(
                    "SELECT * FROM transactions WHERE idempotency_key = ?",
                    (idempotency_key,),
                ).fetchone()
                if existing:
                    previous = existing["request_fingerprint"]
                    if previous is not None and previous != fingerprint:
                        raise IdempotencyConflict(
                            "Idempotency key was already used for a different request"
                        )
                    connection.execute("COMMIT")
                    return self._result(existing, replay=True)

                connection.execute(
                    """
                    INSERT INTO transactions
                    (transaction_id, idempotency_key, business_id, operation, amount,
                     currency, metadata_json, request_fingerprint, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'committed', ?)
                    """,
                    (
                        transaction_id,
                        idempotency_key,
                        business_id,
                        operation,
                        amount,
                        currency,
                        json.dumps(metadata, sort_keys=True, separators=(",", ":")),
                        fingerprint,
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
        """Return a journal entry, optionally requiring an exact tenant match."""
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
