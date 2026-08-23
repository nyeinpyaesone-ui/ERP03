"""
Unit tests for the audit log module (app/core/audit.py).
"""
import dataclasses
from datetime import datetime, timezone

import pytest

from app.core.audit import AuditEvent, AuditLog, audit_log as global_audit_log


class TestAuditLogRecord:
    """Tests for AuditLog.record."""

    def test_record_creates_event_with_expected_fields(self):
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
        assert event.resource_id is None

    def test_record_sets_utc_timestamp(self):
        log = AuditLog()
        before = datetime.now(timezone.utc)

        event = log.record(actor_id=1, actor_kind="user", domain="d", action="a")

        after = datetime.now(timezone.utc)
        assert event.at.tzinfo is not None
        assert before <= event.at <= after

    def test_record_defaults_payload_to_empty_dict(self):
        log = AuditLog()

        event = log.record(actor_id=None, actor_kind="ai_agent", domain="finance", action="query.dashboard")

        assert event.payload == {}

    def test_record_accepts_resource_id(self):
        log = AuditLog()

        event = log.record(
            actor_id=2, actor_kind="user", domain="finance", action="command.create", resource_id="invoice:42",
        )

        assert event.resource_id == "invoice:42"

    def test_record_appends_to_internal_events_list(self):
        log = AuditLog()

        log.record(actor_id=1, actor_kind="user", domain="x", action="a")
        log.record(actor_id=2, actor_kind="user", domain="y", action="b")

        assert len(log._events) == 2

    def test_audit_event_is_frozen(self):
        log = AuditLog()
        event = log.record(actor_id=1, actor_kind="user", domain="d", action="a")

        with pytest.raises(dataclasses.FrozenInstanceError):
            event.actor_id = 99


class TestAuditLogRecent:
    """Tests for AuditLog.recent."""

    def test_recent_returns_events_in_insertion_order(self):
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

    def test_recent_on_empty_log_returns_empty_list(self):
        log = AuditLog()

        assert log.recent() == []

    def test_recent_limit_larger_than_events_returns_all(self):
        log = AuditLog()
        log.record(actor_id=1, actor_kind="user", domain="d", action="a")

        recent = log.recent(limit=100)

        assert len(recent) == 1


class TestGlobalAuditLogSingleton:
    """Tests for the module-level audit_log singleton."""

    def test_global_audit_log_is_audit_log_instance(self):
        assert isinstance(global_audit_log, AuditLog)