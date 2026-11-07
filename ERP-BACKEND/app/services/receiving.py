"""Purchase receiving service: stock-in with weighted-average costing.

Receiving increases a warehouse balance and rolls the product's standard
cost forward using the weighted-average method, so sale-side margin
reporting stays consistent with what was actually paid to suppliers.
"""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import SaleValidationError
from app.models.erp import Product, Warehouse
from app.services.inventory import adjust_stock


async def receive_purchase_lines(
    session: AsyncSession,
    *,
    business_id: UUID,
    branch_id: UUID,
    warehouse_id: UUID,
    lines: list[tuple[UUID, Decimal, Decimal]],
) -> Decimal:
    """Receive ``lines`` of (product_id, quantity, unit_cost) into a warehouse.

    Returns the total purchase value. Every product must belong to the
    caller's tenant/branch and every line must have positive quantity and
    non-negative cost. The helper flushes but never commits: the caller owns
    the transaction boundary so a receipt is all-or-nothing.
    """
    if not lines:
        raise SaleValidationError("A receipt must contain at least one line")
    if any(qty <= 0 for _, qty, _ in lines):
        raise SaleValidationError("Receipt quantities must be positive")
    if any(cost < 0 for _, _, cost in lines):
        raise SaleValidationError("Receipt unit costs cannot be negative")

    product_ids = sorted({pid for pid, _, _ in lines}, key=str)
    result = await session.execute(
        select(Product)
        .where(
            Product.id.in_(product_ids),
            Product.business_id == business_id,
            Product.branch_id == branch_id,
            Product.active.is_(True),
        )
        .with_for_update()
    )
    products = {p.id: p for p in result.scalars().all()}
    if len(products) != len(product_ids):
        raise SaleValidationError("One or more products are invalid for this branch")

    warehouse = await session.scalar(
        select(Warehouse).where(
            Warehouse.id == warehouse_id,
            Warehouse.branch_id == branch_id,
            Warehouse.active.is_(True),
        )
    )
    if warehouse is None:
        raise SaleValidationError("Warehouse is not valid for this branch")

    total_value = Decimal("0")
    for product_id, quantity, unit_cost in sorted(lines, key=lambda item: str(item[0])):
        product = products[product_id]
        balance = await adjust_stock(
            session,
            warehouse_id=warehouse_id,
            product_id=product_id,
            quantity_delta=quantity,
            movement_type="purchase",
            unit_cost=unit_cost,
            reference_type="receipt",
            reference_id=None,
        )
        # Weighted-average roll-forward on the pre-receipt quantity.
        prior_qty = balance.quantity - quantity
        new_cost = (prior_qty * product.cost_price + quantity * unit_cost) / (prior_qty + quantity)
        product.cost_price = new_cost.quantize(Decimal("0.01"))
        total_value += quantity * unit_cost
    return total_value
