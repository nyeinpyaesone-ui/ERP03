"""
Unit tests for regulated inventory models (app/models/regulated_inventory.py).

Focuses on the timezone-aware timestamp defaults introduced when the models
were migrated from the deprecated ``datetime.utcnow()`` to
``datetime.now(timezone.utc)``.
"""
import json
import time
from datetime import datetime, timedelta, timezone

import pytest

from app.models.regulated_inventory import ERPItemMaster, EBMRBatchRecord


def _invoke_default(default_obj):
    """Invoke a SQLAlchemy ColumnDefault's callable.

    SQLAlchemy wraps zero-argument default callables as ``lambda ctx: fn()``
    internally, so the introspected callable may expect an execution-context
    positional argument. This helper works whether or not that wrapping has
    occurred, keeping the test resilient to SQLAlchemy version differences.
    """
    fn = default_obj.arg
    try:
        return fn()
    except TypeError:
        return fn(None)


class TestERPItemMasterCreatedDateTimeDefault:
    """Tests for ERPItemMaster.CreatedDateTime default value generation."""

    def test_default_is_callable(self):
        """The column default must be a callable, not a pre-computed value."""
        column = ERPItemMaster.__table__.columns["CreatedDateTime"]
        assert column.default is not None
        assert column.default.is_callable

    def test_default_callable_returns_timezone_aware_utc_datetime(self):
        """Invoking the default callable must produce a tz-aware UTC datetime."""
        column = ERPItemMaster.__table__.columns["CreatedDateTime"]

        before = datetime.now(timezone.utc)
        value = _invoke_default(column.default)
        after = datetime.now(timezone.utc)

        assert isinstance(value, datetime)
        assert value.tzinfo is not None
        assert value.utcoffset() == timedelta(0)
        assert before - timedelta(seconds=5) <= value <= after + timedelta(seconds=5)

    def test_default_callable_reevaluated_on_each_call(self):
        """Each invocation should reflect the current time, not a fixed value."""
        column = ERPItemMaster.__table__.columns["CreatedDateTime"]

        first = _invoke_default(column.default)
        time.sleep(0.01)
        second = _invoke_default(column.default)

        assert second > first

    def test_created_datetime_populated_on_insert(self, db_session):
        """Inserting an item without an explicit CreatedDateTime populates it."""
        before = datetime.now(timezone.utc)
        item = ERPItemMaster(
            ItemId="ITEM-001",
            ItemName="Widget",
            ItemType="RawMaterial",
            BaseUnitOfMeasure="EA",
            ValuationMethod="FIFO",
        )
        db_session.add(item)
        db_session.commit()
        db_session.refresh(item)
        after = datetime.now(timezone.utc)

        assert item.CreatedDateTime is not None
        created = item.CreatedDateTime
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)

        assert before - timedelta(seconds=5) <= created <= after + timedelta(seconds=5)
        # Boolean defaults untouched by this change should remain correct
        assert item.IsBatchTracked is True
        assert item.IsSerialized is False


class TestEBMRBatchRecordTimestampDefaults:
    """Tests for EBMRBatchRecord.CreatedDateTime / LastModifiedDateTime defaults."""

    def test_created_datetime_default_is_callable(self):
        column = EBMRBatchRecord.__table__.columns["CreatedDateTime"]
        assert column.default is not None
        assert column.default.is_callable

    def test_last_modified_datetime_default_and_onupdate_are_callable(self):
        column = EBMRBatchRecord.__table__.columns["LastModifiedDateTime"]
        assert column.default is not None
        assert column.default.is_callable
        assert column.onupdate is not None
        assert column.onupdate.is_callable

    def test_created_and_last_modified_defaults_return_timezone_aware_utc(self):
        created_column = EBMRBatchRecord.__table__.columns["CreatedDateTime"]
        modified_column = EBMRBatchRecord.__table__.columns["LastModifiedDateTime"]

        created_value = _invoke_default(created_column.default)
        modified_default_value = _invoke_default(modified_column.default)
        modified_onupdate_value = _invoke_default(modified_column.onupdate)

        for value in (created_value, modified_default_value, modified_onupdate_value):
            assert isinstance(value, datetime)
            assert value.tzinfo is not None
            assert value.utcoffset() == timedelta(0)

    def _make_item_master(self, db_session, item_id="ITEM-EBMR-001"):
        item = ERPItemMaster(
            ItemId=item_id,
            ItemName="Batch Tracked Product",
            ItemType="FinishedGood",
            BaseUnitOfMeasure="EA",
            ValuationMethod="StandardCost",
        )
        db_session.add(item)
        db_session.commit()
        return item

    def test_created_and_last_modified_populated_on_insert(self, db_session):
        """Inserting a batch record without explicit timestamps populates both
        CreatedDateTime and LastModifiedDateTime with timezone-consistent values."""
        self._make_item_master(db_session)

        before = datetime.now(timezone.utc)
        ebmr = EBMRBatchRecord(
            batchId="BATCH-001",
            masterBatchRecordVersion="1.0",
            productId="ITEM-EBMR-001",
            productionOrderNumber="PO-001",
            facilitySiteId="SITE-01",
            sourcingAndProcurement=json.dumps({"supplier": "Acme"}),
            productionExecutionLog=json.dumps({"steps": []}),
        )
        db_session.add(ebmr)
        db_session.commit()
        db_session.refresh(ebmr)
        after = datetime.now(timezone.utc)

        assert ebmr.CreatedDateTime is not None
        assert ebmr.LastModifiedDateTime is not None

        for value in (ebmr.CreatedDateTime, ebmr.LastModifiedDateTime):
            normalized = value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
            assert before - timedelta(seconds=5) <= normalized <= after + timedelta(seconds=5)

    def test_last_modified_datetime_refreshes_on_update(self, db_session):
        """The onupdate default must fire when an existing record is modified."""
        self._make_item_master(db_session)

        ebmr = EBMRBatchRecord(
            batchId="BATCH-002",
            masterBatchRecordVersion="1.0",
            productId="ITEM-EBMR-001",
            productionOrderNumber="PO-002",
            facilitySiteId="SITE-01",
            sourcingAndProcurement=json.dumps({}),
            productionExecutionLog=json.dumps({}),
        )
        db_session.add(ebmr)
        db_session.commit()
        db_session.refresh(ebmr)

        original_created = ebmr.CreatedDateTime
        original_modified = ebmr.LastModifiedDateTime

        time.sleep(0.01)

        ebmr.productionOrderNumber = "PO-002-REV1"
        db_session.commit()
        db_session.refresh(ebmr)

        assert ebmr.CreatedDateTime == original_created
        assert ebmr.LastModifiedDateTime >= original_modified