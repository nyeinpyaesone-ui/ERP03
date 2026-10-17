import contextlib
import json
import sqlite3
import threading
from dataclasses import dataclass
from datetime import UTC, datetime
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
        """Initialize the SQLite journal, creating parent directories as needed.

        Filesystem errors and SQLite initialization errors propagate to callers.
        """
        self.database_path = database_path
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        """Open an autocommit connection with named rows, WAL, and foreign keys.

        Wait up to 10 seconds for database locks. The caller must close the
        returned connection; SQLite connection and configuration errors propagate.
        """
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
        """Create the journal table and indexes if absent, propagating SQLite errors."""
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS transactions (
                    transaction_id TEXT PRIMARY KEY,
                    business_id TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    amount TEXT NOT NULL,
                    currency TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            # Tenant-scoped idempotency: the same client key in two businesses
            # must not collide. Legacy databases may still hold the old global
            # UNIQUE constraint on idempotency_key; migrate by rebuilding the
            # table when its column set is outdated.
            columns = {row["name"] for row in connection.execute("PRAGMA table_info(transactions)")}
            if "business_id" not in columns:
                connection.execute("BEGIN IMMEDIATE")
                try:
                    connection.execute(
                        """
                        CREATE TABLE transactions_new (
                            transaction_id TEXT PRIMARY KEY,
                            business_id TEXT NOT NULL DEFAULT '',
                            idempotency_key TEXT NOT NULL,
                            operation TEXT NOT NULL,
                            amount TEXT NOT NULL,
                            currency TEXT NOT NULL,
                            metadata_json TEXT NOT NULL,
                            status TEXT NOT NULL,
                            created_at TEXT NOT NULL
                        )
                        """
                    )
                    connection.execute(
                        """
                        INSERT INTO transactions_new
                        SELECT transaction_id, '', substr(idempotency_key,
                               instr(idempotency_key, ':') + 1),
                               operation, amount, currency, metadata_json,
                               status, created_at
                        FROM transactions
                        """
                    )
                    connection.execute("DROP TABLE transactions")
                    connection.execute("ALTER TABLE transactions_new RENAME TO transactions")
                    connection.execute("COMMIT")
                except Exception:
                    connection.execute("ROLLBACK")
                    raise
            connection.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS ux_transactions_business_idempotency "
                "ON transactions (business_id, idempotency_key)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS ix_transactions_business ON transactions (business_id)"
            )

    def execute(
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
        """Atomically record a committed entry or replay an existing key's entry.

        Idempotency keys are scoped to ``business_id``: a reused key within one
        business returns the original fields with ``idempotent_replay=True``,
        ignoring all other supplied fields, while the same key in another
        business records a new entry. New entries use the supplied transaction
        ID and return the flag as False. The amount is stored as supplied,
        without rounding or validation; metadata must be JSON-serializable.
        This only writes the journal and does not perform the named business
        operation.

        SQLite and metadata encoding/decoding errors propagate. Failures during
        transaction handling trigger an attempted rollback; rollback errors are
        suppressed. Raise RuntimeError if a newly committed entry cannot be
        reloaded. Errors after commit do not undo it.
        """
        with self._lock:
            connection = self._connect()
            try:
                connection.execute("BEGIN IMMEDIATE")
                # Serialize metadata *inside* the write transaction so a
                # non-serializable payload fails before any row is inserted;
                # this keeps failed writes fully rolled back and retryable.
                metadata_json = json.dumps(metadata, sort_keys=True, separators=(",", ":"))
                existing = connection.execute(
                    "SELECT * FROM transactions WHERE business_id = ? AND idempotency_key = ?",
                    (business_id, idempotency_key),
                ).fetchone()
                if existing:
                    connection.execute("COMMIT")
                    return self._result(existing, replay=True)

                connection.execute(
                    """
                    INSERT INTO transactions
                    (transaction_id, business_id, idempotency_key, operation, amount,
                     currency, metadata_json, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'committed', ?)
                    """,
                    (
                        transaction_id,
                        business_id,
                        idempotency_key,
                        operation,
                        amount,
                        currency,
                        metadata_json,
                        datetime.now(UTC).isoformat(),
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
                with contextlib.suppress(sqlite3.Error):
                    connection.execute("ROLLBACK")
                raise
            finally:
                connection.close()

    @staticmethod
    def _result(row: sqlite3.Row, *, replay: bool) -> TransactionResult:
        """Decode a journal row and set its replay flag from ``replay``.

        Missing columns raise IndexError; invalid metadata JSON raises
        json.JSONDecodeError.
        """
        return TransactionResult(
            transaction_id=row["transaction_id"],
            status=row["status"],
            operation=row["operation"],
            amount=row["amount"],
            currency=row["currency"],
            metadata=json.loads(row["metadata_json"]),
            idempotent_replay=replay,
        )

    def get(self, transaction_id: str, *, business_id: str) -> TransactionResult | None:
        """Return the entry owned by ``business_id``, or None if absent/foreign.

        Entries belonging to another tenant are reported as missing so that
        existence is never leaked across businesses. SQLite errors and
        metadata JSON decoding errors propagate to callers.
        """
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM transactions WHERE transaction_id = ? AND business_id = ?",
                (transaction_id, business_id),
            ).fetchone()
            return self._result(row, replay=False) if row else None
