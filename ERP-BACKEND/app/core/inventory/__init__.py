"""Module Inventory and Registration System.

This module provides the foundation for tracking all ERP-BACKEND modules,
their routes, dependencies, and capabilities.
"""

from .registry import ModuleRegistry, RouteInventory
from .dependency_graph import DependencyGraph

__all__ = [
    "ModuleRegistry",
    "RouteInventory",
    "DependencyGraph",
]
