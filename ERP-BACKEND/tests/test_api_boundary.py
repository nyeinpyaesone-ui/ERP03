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
    """Tests for the has_permission helper function."""

    def test_ai_agent_can_read(self):
        actor = DummyActor(actor_kind="ai_agent")
        assert has_permission(actor, "finance", "read", db=None) is True

    def test_ai_agent_cannot_write(self):
        actor = DummyActor(actor_kind="ai_agent")
        assert has_permission(actor, "finance", "write", db=None) is False

    def test_ai_agent_cannot_delete(self):
        actor = DummyActor(actor_kind="ai_agent")
        assert has_permission(actor, "finance", "delete", db=None) is False

    def test_regular_user_can_write(self):
        actor = DummyActor(actor_kind="user")
        assert has_permission(actor, "finance", "write", db=None) is True

    def test_actor_missing_actor_kind_attribute_treated_as_non_ai(self):
        actor = object()
        assert has_permission(actor, "finance", "write", db=None) is True


class TestERPBoundaryRegistration:
    """Tests for registering queries/commands on ERPBoundary."""

    def test_register_query_makes_it_callable_via_query(self):
        b = ERPBoundary()
        fn = MagicMock(return_value="result")
        b.register_query("finance.dashboard", fn)

        result = b.query(name="finance.dashboard", actor=DummyActor(), db=MagicMock())

        assert result == "result"

    def test_register_command_makes_it_callable_via_command(self):
        b = ERPBoundary()
        fn = MagicMock(return_value="created")
        b.register_command("finance.create", fn)

        result = b.command(name="finance.create", actor=DummyActor(), db=MagicMock())

        assert result == "created"


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

    def test_query_success_calls_registered_function_with_db_and_params(self):
        b = ERPBoundary()
        fn = MagicMock(return_value={"ok": True})
        b.register_query("finance.dashboard", fn)
        db = MagicMock()
        actor = DummyActor(id=9, actor_kind="user")

        result = b.query(name="finance.dashboard", actor=actor, db=db, params={"a": 1})

        assert result == {"ok": True}
        fn.assert_called_once_with(db=db, a=1)

    def test_query_without_params_calls_function_with_db_only(self):
        b = ERPBoundary()
        fn = MagicMock(return_value=None)
        b.register_query("finance.dashboard", fn)
        db = MagicMock()

        b.query(name="finance.dashboard", actor=DummyActor(), db=db)

        fn.assert_called_once_with(db=db)

    def test_query_success_records_audit_log_with_expected_fields(self):
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

    def test_ai_agent_can_run_query(self):
        b = ERPBoundary()
        b.register_query("finance.dashboard", MagicMock(return_value={"metric": 1}))
        actor = DummyActor(actor_kind="ai_agent")

        result = b.query(name="finance.dashboard", actor=actor, db=MagicMock())

        assert result == {"metric": 1}

    def test_query_name_without_domain_separator_raises_value_error(self):
        """Boundary case: a registered name lacking a '.' cannot be split into
        (domain, action), so the unpacking itself should raise ValueError
        rather than silently proceeding."""
        b = ERPBoundary()
        b.register_query("dashboard", MagicMock(return_value={}))

        with pytest.raises(ValueError):
            b.query(name="dashboard", actor=DummyActor(), db=MagicMock())

    def test_query_name_with_multiple_dots_splits_only_on_first_dot(self):
        """Boundary case: `name.split(".", 1)` only splits on the first dot,
        so a name like 'finance.dashboard.summary' resolves to domain
        'finance' and action 'dashboard.summary', which then flows into the
        audit log action as 'query.dashboard.summary'."""
        b = ERPBoundary()
        b.register_query("finance.dashboard.summary", MagicMock(return_value={"ok": True}))
        actor = DummyActor(id=1, actor_kind="user")

        with patch("app.api_boundary.boundary.audit_log.record") as mock_record:
            result = b.query(name="finance.dashboard.summary", actor=actor, db=MagicMock())

        assert result == {"ok": True}
        _, kwargs = mock_record.call_args
        assert kwargs["domain"] == "finance"
        assert kwargs["action"] == "query.dashboard.summary"


class TestERPBoundaryCommand:
    """Tests for ERPBoundary.command."""

    def test_unknown_command_raises_boundary_error(self):
        b = ERPBoundary()
        with pytest.raises(BoundaryError, match="Unknown command"):
            b.command(name="finance.create", actor=DummyActor(), db=MagicMock())

    def test_unauthenticated_actor_raises_boundary_error(self):
        b = ERPBoundary()
        b.register_command("finance.create", MagicMock())

        with pytest.raises(BoundaryError, match="Unauthenticated"):
            b.command(name="finance.create", actor=None, db=MagicMock())

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

    def test_command_success_calls_fn_with_db_and_actor(self):
        b = ERPBoundary()
        fn = MagicMock(return_value="created")
        b.register_command("finance.create", fn)
        actor = DummyActor(id=3, actor_kind="user")
        db = MagicMock()

        result = b.command(name="finance.create", actor=actor, db=db, params={"x": 1})

        assert result == "created"
        fn.assert_called_once_with(db=db, actor=actor, x=1)

    def test_command_success_records_audit_log_with_command_prefix(self):
        b = ERPBoundary()
        b.register_command("finance.create", MagicMock(return_value=None))
        actor = DummyActor(id=3, actor_kind="user")

        with patch("app.api_boundary.boundary.audit_log.record") as mock_record:
            b.command(name="finance.create", actor=actor, db=MagicMock())

        mock_record.assert_called_once()
        _, kwargs = mock_record.call_args
        assert kwargs["action"] == "command.create"
        assert kwargs["domain"] == "finance"

    def test_regular_user_can_write_to_any_domain(self):
        b = ERPBoundary()
        fn = MagicMock(return_value="ok")
        b.register_command("hr.terminate", fn)
        actor = DummyActor(actor_kind="user")

        result = b.command(name="hr.terminate", actor=actor, db=MagicMock())

        assert result == "ok"

    def test_command_name_without_domain_separator_raises_value_error(self):
        b = ERPBoundary()
        b.register_command("terminate", MagicMock())

        with pytest.raises(ValueError):
            b.command(name="terminate", actor=DummyActor(), db=MagicMock())

    def test_command_name_with_multiple_dots_splits_only_on_first_dot(self):
        b = ERPBoundary()
        fn = MagicMock(return_value="ok")
        b.register_command("hr.employee.terminate", fn)
        actor = DummyActor(id=2, actor_kind="user")

        with patch("app.api_boundary.boundary.audit_log.record") as mock_record:
            result = b.command(name="hr.employee.terminate", actor=actor, db=MagicMock())

        assert result == "ok"
        _, kwargs = mock_record.call_args
        assert kwargs["domain"] == "hr"
        assert kwargs["action"] == "command.employee.terminate"


class TestGlobalBoundarySingleton:
    """Tests for the module-level `boundary` singleton and its default state."""

    def test_global_boundary_is_erp_boundary_instance(self):
        assert isinstance(global_boundary, ERPBoundary)

    def test_finance_dashboard_query_is_registered_on_import(self):
        assert "finance.dashboard" in global_boundary._queries

    def test_default_ai_write_allowlist_is_empty(self):
        assert AI_WRITE_ALLOWLIST == set()