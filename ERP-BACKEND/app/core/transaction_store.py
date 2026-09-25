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
    """Durable transaction journal with atomic idempotency semantics."""

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
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS transactions (
                    transaction_id TEXT PRIMARY KEY,
                    idempotency_key TEXT NOT NULL UNIQUE,
                    operation TEXT NOT NULL,
                    amount TEXT NOT NULL,
                    currency TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def execute(
        self,
        *,
        transaction_id: str,
        idempotency_key: str,
        operation: str,
        amount: str,
        currency: str,
        metadata: dict[str, Any],
    ) -> TransactionResult:
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
                    (transaction_id, idempotency_key, operation, amount, currency,
                     metadata_json, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, 'committed', ?)
                    """,
                    (
                        transaction_id,
                        idempotency_key,
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
        return TransactionResult(
            transaction_id=row["transaction_id"],
            status=row["status"],
            operation=row["operation"],
            amount=row["amount"],
            currency=row["currency"],
            metadata=json.loads(row["metadata_json"]),
            idempotent_replay=replay,
        )

    def get(self, transaction_id: str) -> TransactionResult | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM transactions WHERE transaction_id = ?",
                (transaction_id,),
            ).fetchone()
            return self._result(row, replay=False) if row else None
