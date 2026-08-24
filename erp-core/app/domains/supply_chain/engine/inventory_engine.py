"""
ERP-CORE: Inventory & Stock Movement Engine
Implements FIFO/LIFO/Average Costing algorithms for inventory valuation.
Handles multi-warehouse stock transfers and reorder point calculations.
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from enum import Enum
from collections import deque

class InventoryError(Exception):
    pass

class CostingMethod(Enum):
    FIFO = "fifo"
    LIFO = "lifo"
    WEIGHTED_AVERAGE = "weighted_average"

class StockMovementType(Enum):
    RECEIPT = "receipt"
    SALE = "sale"
    TRANSFER_OUT = "transfer_out"
    TRANSFER_IN = "transfer_in"
    ADJUSTMENT = "adjustment"
    RETURN = "return"

class InventoryEngine:
    """
    Core algorithm for inventory management.
    Handles stock movements, costing calculations, and reorder logic.
    """
    
    def __init__(self, default_costing: CostingMethod = CostingMethod.FIFO):
        self.default_costing = default_costing
        self.precision = 2

    def calculate_fifo_cost(self, stock_layers: List[Dict], quantity_to_consume: Decimal) -> Tuple[Decimal, List[Dict]]:
        """
        Algorithm: First-In-First-Out costing.
        Consumes oldest stock layers first.
        Returns (total_cost, remaining_layers).
        """
        remaining_qty = quantity_to_consume
        total_cost = Decimal('0.00')
        remaining_layers = []
        
        # Sort by date ascending (oldest first)
        sorted_layers = sorted(stock_layers, key=lambda x: x['receipt_date'])
        
        for layer in sorted_layers:
            layer_qty = Decimal(str(layer['quantity']))
            layer_cost = Decimal(str(layer['unit_cost']))
            
            if remaining_qty <= 0:
                # Keep entire layer
                remaining_layers.append(layer)
                continue
            
            if layer_qty <= remaining_qty:
                # Consume entire layer
                total_cost += (layer_qty * layer_cost).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                remaining_qty -= layer_qty
            else:
                # Partial consumption
                consumed_cost = (remaining_qty * layer_cost).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                total_cost += consumed_cost
                
                # Update layer with remaining quantity
                new_layer = layer.copy()
                new_layer['quantity'] = float(layer_qty - remaining_qty)
                remaining_layers.append(new_layer)
                remaining_qty = Decimal('0.00')
        
        if remaining_qty > 0:
            raise InventoryError(f"Insufficient stock. Short by {remaining_qty}")
        
        return total_cost, remaining_layers

    def calculate_lifo_cost(self, stock_layers: List[Dict], quantity_to_consume: Decimal) -> Tuple[Decimal, List[Dict]]:
        """
        Algorithm: Last-In-First-Out costing.
        Consumes newest stock layers first.
        Returns (total_cost, remaining_layers).
        """
        remaining_qty = quantity_to_consume
        total_cost = Decimal('0.00')
        remaining_layers = []
        
        # Sort by date descending (newest first)
        sorted_layers = sorted(stock_layers, key=lambda x: x['receipt_date'], reverse=True)
        
        for layer in sorted_layers:
            layer_qty = Decimal(str(layer['quantity']))
            layer_cost = Decimal(str(layer['unit_cost']))
            
            if remaining_qty <= 0:
                # Keep entire layer (will be re-sorted later)
                remaining_layers.append(layer)
                continue
            
            if layer_qty <= remaining_qty:
                # Consume entire layer
                total_cost += (layer_qty * layer_cost).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                remaining_qty -= layer_qty
            else:
                # Partial consumption
                consumed_cost = (remaining_qty * layer_cost).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                total_cost += consumed_cost
                
                # Update layer with remaining quantity
                new_layer = layer.copy()
                new_layer['quantity'] = float(layer_qty - remaining_qty)
                remaining_layers.append(new_layer)
                remaining_qty = Decimal('0.00')
        
        if remaining_qty > 0:
            raise InventoryError(f"Insufficient stock. Short by {remaining_qty}")
        
        # Re-sort to original order for storage
        remaining_layers.sort(key=lambda x: x['receipt_date'])
        return total_cost, remaining_layers

    def calculate_weighted_average_cost(self, stock_layers: List[Dict]) -> Decimal:
        """
        Algorithm: Weighted Average Costing.
        Calculates average cost per unit across all layers.
        """
        if not stock_layers:
            return Decimal('0.00')
        
        total_value = Decimal('0.00')
        total_quantity = Decimal('0.00')
        
        for layer in stock_layers:
            qty = Decimal(str(layer['quantity']))
            cost = Decimal(str(layer['unit_cost']))
            total_value += (qty * cost)
            total_quantity += qty
        
        if total_quantity == 0:
            return Decimal('0.00')
        
        avg_cost = (total_value / total_quantity).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return avg_cost

    def calculate_reorder_point(
        self,
        average_daily_sales: Decimal,
        lead_time_days: int,
        safety_stock_days: int = 0
    ) -> Decimal:
        """
        Algorithm: Calculates the reorder point to trigger purchase orders.
        Reorder Point = (Average Daily Sales × Lead Time) + Safety Stock
        """
        lead_time_demand = average_daily_sales * Decimal(str(lead_time_days))
        safety_stock = average_daily_sales * Decimal(str(safety_stock_days))
        
        reorder_point = (lead_time_demand + safety_stock).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return reorder_point

    def calculate_economic_order_quantity(
        self,
        annual_demand: Decimal,
        ordering_cost: Decimal,
        holding_cost_per_unit: Decimal
    ) -> Decimal:
        """
        Algorithm: Economic Order Quantity (EOQ).
        Minimizes total inventory costs (ordering + holding).
        EOQ = sqrt((2 × Annual Demand × Ordering Cost) / Holding Cost)
        """
        if holding_cost_per_unit <= 0:
            raise InventoryError("Holding cost must be positive.")
        if annual_demand <= 0 or ordering_cost <= 0:
            raise InventoryError("Demand and ordering cost must be positive.")
        
        from math import sqrt
        eoq = sqrt((2 * float(annual_demand) * float(ordering_cost)) / float(holding_cost_per_unit))
        return Decimal(str(eoq)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def process_stock_movement(
        self,
        current_stock: Decimal,
        movement_type: StockMovementType,
        quantity: Decimal,
        source_warehouse: str = None,
        dest_warehouse: str = None
    ) -> Decimal:
        """
        Algorithm: Processes a stock movement and returns new stock level.
        Validates constraints based on movement type.
        """
        if quantity < 0:
            raise InventoryError("Quantity cannot be negative.")
        
        if movement_type in [StockMovementType.SALE, StockMovementType.TRANSFER_OUT, StockMovementType.ADJUSTMENT]:
            if quantity > current_stock:
                raise InventoryError(f"Insufficient stock. Current: {current_stock}, Requested: {quantity}")
            new_stock = current_stock - quantity
        elif movement_type in [StockMovementType.RECEIPT, StockMovementType.TRANSFER_IN, StockMovementType.RETURN]:
            new_stock = current_stock + quantity
        else:
            raise InventoryError(f"Unknown movement type: {movement_type}")
        
        return new_stock.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def allocate_inventory(
        self,
        available_stock: Decimal,
        pending_orders: List[Dict]
    ) -> List[Dict]:
        """
        Algorithm: Allocates available stock to pending orders by priority/date.
        Returns allocation status for each order.
        """
        # Sort by priority then date
        sorted_orders = sorted(pending_orders, key=lambda x: (x.get('priority', 99), x['order_date']))
        
        remaining_stock = available_stock
        allocations = []
        
        for order in sorted_orders:
            requested_qty = Decimal(str(order['quantity']))
            
            if remaining_stock >= requested_qty:
                allocated_qty = requested_qty
                remaining_stock -= requested_qty
                status = "fully_allocated"
            elif remaining_stock > 0:
                allocated_qty = remaining_stock
                remaining_stock = Decimal('0.00')
                status = "partially_allocated"
            else:
                allocated_qty = Decimal('0.00')
                status = "unallocated"
            
            allocations.append({
                "order_id": order['id'],
                "requested": requested_qty,
                "allocated": allocated_qty,
                "status": status
            })
        
        return allocations
