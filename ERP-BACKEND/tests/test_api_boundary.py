"""
Unit tests for the ERP API boundary module (app/api_boundary/boundary.py).
"""
import pytest
from unittest.mock import MagicMock, patch

from app.api_boundary.boundary import (
    AI_WRITE_ALLOWLIST,
    BoundaryError,
    ERPBoundary,
    PermissionDenied,
    has_permission,
    boundary as global_boundary,
)


class DummyActor:
    def __init__(self, id=1, actor_kind="user"):
        self.id = id
        self.actor_kind = actor_kind


class TestHasPermission:
    """Tests for the has_permission helper."""

    def test_ai_agent_can_read(self):
        actor = DummyActor(actor_kind="ai_agent")
        assert has_permission(actor, "finance", "read", db=None) is True

    def test_ai_agent_cannot_write(self):
        actor = DummyActor(actor_kind="ai_agent")
        assert has_permission(actor, "finance", "write", db=None) is False

    def test_regular_user_allowed_to_write(self):
        actor = DummyActor(actor_kind="user")
        assert has_permission(actor, "finance", "write", db=None) is True

    def test_actor_without_actor_kind_attribute_treated_as_non_ai(self):
        actor = object()
        assert has_permission(actor, "finance", "write", db=None) is True


class TestERPBoundaryQuery:
    """Tests for ERPBoundary.query."""

    def test_unknown_query_raises_boundary_error(self):
        b = ERPBoundary()
        with pytest.raises(BoundaryError, match="Unknown query"):
            b.query(name="finance.dashboard", actor=DummyActor(), db=MagicMock())

    def test_unauthenticated_actor_raises_boundary_error(self):
        b = ERPBoundary()
        b.register_query("finance.dashboard", MagicMock())
        with pytest.raises(BoundaryError, match="Unauthenticated"):
            b.query(name="finance.dashboard", actor=None, db=MagicMock())

    def test_query_success_calls_registered_function_with_params(self):
        b = ERPBoundary()
        fn = MagicMock(return_value={"ok": True})
        b.register_query("finance.dashboard", fn)
        db = MagicMock()
        actor = DummyActor(id=9, actor_kind="user")

        result = b.query(name="finance.dashboard", actor=actor, db=db, params={"a": 1})

        assert result == {"ok": True}
        fn.assert_called_once_with(db=db, a=1)

    def test_query_success_records_audit_log(self):
        b = ERPBoundary()
        b.register_query("finance.dashboard", MagicMock(return_value={}))
        actor = DummyActor(id=9, actor_kind="user")

        with patch("app.api_boundary.boundary.audit_log.record") as mock_record:
            b.query(name="finance.dashboard", actor=actor, db=MagicMock())

        mock_record.assert_called_once()
        _, kwargs = mock_record.call_args
        assert kwargs["actor_id"] == 9
        assert kwargs["actor_kind"] == "user"
        assert kwargs["domain"] == "finance"
        assert kwargs["action"] == "query.dashboard"

    def test_query_without_params_defaults_to_empty_dict(self):
        b = ERPBoundary()
        fn = MagicMock(return_value=None)
        b.register_query("finance.dashboard", fn)
        db = MagicMock()

        b.query(name="finance.dashboard", actor=DummyActor(), db=db)

        fn.assert_called_once_with(db=db)


class TestERPBoundaryCommand:
    """Tests for ERPBoundary.command."""

    def test_unknown_command_raises_boundary_error(self):
        b = ERPBoundary()
        with pytest.raises(BoundaryError, match="Unknown command"):
            b.command(name="finance.create", actor=DummyActor(), db=MagicMock())

    def test_ai_agent_blocked_from_writing_to_non_allowlisted_domain(self):
        b = ERPBoundary()
        b.register_command("finance.create", MagicMock())
        actor = DummyActor(actor_kind="ai_agent")

        with pytest.raises(BoundaryError, match="may not write"):
            b.command(name="finance.create", actor=actor, db=MagicMock())

    def test_ai_agent_allowed_when_domain_in_allowlist(self):
        b = ERPBoundary()
        fn = MagicMock(return_value="ok")
        b.register_command("finance.create", fn)
        actor = DummyActor(actor_kind="ai_agent")

        with patch("app.api_boundary.boundary.AI_WRITE_ALLOWLIST", {"finance"}):
            result = b.command(name="finance.create", actor=actor, db=MagicMock())

        assert result == "ok"

    def test_command_success_calls_fn_with_actor_and_db(self):
        b = ERPBoundary()
        fn = MagicMock(return_value="created")
        b.register_command("finance.create", fn)
        actor = DummyActor(id=3, actor_kind="user")
        db = MagicMock()

        result = b.command(name="finance.create", actor=actor, db=db, params={"x": 1})

        assert result == "created"
        fn.assert_called_once_with(db=db, actor=actor, x=1)

    def test_command_success_records_audit_log(self):
        b = ERPBoundary()
        b.register_command("finance.create", MagicMock(return_value=None))
        actor = DummyActor(id=3, actor_kind="user")

        with patch("app.api_boundary.boundary.audit_log.record") as mock_record:
            b.command(name="finance.create", actor=actor, db=MagicMock())

        mock_record.assert_called_once()
        _, kwargs = mock_record.call_args
        assert kwargs["action"] == "command.create"

    def test_unauthenticated_actor_raises_boundary_error(self):
        b = ERPBoundary()
        b.register_command("finance.create", MagicMock())
        with pytest.raises(BoundaryError, match="Unauthenticated"):
            b.command(name="finance.create", actor=None, db=MagicMock())


class TestERPBoundaryRegistration:
    """Tests for register_query/register_command."""

    def test_register_query_overwrites_existing_entry(self):
        b = ERPBoundary()
        fn1 = MagicMock(return_value=1)
        fn2 = MagicMock(return_value=2)
        b.register_query("finance.dashboard", fn1)
        b.register_query("finance.dashboard", fn2)

        result = b.query(name="finance.dashboard", actor=DummyActor(), db=MagicMock())

        assert result == 2
        fn1.assert_not_called()

    def test_actor_kind_defaults_to_user_when_missing_attribute(self):
        b = ERPBoundary()
        assert b._actor_kind(object()) == "user"


class TestGlobalBoundarySingleton:
    """Tests for the module-level boundary singleton and its wiring."""

    def test_global_boundary_is_erp_boundary_instance(self):
        assert isinstance(global_boundary, ERPBoundary)

    def test_finance_dashboard_query_is_registered_on_import(self):
        assert "finance.dashboard" in global_boundary._queries

    def test_ai_write_allowlist_is_empty_by_default(self):
        assert AI_WRITE_ALLOWLIST == set()