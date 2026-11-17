"""Tests for the write-fenced legacy transaction-journal importer."""

import importlib.util
import sqlite3
from pathlib import Path
from uuid import uuid4

import pytest

SCRIPT_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "migrate_transaction_journal.py"
)
SPEC = importlib.util.spec_from_file_location("migrate_transaction_journal", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
MIGRATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MIGRATOR)


def _snapshot(
    path: Path,
    *,
    transaction_id: str | None = None,
    business_id: str | None = None,
):
    tenant_id = business_id or str(uuid4())
    transaction_id = transaction_id or uuid4().hex
    connection = sqlite3.connect(path)
    try:
        connection.execute(
            """
            CREATE TABLE transactions (
                transaction_id TEXT PRIMARY KEY,
                idempotency_key TEXT NOT NULL UNIQUE,
                business_id TEXT NOT NULL,
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
        connection.execute(
            """
            INSERT INTO transactions
            (transaction_id, idempotency_key, business_id, operation, amount,
             currency, metadata_json, request_fingerprint, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                transaction_id,
                f"{tenant_id.upper()}:legacy-key-001",
                tenant_id,
                "invoice.create",
                "42.00",
                "mmk",
                '{"invoice":"LEGACY-001"}',
                None,
                "accepted",
                "2026-11-01T12:30:00+00:00",
            ),
        )
        connection.commit()
    finally:
        connection.close()
    return tenant_id, transaction_id


def test_import_normalization_preserves_tenant_key_and_transaction_uuid(tmp_path):
    tenant_id, transaction_id = _snapshot(tmp_path / "journal.sqlite3")
    source = MIGRATOR.open_source(tmp_path / "journal.sqlite3")
    try:
        rows = list(MIGRATOR.source_rows(source))
    finally:
        source.rollback()
        source.close()

    assert len(rows) == 1
    business_id, operation_id, operation_type, payload, operation_uuid, created_at = rows[0]
    assert str(business_id) == tenant_id
    assert operation_id == f"{tenant_id}:legacy-key-001"
    assert operation_type == "invoice.create"
    assert payload == {
        "amount": "42.00",
        "currency": "MMK",
        "metadata": {"invoice": "LEGACY-001"},
    }
    assert operation_uuid.hex == transaction_id
    assert created_at.tzinfo is not None


def test_import_rejects_unknown_tenant_identity(tmp_path):
    _snapshot(
        tmp_path / "journal.sqlite3",
        business_id="not-a-uuid",
    )
    source = MIGRATOR.open_source(tmp_path / "journal.sqlite3")
    try:
        with pytest.raises(ValueError, match="valid UUID tenant"):
            list(MIGRATOR.source_rows(source))
    finally:
        source.rollback()
        source.close()


def test_import_rejects_non_uuid_legacy_transaction_ids(tmp_path):
    _snapshot(tmp_path / "journal.sqlite3", transaction_id="legacy-id-not-uuid")
    source = MIGRATOR.open_source(tmp_path / "journal.sqlite3")
    try:
        with pytest.raises(ValueError, match="is not a UUID"):
            list(MIGRATOR.source_rows(source))
    finally:
        source.rollback()
        source.close()


def test_importer_opens_legacy_snapshot_read_only(tmp_path):
    _snapshot(tmp_path / "journal.sqlite3")
    source = MIGRATOR.open_source(tmp_path / "journal.sqlite3")
    try:
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            source.execute("DELETE FROM transactions")
    finally:
        source.rollback()
        source.close()
