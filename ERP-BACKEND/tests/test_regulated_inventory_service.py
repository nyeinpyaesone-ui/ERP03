"""
Unit tests for app/services/regulated_inventory_service.py, focused on
RegulatedInventoryService.release_quality_hold(), which was updated in this PR
to timestamp releases using datetime.now(timezone.utc) instead of the
deprecated datetime.utcnow().
"""
from datetime import datetime, timedelta, timezone

from app.services.regulated_inventory_service import RegulatedInventoryService


class TestReleaseQualityHold:
    """Tests for RegulatedInventoryService.release_quality_hold."""

    def test_returns_expected_structure(self):
        service = RegulatedInventoryService(db_session=None)

        result = service.release_quality_hold(
            batch_id="BATCH-001",
            released_by_user_id="user-42",
            quality_notes="Visual inspection passed",
        )

        assert result["batchId"] == "BATCH-001"
        assert result["releasedBy"] == "user-42"
        assert result["qualityNotes"] == "Visual inspection passed"
        assert result["status"] == "RELEASED"
        assert "releasedAt" in result

    def test_quality_notes_defaults_to_none(self):
        service = RegulatedInventoryService(db_session=None)

        result = service.release_quality_hold(
            batch_id="BATCH-002", released_by_user_id="user-7"
        )

        assert result["qualityNotes"] is None

    def test_released_at_is_timezone_aware_utc_isoformat(self):
        """
        Regression test: `releasedAt` must be an ISO-8601 timestamp derived
        from a timezone-aware UTC datetime (datetime.now(timezone.utc)), not a
        naive datetime.utcnow() timestamp.
        """
        service = RegulatedInventoryService(db_session=None)

        before = datetime.now(timezone.utc)
        result = service.release_quality_hold(
            batch_id="BATCH-003", released_by_user_id="user-1"
        )
        after = datetime.now(timezone.utc)

        released_at = datetime.fromisoformat(result["releasedAt"])

        assert released_at.tzinfo is not None
        assert released_at.utcoffset() == timedelta(0)
        assert before <= released_at <= after

    def test_multiple_releases_have_increasing_timestamps(self):
        service = RegulatedInventoryService(db_session=None)

        first = service.release_quality_hold(batch_id="BATCH-A", released_by_user_id="u1")
        second = service.release_quality_hold(batch_id="BATCH-B", released_by_user_id="u2")

        first_ts = datetime.fromisoformat(first["releasedAt"])
        second_ts = datetime.fromisoformat(second["releasedAt"])

        assert second_ts >= first_ts