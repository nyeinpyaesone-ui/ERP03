from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.services.sales import SaleLine, SalePayment, SaleValidationError, create_pos_sale


@pytest.mark.asyncio
async def test_pos_sale_rejects_overpayment_before_transaction():
    session = AsyncMock()
    with pytest.raises(SaleValidationError, match="Overpayment"):
        await create_pos_sale(
            session,
            business_id=uuid4(),
            branch_id=uuid4(),
            warehouse_id=uuid4(),
            invoice_no="INV-0001",
            lines=[SaleLine(product_id=uuid4(), quantity=Decimal("1"), unit_price=Decimal("100"))],
            payments=[SalePayment(method="cash", amount=Decimal("101"))],
        )
    session.begin.assert_not_called()
