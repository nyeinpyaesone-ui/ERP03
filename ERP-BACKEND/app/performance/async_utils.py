"""
Async I/O Utilities for Non-Blocking Operations
================================================

This module provides async wrappers and utilities for I/O-bound operations
to prevent blocking the event loop during database queries, HTTP requests,
and file operations.

Key Features:
-------------
- Async database query execution
- Async HTTP client with connection pooling
- File I/O operations using thread pool
- Batch processing with concurrency control

Usage Example:
--------------
    async_utils = AsyncUtils()
    
    # Execute database queries asynchronously
    results = await async_utils.run_db_query_async(
        lambda: db.query(Contact).filter(Contact.status == "active").all()
    )
    
    # Make concurrent HTTP requests
    responses = await async_utils.gather_http_requests(urls)
"""

from typing import Any, Callable, List, Dict, Optional, TypeVar, Awaitable
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import wraps
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

T = TypeVar('T')


class AsyncUtils:
    """Utility class for async I/O operations."""

    def __init__(self, max_workers: int = 10):
        """
        Initialize async utilities.
        
        Parameters:
            max_workers (int): Maximum number of worker threads for I/O operations
        """
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    async def run_in_executor(self, func: Callable[[], T], *args) -> T:
        """
        Run a synchronous function in a thread pool executor.
        
        Parameters:
            func (Callable): Synchronous function to run
            *args: Arguments to pass to the function
            
        Returns:
            Result from the function
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, lambda: func(*args))

    async def run_db_query_async(self, query_func: Callable[[], T]) -> T:
        """
        Execute a database query asynchronously.
        
        Parameters:
            query_func (Callable): Function that executes the database query
            
        Returns:
            Query results
        """
        start_time = datetime.now()
        try:
            result = await self.run_in_executor(query_func)
            elapsed = (datetime.now() - start_time).total_seconds() * 1000
            logger.debug(f"Async DB query completed in {elapsed:.2f}ms")
            return result
        except Exception as e:
            logger.error(f"Async DB query failed: {e}")
            raise

    async def gather_db_queries_async(
        self,
        query_funcs: List[Callable[[], T]]
    ) -> List[T]:
        """
        Execute multiple database queries concurrently.
        
        This is useful for analytics dashboards that need data from multiple tables.
        
        Parameters:
            query_funcs (List[Callable]): List of query functions to execute
            
        Returns:
            List of query results in the same order as input
        """
        tasks = [self.run_db_query_async(func) for func in query_funcs]
        return await asyncio.gather(*tasks)

    async def fetch_url_async(
        self,
        url: str,
        method: str = "GET",
        headers: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Fetch a URL asynchronously using httpx.
        
        Parameters:
            url (str): URL to fetch
            method (str): HTTP method (default: GET)
            headers (Optional[Dict]): HTTP headers
            json_data (Optional[Dict]): JSON body for POST/PUT requests
            timeout (int): Request timeout in seconds
            
        Returns:
            Dict with status_code, headers, and json/text content
        """
        try:
            import httpx
            
            async with httpx.AsyncClient(timeout=timeout) as client:
                if method.upper() == "GET":
                    response = await client.get(url, headers=headers)
                elif method.upper() == "POST":
                    response = await client.post(url, headers=headers, json=json_data)
                elif method.upper() == "PUT":
                    response = await client.put(url, headers=headers, json=json_data)
                elif method.upper() == "DELETE":
                    response = await client.delete(url, headers=headers)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                return {
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "json": response.json() if response.headers.get("content-type", "").startswith("application/json") else None,
                    "text": response.text if not response.headers.get("content-type", "").startswith("application/json") else None
                }
        except ImportError:
            logger.error("httpx not installed. Install with: pip install httpx")
            raise
        except Exception as e:
            logger.error(f"Async HTTP request to {url} failed: {e}")
            raise

    async def gather_http_requests(
        self,
        urls: List[str],
        method: str = "GET",
        headers: Optional[Dict] = None,
        concurrency_limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Fetch multiple URLs concurrently with controlled concurrency.
        
        Parameters:
            urls (List[str]): List of URLs to fetch
            method (str): HTTP method (default: GET)
            headers (Optional[Dict]): HTTP headers
            concurrency_limit (int): Maximum concurrent requests
            
        Returns:
            List of response dicts in the same order as input URLs
        """
        semaphore = asyncio.Semaphore(concurrency_limit)
        
        async def fetch_with_semaphore(url: str) -> Dict[str, Any]:
            async with semaphore:
                return await self.fetch_url_async(url, method, headers)
        
        tasks = [fetch_with_semaphore(url) for url in urls]
        return await asyncio.gather(*tasks, return_exceptions=True)

    async def process_batch_async(
        self,
        items: List[Any],
        processor: Callable[[Any], T],
        batch_size: int = 100,
        concurrency: int = 10
    ) -> List[T]:
        """
        Process a batch of items asynchronously with controlled concurrency.
        
        Parameters:
            items (List[Any]): Items to process
            processor (Callable): Function to process each item
            batch_size (int): Number of items per batch
            concurrency (int): Maximum concurrent processors
            
        Returns:
            List of processed results
        """
        semaphore = asyncio.Semaphore(concurrency)
        results = []
        
        async def process_with_semaphore(item: Any) -> T:
            async with semaphore:
                return await self.run_in_executor(processor, item)
        
        # Process in batches to manage memory
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            tasks = [process_with_semaphore(item) for item in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions and log them
            for j, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    logger.error(f"Error processing item {i+j}: {result}")
                else:
                    results.append(result)
        
        return results

    def async_wrap(self, func: Callable[[], T]) -> Callable[[], Awaitable[T]]:
        """
        Decorator to wrap a synchronous function as async.
        
        Usage:
            @async_utils.async_wrap
            def slow_function():
                time.sleep(1)
                return "done"
            
            result = await slow_function()
        """
        @wraps(func)
        async def wrapper() -> T:
            return await self.run_in_executor(func)
        return wrapper

    def shutdown(self):
        """Shutdown the thread pool executor."""
        self.executor.shutdown(wait=True)


# ==================== ASYNC SERVICE WRAPPERS ====================

class AsyncSearchServiceWrapper:
    """Async wrapper for SearchService to enable non-blocking search operations."""

    def __init__(self, search_service: Any, async_utils: Optional[AsyncUtils] = None):
        """
        Initialize async search wrapper.
        
        Parameters:
            search_service: Instance of SearchService to wrap
            async_utils: AsyncUtils instance (creates default if None)
        """
        self.search_service = search_service
        self.async_utils = async_utils or AsyncUtils()

    async def search_async(
        self,
        query: str,
        entity_types: Optional[List[str]] = None,
        filters: Optional[Dict] = None,
        limit: int = 20,
        offset: int = 0
    ) -> tuple:
        """Execute search asynchronously."""
        return await self.async_utils.run_db_query_async(
            lambda: self.search_service.search(query, entity_types, filters, limit, offset)
        )

    async def reindex_all_async(self) -> Dict[str, int]:
        """Execute full reindex asynchronously."""
        return await self.async_utils.run_db_query_async(
            lambda: self.search_service.reindex_all()
        )

    async def get_suggestions_async(self, query: str, limit: int = 10) -> List[Dict]:
        """Get suggestions asynchronously."""
        return await self.async_utils.run_db_query_async(
            lambda: self.search_service.get_suggestions(query, limit)
        )


class AsyncAnalyticsServiceWrapper:
    """Async wrapper for AnalyticsQueryService to enable non-blocking analytics."""

    def __init__(self, analytics_service: Any, async_utils: Optional[AsyncUtils] = None):
        """
        Initialize async analytics wrapper.
        
        Parameters:
            analytics_service: Instance of AnalyticsQueryService to wrap
            async_utils: AsyncUtils instance (creates default if None)
        """
        self.analytics_service = analytics_service
        self.async_utils = async_utils or AsyncUtils()

    async def get_dashboard_async(self) -> Dict:
        """Get dashboard data asynchronously."""
        return await self.async_utils.run_db_query_async(
            lambda: self.analytics_service.get_dashboard()
        )

    async def get_monthly_trends_async(self, months_back: int = 6) -> Dict:
        """Get monthly trends asynchronously."""
        return await self.async_utils.run_db_query_async(
            lambda: self.analytics_service.get_monthly_trends(months_back)
        )

    async def get_full_analytics_async(self, months_back: int = 6) -> Dict:
        """
        Get all analytics data concurrently.
        
        This executes dashboard and trends queries in parallel.
        """
        results = await self.async_utils.gather_db_queries_async([
            lambda: self.analytics_service.get_dashboard(),
            lambda: self.analytics_service.get_monthly_trends(months_back)
        ])
        
        return {
            "dashboard": results[0],
            "trends": results[1]
        }
