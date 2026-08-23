"""
Unit tests for the inventory package's public API
(app/core/inventory/__init__.py).
"""
import app.core.inventory as inventory_pkg
from app.core.inventory import DependencyGraph, ModuleRegistry, RouteInventory
from app.core.inventory.dependency_graph import DependencyGraph as GraphDependencyGraph
from app.core.inventory.registry import ModuleRegistry as RegistryModuleRegistry
from app.core.inventory.registry import RouteInventory as RegistryRouteInventory


class TestInventoryPackageExports:
    """Tests for the re-exported names and __all__ declared in __init__.py."""

    def test_all_declares_expected_public_names(self):
        assert inventory_pkg.__all__ == ["ModuleRegistry", "RouteInventory", "DependencyGraph"]

    def test_module_registry_is_reexported_from_registry_module(self):
        assert ModuleRegistry is RegistryModuleRegistry

    def test_route_inventory_is_reexported_from_registry_module(self):
        assert RouteInventory is RegistryRouteInventory

    def test_dependency_graph_is_reexported_from_dependency_graph_module(self):
        assert DependencyGraph is GraphDependencyGraph

    def test_every_name_in_all_is_accessible_as_a_package_attribute(self):
        for name in inventory_pkg.__all__:
            assert hasattr(inventory_pkg, name), f"{name} should be importable from app.core.inventory"

    def test_package_does_not_export_undocumented_extra_names_via_all(self):
        """Regression: guards against __all__ silently growing to include
        internal helpers that shouldn't be part of the public API."""
        assert set(inventory_pkg.__all__) == {"ModuleRegistry", "RouteInventory", "DependencyGraph"}