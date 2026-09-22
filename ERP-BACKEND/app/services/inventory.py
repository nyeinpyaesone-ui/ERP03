"""Concurrency-safe inventory primitives.

The service owns stock mutations so POS and inventory workflows can share one
transaction boundary. Callers must commit or roll back the supplied session.
"""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.erp import StockBalance, StockMovement


class InsufficientStockError(ValueError):
    """Raised when a stock deduction would make inventory negative."""


async def adjust_stock(
    session: AsyncSession,
    *,
    warehouse_id: UUID,
    product_id: UUID,
    quantity_delta: Decimal,
    movement_type: str,
    unit_cost: Decimal = Decimal("0"),
    reference_type: str | None = None,
    reference_id: UUID | None = None,
) -> StockBalance:
    """Atomically adjust one warehouse/product balance using a row lock."""
    if quantity_delta == 0:
        raise ValueError("quantity_delta must not be zero")

    result = await session.execute(
        select(StockBalance)
        .where(
            StockBalance.warehouse_id == warehouse_id,
            StockBalance.product_id == product_id,
        )
        .with_for_update()
    )
    balance = result.scalar_one_or_none()
    if balance is None:
        if quantity_delta < 0:
            raise InsufficientStockError("No stock balance exists")
        balance = StockBalance(
            warehouse_id=warehouse_id,
            product_id=product_id,
            quantity=Decimal("0"),
            updated_at=datetime.now(timezone.utc),
        )
        session.add(balance)
        await session.flush()

    new_quantity = balance.quantity + quantity_delta
    if new_quantity < 0:
        raise InsufficientStockError("Insufficient stock")

    balance.quantity = new_quantity
    balance.updated_at = datetime.now(timezone.utc)
    session.add(
        StockMovement(
            warehouse_id=warehouse_id,
            product_id=product_id,
            movement_type=movement_type,
            quantity_delta=quantity_delta,
            unit_cost=unit_cost,
            reference_type=reference_type,
            reference_id=reference_id,
            created_at=datetime.now(timezone.utc),
        )
    )
    return balance
