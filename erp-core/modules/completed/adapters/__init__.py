"""
Integration Adapters Package.

This package provides adapters for converting between internal ERP models/schemas
and the standardized integration contract schemas.
"""

from .integration import CRMAdapter, InventoryAdapter

__all__ = [
    "CRMAdapter",
    "InventoryAdapter",
]
