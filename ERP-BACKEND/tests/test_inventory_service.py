from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.models.erp import Base
from app.services.inventory import InsufficientStockError, adjust_stock


@pytest.mark.asyncio
async def test_adjust_stock_requires_existing_row_for_deduction():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        with pytest.raises(InsufficientStockError):
            await adjust_stock(
                session,
                warehouse_id=uuid4(),
                product_id=uuid4(),
                quantity_delta=Decimal("-1"),
                movement_type="sale",
            )

    await engine.dispose()
