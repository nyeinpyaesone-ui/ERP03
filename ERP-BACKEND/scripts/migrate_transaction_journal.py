"""Dry-run-first backfill from the legacy SQLite journal to PostgreSQL."""

from __future__ import annotations

import argparse
import asyncio
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote

from sqlalchemy import select

from app.core.config import settings
from app.db.session import SessionFactory
from app.models.transaction_journal import TransactionJournal


_REQUIRED_COLUMNS = {
    "transaction_id",
    "idempotency_key",
    "operation",
    "amount",
    "currency",
    "metadata_json",
    "status",
    "created_at",
}


def _normalize_legacy_row(row: sqlite3.Row, columns: set[str]) -> dict:
    stored_key = str(row["idempotency_key"])
    business_id = str(row["business_id"]).strip() if "business_id" in columns else ""
    if not business_id and ":" in stored_key:
        business_id, _separator, _raw_key = stored_key.partition(":")
    if not business_id:
        raise ValueError(
            f"Transaction {row['transaction_id']} has no recoverable business_id; "
            "manual reconciliation is required"
        )

    prefix = f"{business_id}:"
    raw_key = stored_key[len(prefix) :] if stored_key.startswith(prefix) else stored_key
    metadata = json.loads(row["metadata_json"])
    if not isinstance(metadata, dict):
        raise ValueError(f"Transaction {row['transaction_id']} metadata is not a JSON object")

    created_at = datetime.fromisoformat(str(row["created_at"]).replace("Z", "+00:00"))
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=UTC)

    return {
        "transaction_id": str(row["transaction_id"]),
        "business_id": business_id,
        "idempotency_key": raw_key,
        "operation": str(row["operation"]),
        "amount": str(row["amount"]),
        "currency": str(row["currency"]),
        "metadata_json": metadata,
        "request_fingerprint": (
            row["request_fingerprint"] if "request_fingerprint" in columns else None
        ),
        "status": "accepted" if str(row["status"]).lower() == "committed" else str(row["status"]),
        "created_at": created_at,
    }


def _legacy_batches(source: Path, batch_size: int):
    uri = f"file:{quote(str(source.resolve()))}?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    connection.row_factory = sqlite3.Row
    try:
        columns = {str(column["name"]) for column in connection.execute("PRAGMA table_info(transactions)")}
        missing = _REQUIRED_COLUMNS - columns
        if missing:
            raise ValueError(f"Legacy journal is missing required columns: {', '.join(sorted(missing))}")

        cursor = connection.execute(
            "SELECT * FROM transactions ORDER BY created_at, transaction_id"
        )
        batch = []
        for row in cursor:
            batch.append(_normalize_legacy_row(row, columns))
            if len(batch) >= batch_size:
                yield batch
                batch = []
        if batch:
            yield batch
    finally:
        connection.close()


def _matches(existing: TransactionJournal, row: dict) -> bool:
    existing_created = existing.created_at
    row_created = row["created_at"]
    if existing_created.tzinfo is None:
        existing_created = existing_created.replace(tzinfo=UTC)
    if row_created.tzinfo is None:
        row_created = row_created.replace(tzinfo=UTC)

    return (
        existing.transaction_id == row["transaction_id"]
        and existing.business_id == row["business_id"]
        and existing.idempotency_key == row["idempotency_key"]
        and existing.operation == row["operation"]
        and existing.amount == row["amount"]
        and existing.currency == row["currency"]
        and existing.metadata_json == row["metadata_json"]
        and existing.request_fingerprint == row["request_fingerprint"]
        and existing.status == row["status"]
        and existing_created == row_created
    )


async def _process_batch(session, batch: list[dict], apply: bool) -> tuple[int, int]:
    already_present = 0
    would_insert = 0

    async with session.begin():
        for row in batch:
            by_id = await session.get(TransactionJournal, row["transaction_id"])
            by_key = await session.scalar(
                select(TransactionJournal).where(
                    TransactionJournal.business_id == row["business_id"],
                    TransactionJournal.idempotency_key == row["idempotency_key"],
                )
            )

            if by_id is not None or by_key is not None:
                if (
                    by_id is None
                    or by_key is None
                    or by_id.transaction_id != by_key.transaction_id
                    or not _matches(by_id, row)
                ):
                    raise ValueError(
                        "Conflicting target journal record for transaction "
                        f"{row['transaction_id']}; import stopped without overwriting data"
                    )
                already_present += 1
                continue

            would_insert += 1
            if apply:
                session.add(TransactionJournal(**row))
                await session.flush()

    return already_present, would_insert


async def run(source: Path, *, apply: bool, batch_size: int) -> None:
    if not settings.database_url.lower().startswith("postgresql"):
        raise RuntimeError("DATABASE_URL must target PostgreSQL; no data was imported")

    source_count = 0
    already_present = 0
    would_insert = 0

    async with SessionFactory() as session:
        for batch in _legacy_batches(source, batch_size):
            source_count += len(batch)
            present, missing = await _process_batch(session, batch, apply)
            already_present += present
            would_insert += missing

    mode = "APPLIED" if apply else "DRY RUN - NO WRITES"
    print(
        f"{mode}: source_rows={source_count}, "
        f"already_present={already_present}, "
        f"{'inserted' if apply else 'would_insert'}={would_insert}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Backfill a frozen SQLite transaction journal into PostgreSQL."
    )
    parser.add_argument("--source", required=True, type=Path, help="Read-only SQLite journal file")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write missing rows to PostgreSQL; without this flag the command is read-only",
    )
    parser.add_argument("--batch-size", type=int, default=500)
    args = parser.parse_args()

    if not args.source.is_file():
        parser.error("source file does not exist or is not a regular file")
    if args.batch_size < 1:
        parser.error("--batch-size must be at least 1")

    asyncio.run(run(args.source, apply=args.apply, batch_size=args.batch_size))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
