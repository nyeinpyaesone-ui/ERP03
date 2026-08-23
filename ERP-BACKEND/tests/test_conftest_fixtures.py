"""
Tests for fixtures defined in tests/conftest.py that were introduced or
modified in this PR: `setup_jsonb_mock` and the `engine` fixture's new
`echo=False` argument.
"""
import pytest
from sqlalchemy.pool import StaticPool


class TestSetupJsonbMockFixture:
    """
    Regression tests documenting a defect in the `setup_jsonb_mock` autouse
    fixture (tests/conftest.py).

    The fixture does:

        import app.models
        with patch.object(app.models, 'JSONB', MockJSONB):
            yield

    However `app.models` resolves to the `app/models/` package (which
    shadows the sibling `app/models.py` file per Python's import precedence
    rules), and that package's `__init__.py` never defines or re-exports a
    `JSONB` attribute -- only individual submodules like
    `app/models/workflow.py` define their own local `JSONB` alias.
    `unittest.mock.patch.object` requires the target attribute to already
    exist unless `create=True` is passed, so this fixture raises
    `AttributeError` whenever it runs.
    """

    def test_app_models_package_has_no_jsonb_attribute(self):
        import app.models

        assert not hasattr(app.models, "JSONB")

    def test_patching_jsonb_on_app_models_raises_attribute_error(self):
        import sqlalchemy.types as types
        from unittest.mock import patch
        import app.models

        class MockJSONB(types.TypeDecorator):
            impl = types.JSON
            cache_ok = True

        with pytest.raises(AttributeError, match="JSONB"):
            with patch.object(app.models, "JSONB", MockJSONB):
                pass

    def test_patching_with_create_true_would_succeed(self):
        """
        Confirms the fix: passing create=True lets patch.object add the
        attribute instead of requiring it to pre-exist.
        """
        import sqlalchemy.types as types
        from unittest.mock import patch
        import app.models

        class MockJSONB(types.TypeDecorator):
            impl = types.JSON
            cache_ok = True

        with patch.object(app.models, "JSONB", MockJSONB, create=True):
            assert app.models.JSONB is MockJSONB
        assert not hasattr(app.models, "JSONB")


class TestEngineFixture:
    """Tests for the `engine` fixture's echo=False configuration."""

    def test_engine_uses_static_pool(self, engine):
        assert engine.pool.__class__ is StaticPool

    def test_engine_echo_is_disabled(self, engine):
        assert engine.echo is False

    def test_engine_is_in_memory_sqlite(self, engine):
        assert engine.url.get_backend_name() == "sqlite"
        assert engine.url.database == ":memory:"

    def test_engine_connections_work(self, engine):
        with engine.connect() as conn:
            from sqlalchemy import text
            result = conn.execute(text("SELECT 1")).scalar()
        assert result == 1