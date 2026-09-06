"""
Unit tests for the database configuration module (app/database.py).
"""
import pytest
from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session

from app.database import _create_database_engine, get_db, engine, SessionLocal, Base


class TestCreateDatabaseEngine:
    """Tests for _create_database_engine function."""

    @patch('app.database.create_engine')
    def test_sqlite_url_uses_check_same_thread_config(self, mock_create_engine):
        """SQLite URLs should be configured with connect_args and no pool sizing."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        result = _create_database_engine("sqlite:///:memory:")

        mock_create_engine.assert_called_once_with(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            pool_pre_ping=True,
        )
        assert result is mock_engine

    @patch('app.database.create_engine')
    def test_sqlite_file_url_detected(self, mock_create_engine):
        """Any URL starting with 'sqlite' should use the SQLite branch."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        _create_database_engine("sqlite:////tmp/test.db")

        _, kwargs = mock_create_engine.call_args
        assert kwargs == {"connect_args": {"check_same_thread": False}, "pool_pre_ping": True}

    @patch('app.database.create_engine')
    def test_postgres_url_uses_connection_pooling(self, mock_create_engine):
        """Non-SQLite URLs should be configured with pool_size/max_overflow."""
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine

        result = _create_database_engine("postgresql://user:pass@localhost:5432/erp_db")

        mock_create_engine.assert_called_once_with(
            "postgresql://user:pass@localhost:5432/erp_db",
            pool_size=20,
            max_overflow=30,
            pool_pre_ping=True,
        )
        assert result is mock_engine

    @patch('app.database.create_engine')
    def test_postgres_url_does_not_set_connect_args(self, mock_create_engine):
        """Non-SQLite URLs must not receive the SQLite-only connect_args kwarg."""
        _create_database_engine("postgresql://user:pass@localhost/db")

        _, kwargs = mock_create_engine.call_args
        assert "connect_args" not in kwargs

    def test_sqlite_engine_is_actually_usable(self):
        """Integration-style check that a real SQLite engine can be created and connected to."""
        test_engine = _create_database_engine("sqlite:///:memory:")
        try:
            assert test_engine.url.drivername == "sqlite"
            connection = test_engine.connect()
            connection.close()
        finally:
            test_engine.dispose()


class TestModuleLevelObjects:
    """Tests for module-level database objects."""

    def test_engine_is_created(self):
        """The module-level engine should be a valid SQLAlchemy engine."""
        assert engine is not None
        assert hasattr(engine, "connect")

    def test_session_local_bound_to_engine(self):
        """SessionLocal should produce sessions bound to the module engine."""
        session = SessionLocal()
        try:
            assert session.bind is engine
        finally:
            session.close()

    def test_base_has_metadata(self):
        """Base should be a declarative base exposing metadata for model registration."""
        assert hasattr(Base, "metadata")


class TestGetDb:
    """Tests for the get_db dependency generator."""

    @patch('app.database.SessionLocal')
    def test_get_db_yields_session(self, mock_session_local):
        """get_db should yield the session created by SessionLocal."""
        mock_session = MagicMock(spec=Session)
        mock_session_local.return_value = mock_session

        gen = get_db()
        db = next(gen)

        assert db is mock_session
        mock_session.close.assert_not_called()

        # Drain the generator so the finally block executes.
        with pytest.raises(StopIteration):
            next(gen)

    @patch('app.database.SessionLocal')
    def test_get_db_closes_session_after_normal_use(self, mock_session_local):
        """The session should be closed once the generator is exhausted."""
        mock_session = MagicMock(spec=Session)
        mock_session_local.return_value = mock_session

        gen = get_db()
        next(gen)
        with pytest.raises(StopIteration):
            next(gen)

        mock_session.close.assert_called_once()

    @patch('app.database.SessionLocal')
    def test_get_db_closes_session_on_exception(self, mock_session_local):
        """The session should still be closed if an exception propagates through the generator."""
        mock_session = MagicMock(spec=Session)
        mock_session_local.return_value = mock_session

        gen = get_db()
        next(gen)

        with pytest.raises(ValueError):
            gen.throw(ValueError("boom"))

        mock_session.close.assert_called_once()

    def test_get_db_real_session_is_functional(self):
        """End-to-end check using a real in-memory session."""
        gen = get_db()
        db = next(gen)
        try:
            assert isinstance(db, Session)
        finally:
            gen.close()