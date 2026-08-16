"""
Unit tests for the activity log service (app/services/activity_log.py).
"""
import pytest
from unittest.mock import MagicMock, patch

from app.services.activity_log import log_activity


class TestLogActivity:
    """Tests for log_activity function."""

    def test_log_activity_minimal_params(self, mock_db):
        """Test logging activity with minimal parameters."""
        result = log_activity(
            db=mock_db,
            action="login"
        )
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        
        # Verify the logged object has correct attributes
        call_args = mock_db.add.call_args[0][0]
        assert call_args.action == "login"
        assert call_args.user_id is None
        assert call_args.entity_type is None
        assert call_args.entity_id is None
        assert call_args.details is None
        assert call_args.ip_address is None
        assert call_args.user_agent is None

    def test_log_activity_all_params(self, mock_db):
        """Test logging activity with all parameters."""
        result = log_activity(
            db=mock_db,
            user_id=1,
            action="create",
            entity_type="contact",
            entity_id=100,
            details={"name": "John Doe"},
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0"
        )
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        
        call_args = mock_db.add.call_args[0][0]
        assert call_args.user_id == 1
        assert call_args.action == "create"
        assert call_args.entity_type == "contact"
        assert call_args.entity_id == 100
        assert call_args.details == {"name": "John Doe"}
        assert call_args.ip_address == "192.168.1.1"
        assert call_args.user_agent == "Mozilla/5.0"

    def test_log_activity_returns_log_object(self, mock_db):
        """Test that log_activity returns the created log object."""
        from app.models import ActivityLog
        
        result = log_activity(
            db=mock_db,
            action="test_action"
        )
        
        assert result is not None
        assert isinstance(result, ActivityLog) or hasattr(result, 'action')

    def test_log_activity_with_empty_details(self, mock_db):
        """Test logging activity with empty details dict."""
        result = log_activity(
            db=mock_db,
            action="view",
            details={}
        )
        
        call_args = mock_db.add.call_args[0][0]
        assert call_args.details == {}

    def test_log_activity_multiple_logs(self, mock_db):
        """Test logging multiple activities."""
        log_activity(db=mock_db, action="login")
        log_activity(db=mock_db, action="logout")
        
        assert mock_db.add.call_count == 2
        assert mock_db.commit.call_count == 2
