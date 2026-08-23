"""
Regression tests for the regulated-manufacturing inventory models added to
app/models.py (Location, Batch, StockLevel, StockMovement, QualityStatus).

The repository contains both a sibling module `app/models.py` and a package
`app/models/` (with its own `__init__.py`). Python's import system always
gives precedence to a package over a same-named module in the same parent
package, so `import app.models` (used everywhere else in the codebase,
including app/routers/inventory.py and app/services/inventory_service.py)
resolves to the `app/models/` package -- never to `app/models.py`. As a
result, the new regulated-manufacturing classes appended to app/models.py in
this PR are unreachable dead code.

Additionally, app/models.py itself is broken: it defines
`class QualityStatus(str, enum.Enum)` and uses `CheckConstraint` in
`StockLevel.__table_args__` without importing either `enum` or
`CheckConstraint`, so loading the file directly raises `NameError`.

These tests document both defects so they are caught by the test suite
instead of silently regressing further.
"""
import importlib.util
import os

import pytest


MODELS_PY_PATH = os.path.join(os.path.dirname(__file__), "..", "app", "models.py")


class TestAppModelsResolvesToPackage:
    """`import app.models` resolves to app/models/__init__.py, not app/models.py."""

    def test_app_models_file_is_the_package_init(self):
        import app.models as models_module

        normalized = models_module.__file__.replace(os.sep, "/")
        assert normalized.endswith("app/models/__init__.py")

    @pytest.mark.parametrize(
        "class_name", ["Location", "Batch", "StockLevel", "StockMovement", "QualityStatus"]
    )
    def test_new_regulated_inventory_classes_not_importable(self, class_name):
        import app.models as models_module

        assert not hasattr(models_module, class_name), (
            f"'{class_name}' should not be reachable via `import app.models` because "
            "the app/models/ package shadows the sibling app/models.py file"
        )

    def test_existing_models_still_importable_from_package(self):
        """Sanity check: symbols that DO exist in the package still resolve."""
        import app.models as models_module

        assert hasattr(models_module, "Product")
        assert hasattr(models_module, "InventoryMovement")
        assert hasattr(models_module, "User")


class TestModelsPyFileDirectLoad:
    """
    Loading app/models.py directly (bypassing the app/models/ package that
    normally shadows it) demonstrates that the file fails to execute.
    """

    def test_direct_load_raises_name_error_for_missing_enum_import(self):
        spec = importlib.util.spec_from_file_location(
            "app_models_standalone_under_test", MODELS_PY_PATH
        )
        module = importlib.util.module_from_spec(spec)

        with pytest.raises(NameError, match="enum"):
            spec.loader.exec_module(module)

    def test_source_references_enum_without_importing_it(self):
        """Static confirmation that `enum` is used but never imported."""
        with open(MODELS_PY_PATH, "r", encoding="utf-8") as fh:
            source = fh.read()

        assert "enum.Enum" in source
        assert "import enum" not in source

    def test_source_references_check_constraint_without_importing_it(self):
        """Static confirmation that `CheckConstraint` is used but never imported."""
        with open(MODELS_PY_PATH, "r", encoding="utf-8") as fh:
            source = fh.read()

        assert "CheckConstraint(" in source
        assert "CheckConstraint" not in source.split("class QualityStatus", 1)[0]