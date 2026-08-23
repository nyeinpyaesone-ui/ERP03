"""
Performance Optimization Module for ERP Backend
================================================

This module provides optimized implementations of services with performance-critical operations.
Key optimizations include:
- Bulk database operations to eliminate N+1 queries
- Connection pooling configuration
- Query optimization with proper indexing hints
- Caching layer integration (Redis)
- Async I/O support for non-blocking operations

Modules:
--------
- bulk_operations: Optimized bulk insert/update/delete operations
- query_optimizer: Query optimization utilities and indexing helpers
- cache_manager: Redis-based caching for frequently accessed data
- async_utils: Async wrappers for I/O-bound operations
"""

from .bulk_operations import BulkOperationService
from .query_optimizer import QueryOptimizer
from .cache_manager import CacheManager

__all__ = [
    "BulkOperationService",
    "QueryOptimizer", 
    "CacheManager",
]
