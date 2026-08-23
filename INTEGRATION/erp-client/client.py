"""
ERP Client Adapter for AI-BACKEND to communicate with ERP-BACKEND.

This module provides a safe, validated HTTP client for AI systems to interact
with the ERP system through versioned API contracts.

IMPORTANT: This is the ONLY way AI systems should access ERP data.
Never import ERP ORM models or connect directly to ERP database.
"""

import httpx
import logging
from typing import Optional, Dict, Any, List, TypeVar, Generic
from datetime import timedelta
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Import schemas with absolute path to avoid relative import issues
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from contracts.schemas import (
    BaseResponse,
    ErrorResponse,
    UserSchema,
    CustomerSchema,
    ProductSchema,
    HealthStatusSchema,
)

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ERPClientError(Exception):
    """Base exception for ERP client errors."""
    def __init__(self, message: str, status_code: Optional[int] = None, error_code: Optional[str] = None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.message)


class AuthenticationError(ERPClientError):
    """Authentication/authorization failed."""
    pass


class ValidationError(ERPClientError):
    """Request validation failed."""
    pass


class RateLimitError(ERPClientError):
    """Rate limit exceeded."""
    pass


class CircuitBreakerOpen(Exception):
    """Circuit breaker is open, requests are blocked."""
    pass


