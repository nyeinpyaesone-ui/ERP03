"""
Unit tests for app/models/regulated_inventory.py.

Covers the migration of `CreatedDateTime` / `LastModifiedDateTime` column
defaults from the deprecated `datetime.utcnow` to a timezone-aware
`datetime.now(timezone.utc)` callable.
"""
from datetime import timezone

from app.models.regulated_inventory import ERPItemMaster, EBMRBatchRecord


class TestERPItemMasterCreatedDateTimeDefault:
    """Tests for ERPItemMaster.CreatedDateTime default."""

    def test_default_is_a_callable(self):
        column = ERPItemMaster.__table__.columns["CreatedDateTime"]
        assert column.default is not None
        assert callable(column.default.arg)

    def test_default_callable_returns_timezone_aware_utc_datetime(self):
        column = ERPItemMaster.__table__.columns["CreatedDateTime"]
        value = column.default.arg()

        assert value.tzinfo is not None
        assert value.tzinfo == timezone.utc

    def test_default_callable_is_evaluated_freshly_each_call(self):
        """The default must be a callable (lambda) evaluated per-row, not a
        single value computed once at class-definition/import time."""
        column = ERPItemMaster.__table__.columns["CreatedDateTime"]
        first = column.default.arg()
        second = column.default.arg()

        assert first.tzinfo == timezone.utc
        assert second.tzinfo == timezone.utc
        # Second call should not be earlier than the first.
        assert second >= first

    def test_persisted_item_master_has_created_datetime_populated(self, db_session):
        """Integration check: inserting a row triggers the Python-side default
        and populates CreatedDateTime."""
        item = ERPItemMaster(
            ItemId="ITEM-TZ-001",
            ItemName="Test Raw Material",
            ItemType="RawMaterial",
            BaseUnitOfMeasure="KG",
            ValuationMethod="FIFO",
        )
        db_session.add(item)
        db_session.commit()
        db_session.refresh(item)

        assert item.CreatedDateTime is not None


class TestEBMRBatchRecordDateTimeDefaults:
    """Tests for EBMRBatchRecord.CreatedDateTime / LastModifiedDateTime defaults."""

    def test_created_datetime_default_is_timezone_aware_utc(self):
        column = EBMRBatchRecord.__table__.columns["CreatedDateTime"]
        value = column.default.arg()

        assert value.tzinfo is not None
        assert value.tzinfo == timezone.utc

    def test_last_modified_datetime_default_is_timezone_aware_utc(self):
        column = EBMRBatchRecord.__table__.columns["LastModifiedDateTime"]
        value = column.default.arg()

        assert value.tzinfo is not None
        assert value.tzinfo == timezone.utc

    def test_last_modified_datetime_onupdate_is_timezone_aware_utc(self):
        column = EBMRBatchRecord.__table__.columns["LastModifiedDateTime"]
        assert column.onupdate is not None
        value = column.onupdate.arg()

        assert value.tzinfo is not None
        assert value.tzinfo == timezone.utc

    def test_created_and_last_modified_use_independent_callables(self):
        """CreatedDateTime and LastModifiedDateTime must not share a single
        pre-computed timestamp; each column has its own default callable."""
        created_column = EBMRBatchRecord.__table__.columns["CreatedDateTime"]
        modified_column = EBMRBatchRecord.__table__.columns["LastModifiedDateTime"]

        assert created_column.default.arg is not modified_column.default.arg

    def test_persisted_batch_record_has_datetime_fields_populated(self, db_session):
        """Integration check: inserting an EBMRBatchRecord (with its required
        ERPItemMaster parent) triggers the Python-side defaults for both
        CreatedDateTime and LastModifiedDateTime."""
        item = ERPItemMaster(
            ItemId="ITEM-TZ-002",
            ItemName="Test Finished Good",
            ItemType="FinishedGood",
            BaseUnitOfMeasure="EA",
            ValuationMethod="FIFO",
        )
        db_session.add(item)
        db_session.commit()

        batch = EBMRBatchRecord(
            batchId="BATCH-TZ-001",
            masterBatchRecordVersion="1.0",
            productId="ITEM-TZ-002",
            productionOrderNumber="PO-001",
            facilitySiteId="SITE-01",
            sourcingAndProcurement="{}",
            productionExecutionLog="{}",
        )
        db_session.add(batch)
        db_session.commit()
        db_session.refresh(batch)

        assert batch.CreatedDateTime is not None
        assert batch.LastModifiedDateTime is not None

    def test_persisted_batch_record_last_modified_updates_on_change(self, db_session):
        """The onupdate default must fire when an existing EBMRBatchRecord row
        is modified, without raising a NameError for the `timezone` import."""
        item = ERPItemMaster(
            ItemId="ITEM-TZ-003",
            ItemName="Test Finished Good 2",
            ItemType="FinishedGood",
            BaseUnitOfMeasure="EA",
            ValuationMethod="FIFO",
        )
        db_session.add(item)
        db_session.commit()

        batch = EBMRBatchRecord(
            batchId="BATCH-TZ-002",
            masterBatchRecordVersion="1.0",
            productId="ITEM-TZ-003",
            productionOrderNumber="PO-002",
            facilitySiteId="SITE-01",
            sourcingAndProcurement="{}",
            productionExecutionLog="{}",
        )
        db_session.add(batch)
        db_session.commit()
        db_session.refresh(batch)
        original_last_modified = batch.LastModifiedDateTime

        import time
        time.sleep(0.01)

        batch.masterBatchRecordVersion = "1.1"
        db_session.commit()
        db_session.refresh(batch)

        assert batch.LastModifiedDateTime is not None
        assert batch.LastModifiedDateTime >= original_last_modified
