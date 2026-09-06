"""
Unit tests for the audit log module (app/core/audit.py).
"""
import dataclasses
from datetime import datetime, timezone

import pytest

from app.core.audit import AuditEvent, AuditLog, audit_log


class TestAuditLogRecord:
    """Tests for AuditLog.record."""

    def test_record_returns_audit_event_with_provided_fields(self):
        log = AuditLog()

        event = log.record(
            actor_id=1,
            actor_kind="user",
            domain="finance",
            action="query.dashboard",
            payload={"a": 1},
        )

        assert isinstance(event, AuditEvent)
        assert event.actor_id == 1
        assert event.actor_kind == "user"
        assert event.domain == "finance"
        assert event.action == "query.dashboard"
        assert event.payload == {"a": 1}

    def test_record_defaults_resource_id_to_none(self):
        log = AuditLog()

        event = log.record(actor_id=1, actor_kind="user", domain="finance", action="query.dashboard")

        assert event.resource_id is None

    def test_record_accepts_explicit_resource_id(self):
        log = AuditLog()

        event = log.record(
            actor_id=1, actor_kind="user", domain="finance", action="command.create",
            resource_id="invoice:42",
        )

        assert event.resource_id == "invoice:42"

    def test_record_defaults_payload_to_empty_dict_when_none(self):
        log = AuditLog()

        event = log.record(actor_id=None, actor_kind="ai_agent", domain="finance", action="query.dashboard",
                            payload=None)

        assert event.payload == {}

    def test_record_supports_none_actor_id(self):
        log = AuditLog()

        event = log.record(actor_id=None, actor_kind="ai_agent", domain="finance", action="query.dashboard")

        assert event.actor_id is None
        assert event.actor_kind == "ai_agent"

    def test_record_sets_utc_aware_timestamp_close_to_now(self):
        log = AuditLog()
        before = datetime.now(timezone.utc)

        event = log.record(actor_id=1, actor_kind="user", domain="d", action="a")

        after = datetime.now(timezone.utc)
        assert event.at.tzinfo is not None
        assert before <= event.at <= after

    def test_record_appends_events_to_internal_list(self):
        log = AuditLog()

        log.record(actor_id=1, actor_kind="user", domain="x", action="a")
        log.record(actor_id=2, actor_kind="user", domain="y", action="b")

        assert len(log._events) == 2
        assert log._events[0].domain == "x"
        assert log._events[1].domain == "y"

    def test_audit_event_is_immutable(self):
        log = AuditLog()
        event = log.record(actor_id=1, actor_kind="user", domain="d", action="a")

        with pytest.raises(dataclasses.FrozenInstanceError):
            event.actor_id = 99


class TestAuditLogRecent:
    """Tests for AuditLog.recent."""

    def test_recent_on_empty_log_returns_empty_list(self):
        log = AuditLog()
        assert log.recent() == []

    def test_recent_respects_limit_and_preserves_order(self):
        log = AuditLog()
        for i in range(5):
            log.record(actor_id=i, actor_kind="user", domain="d", action="a")

        recent = log.recent(limit=3)

        assert [e.actor_id for e in recent] == [2, 3, 4]

    def test_recent_default_limit_is_100(self):
        log = AuditLog()
        for i in range(150):
            log.record(actor_id=i, actor_kind="user", domain="d", action="a")

        recent = log.recent()

        assert len(recent) == 100
        assert recent[0].actor_id == 50
        assert recent[-1].actor_id == 149

    def test_recent_limit_larger_than_event_count_returns_all_events(self):
        log = AuditLog()
        log.record(actor_id=1, actor_kind="user", domain="d", action="a")

        assert len(log.recent(limit=100)) == 1

    def test_recent_limit_zero_returns_empty_list(self):
        log = AuditLog()
        log.record(actor_id=1, actor_kind="user", domain="d", action="a")

        assert log.recent(limit=0) == []

    def test_recent_negative_limit_uses_python_slice_semantics(self):
        """Boundary case: `recent` slices with `self._events[-limit:]`, so a
        negative limit is passed straight through to list slicing (e.g.
        limit=-1 drops the oldest event rather than raising)."""
        log = AuditLog()
        for i in range(3):
            log.record(actor_id=i, actor_kind="user", domain="d", action="a")

        recent = log.recent(limit=-1)

        assert [e.actor_id for e in recent] == [1, 2]


class TestGlobalAuditLogSingleton:
    """Tests for the module-level `audit_log` singleton instance."""

    def test_global_audit_log_is_an_audit_log_instance(self):
        assert isinstance(audit_log, AuditLog)

    def test_global_audit_log_record_is_retrievable_via_recent(self):
        existing_count = len(audit_log.recent(limit=10_000))

        audit_log.record(actor_id=1, actor_kind="user", domain="regression", action="test")

        recent = audit_log.recent(limit=10_000)
        assert len(recent) == existing_count + 1
        assert recent[-1].domain == "regression"