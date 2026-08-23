"""
Unit tests for the inventory package exports (app/core/inventory/__init__.py).
"""
import app.core.inventory as inventory_pkg
from app.core.inventory import ModuleRegistry, RouteInventory, DependencyGraph
from app.core.inventory.registry import ModuleRegistry as RegistryModuleRegistry
from app.core.inventory.registry import RouteInventory as RegistryRouteInventory
from app.core.inventory.dependency_graph import DependencyGraph as GraphDependencyGraph


class TestInventoryPackageExports:
    """Tests for the public re-exports of the `app.core.inventory` package."""

    def test_all_contains_expected_names(self):
        assert inventory_pkg.__all__ == ["ModuleRegistry", "RouteInventory", "DependencyGraph"]

    def test_module_registry_is_reexported_from_registry_module(self):
        assert ModuleRegistry is RegistryModuleRegistry

    def test_route_inventory_is_reexported_from_registry_module(self):
        assert RouteInventory is RegistryRouteInventory

    def test_dependency_graph_is_reexported_from_dependency_graph_module(self):
        assert DependencyGraph is GraphDependencyGraph

    def test_exported_classes_are_usable_directly_from_package(self):
        registry = ModuleRegistry()
        registry.register_module("finance", "Financial transactions")

        assert registry.modules == {"finance": "Financial transactions"}
        assert isinstance(DependencyGraph(), DependencyGraph)