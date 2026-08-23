"""
Unit tests for the authentication router (app/routers/auth.py), focused on the
login() endpoint, which was updated in this PR to record `last_login` using a
timezone-aware UTC timestamp (datetime.now(timezone.utc)) instead of the
deprecated datetime.utcnow().
"""
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from app.routers.auth import login
from app.models import User


def _make_form_data(username: str, password: str) -> OAuth2PasswordRequestForm:
    """Build an OAuth2PasswordRequestForm-like object for direct function calls."""
    form = MagicMock(spec=OAuth2PasswordRequestForm)
    form.username = username
    form.password = password
    return form


@pytest.fixture
def mock_db():
    db = MagicMock()
    return db


class TestLogin:
    """Tests for the login() endpoint function."""

    def test_login_success_issues_token(self, mock_db, sample_user, mock_pwd_context):
        """Successful login returns an access token, bearer type, and the user."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_user
        mock_pwd_context.verify.return_value = True

        with patch('app.routers.auth.create_access_token', return_value="signed.jwt.token") as mock_create_token, \
             patch('app.routers.auth.log_activity') as mock_log:
            form_data = _make_form_data("test@example.com", "CorrectPassword1!")
            result = login(form_data=form_data, db=mock_db)

        assert result["access_token"] == "signed.jwt.token"
        assert result["token_type"] == "bearer"
        assert result["user"] == sample_user
        mock_create_token.assert_called_once_with({"sub": str(sample_user.id), "role": sample_user.role})
        mock_log.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_login_updates_last_login_with_timezone_aware_utc_datetime(
        self, mock_db, sample_user, mock_pwd_context
    ):
        """
        Regression test: login() must set `last_login` to a timezone-aware UTC
        datetime (datetime.now(timezone.utc)). This guards against reintroducing
        a NameError from referencing `timezone` without importing it, and against
        regressing to a naive datetime.utcnow() timestamp.
        """
        mock_db.query.return_value.filter.return_value.first.return_value = sample_user
        mock_pwd_context.verify.return_value = True

        before = datetime.now(timezone.utc)
        with patch('app.routers.auth.create_access_token', return_value="token"), \
             patch('app.routers.auth.log_activity'):
            form_data = _make_form_data("test@example.com", "CorrectPassword1!")
            login(form_data=form_data, db=mock_db)
        after = datetime.now(timezone.utc)

        assert sample_user.last_login is not None
        assert sample_user.last_login.tzinfo is not None
        assert sample_user.last_login.tzinfo == timezone.utc
        assert before <= sample_user.last_login <= after

    def test_login_invalid_password_raises_401(self, mock_db, sample_user, mock_pwd_context):
        """Wrong password results in a generic 401 error (no user enumeration)."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_user
        mock_pwd_context.verify.return_value = False

        form_data = _make_form_data("test@example.com", "WrongPassword1!")

        with pytest.raises(HTTPException) as exc_info:
            login(form_data=form_data, db=mock_db)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid credentials"
        mock_db.commit.assert_not_called()

    def test_login_unknown_user_raises_401_and_still_verifies(self, mock_db, mock_pwd_context):
        """
        Unknown user still triggers a dummy password verification (constant-time
        comparison to prevent user enumeration via timing) and raises 401.
        """
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_pwd_context.verify.return_value = False

        form_data = _make_form_data("nobody@example.com", "SomePassword1!")

        with pytest.raises(HTTPException) as exc_info:
            login(form_data=form_data, db=mock_db)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid credentials"
        # Dummy verification must still occur to keep timing constant.
        mock_pwd_context.verify.assert_called()

    def test_login_does_not_commit_or_log_on_failure(self, mock_db, sample_user, mock_pwd_context):
        """On failed login, no commit or activity log should occur."""
        mock_db.query.return_value.filter.return_value.first.return_value = sample_user
        mock_pwd_context.verify.return_value = False

        with patch('app.routers.auth.log_activity') as mock_log:
            form_data = _make_form_data("test@example.com", "WrongPassword1!")
            with pytest.raises(HTTPException):
                login(form_data=form_data, db=mock_db)

            mock_log.assert_not_called()
        mock_db.commit.assert_not_called()