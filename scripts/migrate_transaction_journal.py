#!/usr/bin/env python3
"""Import a write-fenced SQLite journal snapshot into ERP03 PostgreSQL operations.

This command is read-only by default. Pass --apply only after the legacy
journal has been write-fenced and a consistent SQLite backup has been taken.
Legacy journal states are imported as PENDING, never COMMITTED: the old journal
did not prove that a PostgreSQL domain mutation had committed.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import NAMESPACE_URL, UUID, uuid5

BACKEND_DIR = Path(__file__).resolve().parents[1] / "ERP-BACKEND"
sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.models import Business  # noqa: E402
from app.models.operations import Operation, OperationState  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sqlite-path",
        required=True,
        type=Path,
        help="Path to the write-fenced SQLite journal snapshot",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Insert missing journal operations into PostgreSQL (default is dry-run)",
    )
    return parser.parse_args()


def open_source(path: Path) -> sqlite3.Connection:
    if not path.is_file():
        raise FileNotFoundError(f"SQLite snapshot does not exist: {path}")
    # URI read-only mode prevents this tool from modifying the source snapshot.
    uri = path.resolve().as_uri() + "?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("BEGIN")
    return connection


def normalize_row(row: sqlite3.Row, columns: set[str]) -> tuple[UUID, str, str, dict, UUID, datetime]:
    raw_key = str(row["idempotency_key"])
    raw_business = str(row["business_id"] or "") if "business_id" in columns else ""
    if not raw_business and ":" in raw_key:
        raw_business = raw_key.split(":", 1)[0]
    try:
        business_id = UUID(raw_business)
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError(
            f"Journal transaction {row['transaction_id']!r} has no valid UUID tenant"
        ) from exc

    prefix = f"{business_id}:"
    operation_id = raw_key if raw_key.startswith(prefix) else f"{prefix}{raw_key}"
    if len(operation_id) > 255:
        raise ValueError(
            f"Journal transaction {row['transaction_id']!r} has an operation ID over 255 chars"
        )

    operation_type = str(row["operation"])
    if not operation_type or len(operation_type) > 100:
        raise ValueError(
            f"Journal transaction {row['transaction_id']!r} has invalid operation type"
        )
    metadata = json.loads(row["metadata_json"])
    if not isinstance(metadata, dict):
        raise ValueError(
            f"Journal transaction {row['transaction_id']!r} metadata must be a JSON object"
        )

    payload = {
        "amount": str(row["amount"]),
        "currency": str(row["currency"]).upper(),
        "metadata": metadata,
    }
    try:
        operation_uuid = UUID(str(row["transaction_id"]))
    except ValueError:
        operation_uuid = uuid5(
            NAMESPACE_URL,
            f"erp03:legacy-transaction:{business_id}:{row['transaction_id']}",
        )

    try:
        created_at = datetime.fromisoformat(str(row["created_at"]))
    except ValueError as exc:
        raise ValueError(
            f"Journal transaction {row['transaction_id']!r} has invalid created_at"
        ) from exc
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=UTC)

    return business_id, operation_id, operation_type, payload, operation_uuid, created_at


def source_rows(connection: sqlite3.Connection):
    columns = {
        item["name"] for item in connection.execute("PRAGMA table_info(transactions)")
    }
    required = {
        "transaction_id",
        "idempotency_key",
        "operation",
        "amount",
        "currency",
        "metadata_json",
        "status",
        "created_at",
    }
    missing = required - columns
    if missing:
        raise ValueError(f"SQLite journal is missing columns: {', '.join(sorted(missing))}")
    rows = connection.execute(
        "SELECT * FROM transactions ORDER BY created_at, transaction_id"
    )
    for row in rows:
        yield normalize_row(row, columns)


async def migrate(snapshot: Path, apply: bool) -> None:
    if not settings.database_url.lower().startswith("postgresql+"):
        raise RuntimeError(
            "DATABASE_URL must target PostgreSQL using an async SQLAlchemy driver"
        )

    connection = open_source(snapshot)
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    inserted = 0
    already_present = 0
    source_count = 0
    checksum = hashlib.sha256()

    try:
        async with session_factory() as session:
            async with session.begin():
                async for item in _async_rows(source_rows(connection)):
                    business_id, operation_id, operation_type, payload, operation_uuid, created_at = item
                    source_count += 1
                    canonical = json.dumps(
                        {
                            "business_id": str(business_id),
                            "operation_id": operation_id,
                            "operation_type": operation_type,
                            "payload": payload,
                        },
                        sort_keys=True,
                        separators=(",", ":"),
                        ensure_ascii=False,
                        allow_nan=False,
                    )
                    checksum.update(canonical.encode("utf-8"))
                    checksum.update(b"\n")

                    business = await session.get(Business, business_id)
                    if business is None:
                        raise ValueError(
                            f"Tenant {business_id} for operation {operation_id!r} "
                            "does not exist in PostgreSQL"
                        )

                    existing = await session.scalar(
                        select(Operation).where(Operation.operation_id == operation_id)
                    )
                    if existing is not None:
                        same_command = (
                            existing.business_id == business_id
                            and existing.operation_type == operation_type
                            and existing.payload_json == payload
                        )
                        if not same_command:
                            raise ValueError(
                                f"Conflicting PostgreSQL operation already exists: {operation_id}"
                            )
                        already_present += 1
                        continue

                    if apply:
                        session.add(
                            Operation(
                                id=operation_uuid,
                                operation_id=operation_id,
                                operation_type=operation_type,
                                state=OperationState.PENDING,
                                business_id=business_id,
                                branch_id=None,
                                payload_json=payload,
                                result_json=None,
                                retry_count=0,
                                max_retries=5,
                                created_at=created_at,
                                updated_at=created_at,
                            )
                        )
                        await session.flush()
                    inserted += 1

        mode = "APPLIED" if apply else "DRY RUN"
        print(
            f"{mode}: source_rows={source_count} "
            f"inserted={inserted} already_present={already_present} "
            f"source_sha256={checksum.hexdigest()}"
        )
        if not apply:
            print("No PostgreSQL rows were inserted. Re-run with --apply after approval.")
    finally:
        connection.rollback()
        connection.close()
        await engine.dispose()


async def _async_rows(rows):
    """Adapt the source iterator to an async loop without blocking the event loop."""
    for item in rows:
        yield item


def main() -> int:
    args = parse_args()
    try:
        asyncio.run(migrate(args.sqlite_path, args.apply))
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