class CircuitBreaker:
    """
    Circuit breaker pattern implementation.
    
    Prevents cascading failures by failing fast when the ERP system is unavailable.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: timedelta = timedelta(seconds=30),
        half_open_requests: int = 1
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_requests = half_open_requests
        
        self._failures = 0
        self._last_failure_time: Optional[float] = None
        self._state = "closed"  # closed, open, half-open
        self._half_open_successes = 0
    
    def record_success(self):
        """Record a successful request."""
        self._failures = 0
        self._state = "closed"
        self._half_open_successes = 0
    
    def record_failure(self):
        """Record a failed request."""
        self._failures += 1
        self._last_failure_time = __import__('time').time()
        
        if self._failures >= self.failure_threshold:
            self._state = "open"
            logger.warning(f"Circuit breaker opened after {self._failures} failures")
    
    def can_execute(self) -> bool:
        """Check if a request can be executed."""
        if self._state == "closed":
            return True
        
        if self._state == "open":
            # Check if recovery timeout has passed
            if self._last_failure_time is None:
                return False
            
            elapsed = __import__('time').time() - self._last_failure_time
            if elapsed >= self.recovery_timeout.total_seconds():
                self._state = "half-open"
                self._half_open_successes = 0
                logger.info("Circuit breaker entering half-open state")
                return True
            return False
        
        if self._state == "half-open":
            # Allow limited requests in half-open state
            return self._half_open_successes < self.half_open_requests
        
        return False
    
    def record_half_open_success(self):
        """Record a success in half-open state."""
        self._half_open_successes += 1
        if self._half_open_successes >= self.half_open_requests:
            self._state = "closed"
            logger.info("Circuit breaker closed after successful half-open tests")


class ERPClient:
    """
    HTTP client for AI-BACKEND to communicate with ERP-BACKEND.
    
    Features:
    - Automatic retry with exponential backoff
    - Circuit breaker pattern
    - Request/response validation
    - JWT authentication
    - Correlation ID tracking
    """
    
    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        jwt_token: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        circuit_breaker: Optional[CircuitBreaker] = None
    ):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.jwt_token = jwt_token
        self.timeout = timeout
        self.max_retries = max_retries
        self.circuit_breaker = circuit_breaker or CircuitBreaker()
        
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout),
            headers=self._build_headers()
        )
        
        logger.info(f"ERPClient initialized for {self.base_url}")
    
    def _build_headers(self) -> Dict[str, str]:
        """Build default headers for all requests."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        
        if self.jwt_token:
            headers["Authorization"] = f"Bearer {self.jwt_token}"
        
        return headers
    
    def set_correlation_id(self, correlation_id: str):
        """Set correlation ID for request tracing."""
        self._client.headers["X-Correlation-ID"] = correlation_id
    
    def set_jwt_token(self, token: str):
        """Update JWT token for authentication."""
        self.jwt_token = token
        self._client.headers["Authorization"] = f"Bearer {token}"
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException))
    )
    async def _request(
        self,
        method: str,
        path: str,
        **kwargs
    ) -> httpx.Response:
        """
        Make an HTTP request with retry logic.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            path: API path (e.g., '/api/v1/customers')
            **kwargs: Additional arguments for httpx.request
            
        Returns:
            httpx.Response object
            
        Raises:
            CircuitBreakerOpen: If circuit breaker is open
            ERPClientError: If request fails
        """
        if not self.circuit_breaker.can_execute():
            raise CircuitBreakerOpen(
                "ERP service unavailable, circuit breaker is open"
            )
        
        try:
            response = await self._client.request(method, path, **kwargs)
            
            if response.status_code >= 400:
                self.circuit_breaker.record_failure()
                
                if response.status_code == 401:
                    raise AuthenticationError(
                        "Authentication failed",
                        status_code=401
                    )
                elif response.status_code == 403:
                    raise AuthenticationError(
                        "Authorization denied",
                        status_code=403
                    )
                elif response.status_code == 429:
                    raise RateLimitError(
                        "Rate limit exceeded",
                        status_code=429
                    )
                elif response.status_code >= 500:
                    raise ERPClientError(
                        f"ERP server error: {response.status_code}",
                        status_code=response.status_code
                    )
                else:
                    # Try to parse error response
                    try:
                        error_data = response.json()
                        raise ValidationError(
                            error_data.get('message', 'Validation failed'),
                            status_code=response.status_code,
                            error_code=error_data.get('error_code')
                        )
                    except Exception:
                        raise ERPClientError(
                            f"Request failed with status {response.status_code}",
                            status_code=response.status_code
                        )
            
            self.circuit_breaker.record_success()
            return response
            
        except (httpx.ConnectError, httpx.TimeoutException) as e:
            self.circuit_breaker.record_failure()
            raise ERPClientError(f"Connection error: {str(e)}") from e
    
    async def get(self, path: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make GET request."""
        response = await self._request("GET", path, params=params)
        return response.json()
    
    async def post(
        self,
        path: str,
        data: Dict[str, Any],
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make POST request."""
        response = await self._request("POST", path, params=params, json=data)
        return response.json()
    
    async def put(
        self,
        path: str,
        data: Dict[str, Any],
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make PUT request."""
        response = await self._request("PUT", path, params=params, json=data)
        return response.json()
    
    async def patch(
        self,
        path: str,
        data: Dict[str, Any],
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make PATCH request."""
        response = await self._request("PATCH", path, params=params, json=data)
        return response.json()
    
    async def delete(self, path: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make DELETE request."""
        response = await self._request("DELETE", path, params=params)
        return response.json()
    
    # ========================================================================
    # High-level ERP operations
    # ========================================================================
    
    async def health_check(self) -> HealthStatusSchema:
        """Check ERP system health."""
        data = await self.get("/health")
        return HealthStatusSchema(**data)
    
    async def get_current_user(self) -> UserSchema:
        """Get current authenticated user."""
        data = await self.get("/api/v1/auth/me")
        return UserSchema(**data)
    
    # CRM Operations
    
    async def list_customers(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None
    ) -> List[CustomerSchema]:
        """List customers with pagination."""
        params = {"page": page, "page_size": page_size}
        if search:
            params["search"] = search
        
        data = await self.get("/api/v1/crm/customers", params=params)
        return [CustomerSchema(**item) for item in data.get('items', [])]
    
    async def get_customer(self, customer_id: int) -> CustomerSchema:
        """Get a specific customer."""
        data = await self.get(f"/api/v1/crm/customers/{customer_id}")
        return CustomerSchema(**data)
    
    async def create_customer(self, customer_data: Dict[str, Any]) -> CustomerSchema:
        """Create a new customer."""
        data = await self.post("/api/v1/crm/customers", customer_data)
        return CustomerSchema(**data)
    
    async def update_customer(
        self,
        customer_id: int,
        customer_data: Dict[str, Any]
    ) -> CustomerSchema:
        """Update an existing customer."""
        data = await self.put(f"/api/v1/crm/customers/{customer_id}", customer_data)
        return CustomerSchema(**data)
    
    # Inventory Operations
    
    async def list_products(
        self,
        page: int = 1,
        page_size: int = 20,
        category_id: Optional[int] = None,
        search: Optional[str] = None
    ) -> List[ProductSchema]:
        """List products with pagination and filters."""
        params = {"page": page, "page_size": page_size}
        if category_id:
            params["category_id"] = category_id
        if search:
            params["search"] = search
        
        data = await self.get("/api/v1/inventory/products", params=params)
        return [ProductSchema(**item) for item in data.get('items', [])]
    
    async def get_product(self, product_id: int) -> ProductSchema:
        """Get a specific product."""
        data = await self.get(f"/api/v1/inventory/products/{product_id}")
        return ProductSchema(**data)
    
    async def get_product_by_sku(self, sku: str) -> ProductSchema:
        """Get a product by SKU."""
        data = await self.get(f"/api/v1/inventory/products/sku/{sku}")
        return ProductSchema(**data)
    
    async def create_product(self, product_data: Dict[str, Any]) -> ProductSchema:
        """Create a new product."""
        data = await self.post("/api/v1/inventory/products", product_data)
        return ProductSchema(**data)
    
    async def update_product(
        self,
        product_id: int,
        product_data: Dict[str, Any]
    ) -> ProductSchema:
        """Update an existing product."""
        data = await self.put(f"/api/v1/inventory/products/{product_id}", product_data)
        return ProductSchema(**data)
    
    async def adjust_stock(
        self,
        product_id: int,
        quantity: int,
        reason: str,
        location_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Adjust stock level for a product."""
        data = await self.post(
            f"/api/v1/inventory/products/{product_id}/adjust_stock",
            {
                "quantity": quantity,
                "reason": reason,
                "location_id": location_id
            }
        )
        return data
    
    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()
        logger.info("ERPClient connection closed")


# ============================================================================
# Synchronous client for non-async contexts
# ============================================================================

class ERPSyncClient:
    """Synchronous version of ERPClient for non-async contexts."""
    
    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        jwt_token: Optional[str] = None,
        timeout: float = 30.0
    ):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.jwt_token = jwt_token
        self.timeout = timeout
        
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout),
            headers=self._build_headers()
        )
        
        logger.info(f"ERPSyncClient initialized for {self.base_url}")
    
    def _build_headers(self) -> Dict[str, str]:
        """Build default headers."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        
        if self.jwt_token:
            headers["Authorization"] = f"Bearer {self.jwt_token}"
        
        return headers
    
    def get(self, path: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make GET request."""
        response = self._client.get(path, params=params)
        response.raise_for_status()
        return response.json()
    
    def post(self, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make POST request."""
        response = self._client.post(path, json=data)
        response.raise_for_status()
        return response.json()
    
    def put(self, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make PUT request."""
        response = self._client.put(path, json=data)
        response.raise_for_status()
        return response.json()
    
    def patch(self, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make PATCH request."""
        response = self._client.patch(path, json=data)
        response.raise_for_status()
        return response.json()
    
    def delete(self, path: str) -> Dict[str, Any]:
        """Make DELETE request."""
        response = self._client.delete(path)
        response.raise_for_status()
        return response.json()
    
    def close(self):
        """Close the HTTP client."""
        self._client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
