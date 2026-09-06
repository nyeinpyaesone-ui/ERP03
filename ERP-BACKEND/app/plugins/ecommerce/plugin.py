"""
E-commerce Plugin Example

Demonstrates plugin architecture for e-commerce functionality.
This is a sample plugin that can be enabled/disabled via configuration.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import logging

from app.plugins import PluginBase, PluginMetadata


# ==================== Schemas ====================

class ProductListing(BaseModel):
    """E-commerce product listing schema."""
    id: int
    name: str
    description: Optional[str] = None
    price: float
    stock: int
    category: str
    images: List[str] = []
    created_at: datetime


class OrderCreate(BaseModel):
    """Order creation schema."""
    customer_id: int
    items: List[dict] = Field(..., description="List of {product_id, quantity}")
    shipping_address: dict
    payment_method: str


class OrderResponse(BaseModel):
    """Order response schema."""
    id: int
    order_number: str
    customer_id: int
    status: str
    total: float
    created_at: datetime


# ==================== Plugin Implementation ====================

class EcommercePlugin(PluginBase):
    """E-commerce domain plugin."""
    
    metadata = PluginMetadata(
        name="ecommerce",
        version="1.0.0",
        description="E-commerce functionality plugin",
        domain="ecommerce",
        author="ERP03",
        dependencies=["inventory", "payments"],
        router_prefix="/api/v1/ecommerce",
        auto_register=True
    )
    
    def __init__(self, app, config=None):
        super().__init__(app, config)
        self.logger = logging.getLogger("erp03.plugins.ecommerce")
    
    def on_load(self) -> bool:
        """Validate required dependencies before loading."""
        # Check if required core modules are available
        required_deps = ["inventory", "payments"]
        for dep in required_deps:
            if not hasattr(self.app.state, 'core_modules'):
                self.logger.warning(f"Dependency {dep} not found, ecommerce plugin may have limited functionality")
        return True
    
    def on_register(self) -> None:
        """Register plugin routes."""
        pass
    
    def on_startup(self) -> None:
        """Initialize plugin on application startup."""
        self.initialized = True
        self.logger.info("E-commerce plugin initialized")
    
    def on_shutdown(self) -> None:
        """Cleanup on application shutdown."""
        self.logger.info("E-commerce plugin shutting down")
        self.initialized = False
    
    def get_router(self) -> APIRouter:
        """Return the API router for this plugin."""
        router = APIRouter()
        
        @router.get("/products", response_model=List[ProductListing])
        async def list_products(
            skip: int = 0,
            limit: int = 20,
            category: Optional[str] = None
        ):
            """List e-commerce products."""
            # Placeholder - would integrate with inventory module
            return []
        
        @router.post("/orders", response_model=OrderResponse, status_code=201)
        async def create_order(order: OrderCreate):
            """Create a new order."""
            # Placeholder - would integrate with inventory and payments
            return OrderResponse(
                id=1,
                order_number=f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                customer_id=order.customer_id,
                status="pending",
                total=0.0,
                created_at=datetime.now(timezone.utc)
            )
        
        @router.get("/orders/{order_id}", response_model=OrderResponse)
        async def get_order(order_id: int):
            """Get order details."""
            raise HTTPException(status_code=404, detail="Order not found")
        
        @router.get("/stats")
        async def get_ecommerce_stats():
            """Get e-commerce statistics."""
            return {
                "total_products": 0,
                "total_orders": 0,
                "revenue_today": 0.0
            }
        
        return router


# Expose the plugin class
Plugin = EcommercePlugin
