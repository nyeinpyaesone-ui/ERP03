"""Service-level coverage for the catalog and purchasing domain logic."""

from decimal import Decimal
from uuid import uuid4

import pytest
from app.core.errors import ConflictError, ForbiddenError, NotFoundError, SaleValidationError
from app.db.session import SessionFactory
from app.models.erp import StockBalance
from app.services.bootstrap import bootstrap_business
from app.services.catalog import (
    create_customer,
    create_product,
    create_supplier,
    list_products,
    set_product_active,
)
from app.services.receiving import receive_purchase_lines

pytestmark = pytest.mark.integration


async def _bootstrap(prefix: str):
    async with SessionFactory() as session, session.begin():
        return await bootstrap_business(
            session,
            business_name=f"{prefix} Business",
            business_code=f"{prefix}-{uuid4().hex[:8]}",
            branch_name="Main Branch",
            branch_code="MAIN",
            owner_email=f"owner-{uuid4().hex[:8]}@example.com",
            owner_password="Correct-Horse-123",
            owner_name="Owner",
        )


@pytest.mark.asyncio
async def test_create_and_list_products_with_search_and_pagination():
    business, branch, _warehouse, _user = await _bootstrap("CAT")
    for index in range(3):
        async with SessionFactory() as session:
            await create_product(
                session,
                business_id=business.id,
                branch_id=branch.id,
                sku=f"SKU-{index}-{uuid4().hex[:6]}",
                name=f"WIDGET item {index}",
                sale_price=Decimal("10.00"),
            )
    async with SessionFactory() as session, session.begin():
        page = await list_products(
            session, business_id=business.id, search="widget", limit=2, offset=0
        )
        assert page.total == 3
        assert len(page.items) == 2
        assert page.has_more is True
        other_tenant = await list_products(session, business_id=uuid4())
        assert other_tenant.total == 0  # tenant isolation on reads


@pytest.mark.asyncio
async def test_duplicate_sku_conflicts_and_deactivation_is_404_scoped():
    business, branch, _warehouse, _user = await _bootstrap("CAT")
    sku = f"SKU-dup-{uuid4().hex[:6]}"
    async with SessionFactory() as session, session.begin():
        product = await create_product(
            session,
            business_id=business.id,
            branch_id=branch.id,
            sku=sku,
            name="First",
            sale_price=Decimal("5.00"),
        )
    async with SessionFactory() as session, session.begin():
        with pytest.raises(ConflictError):
            await create_product(
                session,
                business_id=business.id,
                branch_id=branch.id,
                sku=sku,
                name="Second",
                sale_price=Decimal("5.00"),
            )
    async with SessionFactory() as session, session.begin():
        deactivated = await set_product_active(
            session, business_id=business.id, product_id=product.id, active=False
        )
        assert deactivated.active is False
        with pytest.raises(NotFoundError):
            await set_product_active(
                session, business_id=uuid4(), product_id=product.id, active=True
            )


@pytest.mark.asyncio
async def test_customer_and_supplier_creation_respects_branch_scope():
    business, branch, _warehouse, _user = await _bootstrap("CAT")
    claims = {"business_id": str(business.id), "branch_id": str(branch.id)}
    async with SessionFactory() as session, session.begin():
        customer = await create_customer(
            session,
            claims=claims,
            business_id=business.id,
            branch_id=branch.id,
            code=f"C{uuid4().hex[:6]}",
            name="Walk-in",
        )
        assert customer.active is True
        with pytest.raises(ForbiddenError):
            await create_customer(
                session,
                claims=claims,
                business_id=business.id,
                branch_id=uuid4(),  # outside the caller's granted branch
                code="C999",
                name="Cross-branch attempt",
            )
    async with SessionFactory() as session, session.begin():
        supplier = await create_supplier(
            session,
            claims={"business_id": str(business.id)},  # unscoped grant allows any own branch
            business_id=business.id,
            branch_id=branch.id,
            code=f"S{uuid4().hex[:6]}",
            name="Acme Wholesale",
        )
        assert supplier.payable_balance == Decimal("0")


@pytest.mark.asyncio
async def test_receive_purchase_stocks_in_and_rolls_weighted_average_cost():
    business, branch, warehouse, _user = await _bootstrap("PUR")
    async with SessionFactory() as session, session.begin():
        product = await create_product(
            session,
            business_id=business.id,
            branch_id=branch.id,
            sku=f"SKU-{uuid4().hex[:6]}",
            name="Costed item",
            sale_price=Decimal("100.00"),
            cost_price=Decimal("10.00"),
        )
    async with SessionFactory() as session, session.begin():
        total = await receive_purchase_lines(
            session,
            business_id=business.id,
            branch_id=branch.id,
            warehouse_id=warehouse.id,
            lines=[(product.id, Decimal("40"), Decimal("20.00"))],
        )
        assert total == Decimal("800.00")
    async with SessionFactory() as session, session.begin():
        balance = await session.scalar(select_balance(product.id, warehouse.id))
        assert balance.quantity == Decimal("40")
        fresh = await session.get(type(product), product.id)
        # WAAP: (0*10 + 40*20) / 40 = 20.00
        assert fresh.cost_price == Decimal("20.00")
        # Second batch of 60 @ 25 -> (40*20 + 60*25)/100 = 23.00
        await receive_purchase_lines(
            session,
            business_id=business.id,
            branch_id=branch.id,
            warehouse_id=warehouse.id,
            lines=[(product.id, Decimal("60"), Decimal("25.00"))],
        )
    async with SessionFactory() as session, session.begin():
        fresh = await session.get(type(product), product.id)
        assert fresh.cost_price == Decimal("23.00")


@pytest.mark.asyncio
async def test_receive_purchase_rejects_invalid_lines_atomically():
    business, branch, warehouse, _user = await _bootstrap("PUR")
    async with SessionFactory() as session, session.begin():
        product = await create_product(
            session,
            business_id=business.id,
            branch_id=branch.id,
            sku=f"SKU-{uuid4().hex[:6]}",
            name="Item",
            sale_price=Decimal("10.00"),
        )
    async with SessionFactory() as session, session.begin():
        with pytest.raises(SaleValidationError):
            await receive_purchase_lines(
                session,
                business_id=business.id,
                branch_id=branch.id,
                warehouse_id=warehouse.id,
                lines=[(product.id, Decimal("-1"), Decimal("5.00"))],
            )
        with pytest.raises(SaleValidationError):
            await receive_purchase_lines(
                session,
                business_id=business.id,
                branch_id=branch.id,
                warehouse_id=warehouse.id,
                lines=[(uuid4(), Decimal("1"), Decimal("5.00"))],  # unknown product
            )
    async with SessionFactory() as session, session.begin():
        balance = await session.scalar(select_balance(product.id, warehouse.id))
        assert balance is None  # nothing persisted from rejected receipts


def select_balance(product_id, warehouse_id):
    from sqlalchemy import select

    return (
        select(StockBalance)
        .where(StockBalance.product_id == product_id)
        .where(StockBalance.warehouse_id == warehouse_id)
    )
