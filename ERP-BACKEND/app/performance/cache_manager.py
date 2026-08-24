"""
Cache Manager Module for Redis-Based Caching
=============================================

This module provides a Redis caching layer for frequently accessed data
to reduce database load and improve response times.

Key Features:
-------------
- TTL-based cache expiration
- Automatic serialization/deserialization
- Cache invalidation utilities
- Dashboard-specific caching strategies

Usage Example:
--------------
    cache = CacheManager(redis_client)
    
    # Cache dashboard data for 5 minutes
    dashboard = cache.get_or_set(
        "dashboard:main",
        lambda: analytics_service.get_dashboard(),
        ttl=300
    )
"""

from typing import Any, Optional, Callable, Dict, List
from datetime import timedelta
import json
import logging
import hashlib

logger = logging.getLogger(__name__)


class CacheManager:
    """Redis-based cache manager for ERP performance optimization."""

    def __init__(self, redis_client=None, prefix: str = "erp_cache"):
        """
        Initialize cache manager.
        
        Parameters:
            redis_client: Redis client instance (will create default if None)
            prefix (str): Key prefix for all cache entries
        """
        self.prefix = prefix
        self.redis = redis_client
        
        if self.redis is None:
            try:
                import redis
                self.redis = redis.Redis(
                    host='localhost',
                    port=6379,
                    db=0,
                    decode_responses=True
                )
            except ImportError:
                logger.warning("Redis not installed. CacheManager will operate in no-op mode.")
                self.redis = None

    def _make_key(self, key: str) -> str:
        """Create a prefixed cache key."""
        return f"{self.prefix}:{key}"

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Parameters:
            key (str): Cache key
            
        Returns:
            Cached value or None if not found
        """
        if not self.redis:
            return None
            
        try:
            full_key = self._make_key(key)
            value = self.redis.get(full_key)
            
            if value is None:
                return None
                
            return json.loads(value)
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """
        Set value in cache with TTL.
        
        Parameters:
            key (str): Cache key
            value (Any): Value to cache (must be JSON-serializable)
            ttl (int): Time-to-live in seconds (default: 300)
            
        Returns:
            bool: True if successful
        """
        if not self.redis:
            return False
            
        try:
            full_key = self._make_key(key)
            serialized = json.dumps(value, default=str)
            self.redis.setex(full_key, ttl, serialized)
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        Delete a specific cache entry.
        
        Parameters:
            key (str): Cache key to delete
            
        Returns:
            bool: True if deleted
        """
        if not self.redis:
            return False
            
        try:
            full_key = self._make_key(key)
            self.redis.delete(full_key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False

    def delete_pattern(self, pattern: str) -> int:
        """
        Delete multiple cache entries matching a pattern.
        
        Parameters:
            pattern (str): Pattern to match (e.g., "dashboard:*")
            
        Returns:
            int: Number of keys deleted
        """
        if not self.redis:
            return 0
            
        try:
            full_pattern = self._make_key(pattern)
            keys = self.redis.keys(full_pattern)
            if keys:
                return self.redis.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache delete_pattern error for {pattern}: {e}")
            return 0

    def get_or_set(
        self,
        key: str,
        fetch_func: Callable[[], Any],
        ttl: int = 300
    ) -> Any:
        """
        Get value from cache or compute and cache it.
        
        Parameters:
            key (str): Cache key
            fetch_func (Callable): Function to call if cache miss
            ttl (int): Time-to-live in seconds
            
        Returns:
            Cached or freshly computed value
        """
        cached = self.get(key)
        if cached is not None:
            return cached
            
        value = fetch_func()
        self.set(key, value, ttl)
        return value

    def invalidate_dashboard_cache(self) -> bool:
        """
        Invalidate all dashboard-related cache entries.
        
        Call this when underlying data changes (new invoices, deals, etc.)
        
        Returns:
            bool: Success status
        """
        deleted = self.delete_pattern("dashboard:*")
        logger.info(f"Invalidated {deleted} dashboard cache entries")
        return deleted >= 0

    # ==================== DASHBOARD CACHING STRATEGIES ====================

    def get_cached_dashboard(
        self,
        analytics_service: Any,
        ttl: int = 300
    ) -> Dict[str, Any]:
        """
        Get dashboard data with caching.
        
        This is the optimized replacement for direct analytics_service.get_dashboard() calls.
        
        Parameters:
            analytics_service: Instance of AnalyticsQueryService
            ttl (int): Cache TTL in seconds (default: 300 = 5 minutes)
            
        Returns:
            Dict containing dashboard metrics
        """
        cache_key = "dashboard:main"
        
        return self.get_or_set(
            cache_key,
            lambda: analytics_service.get_dashboard(),
            ttl=ttl
        )

    def get_cached_monthly_trends(
        self,
        analytics_service: Any,
        months_back: int = 6,
        ttl: int = 600
    ) -> Dict[str, Any]:
        """
        Get monthly trends with caching.
        
        Parameters:
            analytics_service: Instance of AnalyticsQueryService
            months_back (int): Number of months to include
            ttl (int): Cache TTL in seconds (default: 600 = 10 minutes)
            
        Returns:
            Dict containing monthly trend data
        """
        cache_key = f"dashboard:trends:{months_back}"
        
        return self.get_or_set(
            cache_key,
            lambda: analytics_service.get_monthly_trends(months_back),
            ttl=ttl
        )

    def get_cached_search_results(
        self,
        search_service: Any,
        query: str,
        entity_types: Optional[List[str]] = None,
        filters: Optional[Dict] = None,
        limit: int = 20,
        offset: int = 0,
        ttl: int = 120
    ) -> tuple:
        """
        Get search results with caching.
        
        Note: Use shorter TTL for search as new content may be indexed frequently.
        
        Parameters:
            search_service: Instance of SearchService
            query (str): Search query string
            entity_types: Optional list of entity types to filter
            filters: Optional dict of metadata filters
            limit (int): Result limit
            offset (int): Result offset
            ttl (int): Cache TTL in seconds (default: 120 = 2 minutes)
            
        Returns:
            Tuple of (results, total_count)
        """
        # Create cache key from query parameters
        key_parts = [
            query.lower().strip(),
            str(entity_types) if entity_types else "all",
            str(sorted(filters.items())) if filters else "no_filters",
            str(limit),
            str(offset)
        ]
        key_hash = hashlib.md5("|".join(key_parts).encode()).hexdigest()[:12]
        cache_key = f"search:results:{key_hash}"
        
        return self.get_or_set(
            cache_key,
            lambda: search_service.search(query, entity_types, filters, limit, offset)[:2],
            ttl=ttl
        )

    def warm_up_cache(self, analytics_service: Any, search_service: Any = None) -> Dict[str, bool]:
        """
        Pre-populate cache with commonly accessed data.
        
        Call this during application startup or off-peak hours.
        
        Parameters:
            analytics_service: Instance of AnalyticsQueryService
            search_service: Optional instance of SearchService
            
        Returns:
            Dict indicating success status for each cache operation
        """
        results = {}
        
        # Warm up dashboard cache
        try:
            self.get_cached_dashboard(analytics_service, ttl=300)
            results["dashboard"] = True
        except Exception as e:
            logger.error(f"Failed to warm dashboard cache: {e}")
            results["dashboard"] = False
        
        # Warm up trends cache
        try:
            self.get_cached_monthly_trends(analytics_service, months_back=6, ttl=600)
            results["trends_6m"] = True
        except Exception as e:
            logger.error(f"Failed to warm trends cache: {e}")
            results["trends_6m"] = False
        
        # Warm up search suggestions if search service provided
        if search_service:
            try:
                common_queries = ["contact", "company", "product", "invoice"]
                for q in common_queries:
                    cache_key = f"search:suggestions:{q}"
                    self.get_or_set(
                        cache_key,
                        lambda q=q: search_service.get_suggestions(q, limit=5),
                        ttl=300
                    )
                results["suggestions"] = True
            except Exception as e:
                logger.error(f"Failed to warm search suggestions cache: {e}")
                results["suggestions"] = False
        
        return results

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dict with cache stats (memory usage, key count, etc.)
        """
        if not self.redis:
            return {"available": False, "reason": "Redis not configured"}
            
        try:
            info = self.redis.info("memory")
            keys_count = self.redis.dbsize()
            
            return {
                "available": True,
                "used_memory": info.get("used_memory_human", "unknown"),
                "used_memory_peak": info.get("used_memory_peak_human", "unknown"),
                "keys_count": keys_count,
                "prefix": self.prefix
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"available": False, "error": str(e)}
