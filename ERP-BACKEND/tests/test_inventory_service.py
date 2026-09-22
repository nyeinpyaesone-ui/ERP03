from decimal import Decimal
from uuid import uuid4
from unittest.mock import AsyncMock

import pytest

from app.services.inventory import InsufficientStockError, adjust_stock


@pytest.mark.asyncio
async def test_adjust_stock_rejects_deduction_without_balance():
    result = AsyncMock()
    result.scalar_one_or_none.return_value = None
    session = AsyncMock()
    session.execute.return_value = result

    with pytest.raises(InsufficientStockError):
        await adjust_stock(
            session,
            warehouse_id=uuid4(),
            product_id=uuid4(),
            quantity_delta=Decimal("-1"),
            movement_type="sale",
        )

    session.flush.assert_not_awaited()
