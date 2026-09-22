import asyncio
from decimal import Decimal
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.exc import DataError
from app.db.session import SessionFactory
from app.main import app
from app.models.erp import Invoice, Product, StockBalance, Warehouse
from app.models.identity import Branch
from app.services.bootstrap import bootstrap_business
from app.services.sales import SaleLine, SalePayment, create_pos_sale


async def _bootstrap(prefix: str):
    async with SessionFactory() as session:
        async with session.begin():
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
async def test_bootstrap_login_and_pos_sale_round_trip():
    business, branch, warehouse, user = await _bootstrap("IT")

    async with SessionFactory() as session:
        async with session.begin():
            product = Product(
                business_id=business.id,
                branch_id=branch.id,
                sku=f"SKU-{uuid4().hex[:8]}",
                name="Integration Product",
                unit="pcs",
                sale_price=Decimal("100.00"),
                cost_price=Decimal("60.00"),
                min_stock=Decimal("1"),
                active=True,
            )
            session.add(product)
            await session.flush()
            session.add(
                StockBalance(
                    warehouse_id=warehouse.id,
                    product_id=product.id,
                    quantity=Decimal("5"),
                )
            )

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        login = await client.post(
            "/api/v1/auth/login",
            json={
                "business_code": business.code,
                "email": user.email,
                "password": "Correct-Horse-123",
            },
        )
        assert login.status_code == 200, login.text
        token = login.json()["access_token"]

        sale = await client.post(
            "/api/v1/sales",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "branch_id": str(branch.id),
                "warehouse_id": str(warehouse.id),
                "invoice_no": f"INV-{uuid4().hex[:8]}",
                "currency": "MMK",
                "lines": [
                    {
                        "product_id": str(product.id),
                        "quantity": "2",
                    }
                ],
                "payments": [
                    {
                        "method": "cash",
                        "amount": "200.00",
                        "currency": "MMK",
                    }
                ],
            },
        )
        assert sale.status_code == 201, sale.text
        assert sale.json()["total"] == "200.00"
        assert sale.json()["balance"] == "0.00"

    async with SessionFactory() as session:
        balance = await session.scalar(
            select(StockBalance).where(
                StockBalance.warehouse_id == warehouse.id,
                StockBalance.product_id == product.id,
            )
        )
        assert balance is not None
        assert balance.quantity == Decimal("3")

        invoice = await session.scalar(
            select(Invoice).where(Invoice.id == sale.json()["invoice_id"])
        )
        assert invoice is not None
        assert invoice.paid == Decimal("200.00")


@pytest.mark.asyncio
async def test_pos_sale_rollback_restores_stock_after_post_mutation_failure():
    business, branch, warehouse, _ = await _bootstrap("RB")
    async with SessionFactory() as session:
        async with session.begin():
            product = Product(
                business_id=business.id,
                branch_id=branch.id,
                sku=f"SKU-{uuid4().hex[:8]}",
                name="Rollback Product",
                unit="pcs",
                sale_price=Decimal("50.00"),
                cost_price=Decimal("25.00"),
                active=True,
            )
            session.add(product)
            await session.flush()
            session.add(
                StockBalance(
                    warehouse_id=warehouse.id,
                    product_id=product.id,
                    quantity=Decimal("2"),
                )
            )

    async with SessionFactory() as session:
        with pytest.raises(DataError):
            await create_pos_sale(
                session,
                business_id=business.id,
                branch_id=branch.id,
                warehouse_id=warehouse.id,
                invoice_no=f"INV-{uuid4().hex[:8]}",
                lines=[SaleLine(product.id, Decimal("1"))],
                payments=[SalePayment(method="x" * 33, amount=Decimal("50"))],
            )
        await session.rollback()

    async with SessionFactory() as session:
        balance = await session.scalar(
            select(StockBalance).where(
                StockBalance.warehouse_id == warehouse.id,
                StockBalance.product_id == product.id,
            )
        )
        assert balance is not None
        assert balance.quantity == Decimal("2")
        assert await session.scalar(
            select(Invoice).where(Invoice.id == product.id)
        ) is None


@pytest.mark.asyncio
async def test_concurrent_sales_cannot_oversell_stock():
    business, branch, warehouse, _ = await _bootstrap("CC")
    async with SessionFactory() as session:
        async with session.begin():
            product = Product(
                business_id=business.id,
                branch_id=branch.id,
                sku=f"SKU-{uuid4().hex[:8]}",
                name="Concurrent Product",
                unit="pcs",
                sale_price=Decimal("100.00"),
                cost_price=Decimal("50.00"),
                active=True,
            )
            session.add(product)
            await session.flush()
            session.add(
                StockBalance(
                    warehouse_id=warehouse.id,
                    product_id=product.id,
                    quantity=Decimal("1"),
                )
            )

    async def attempt(invoice_no: str):
        async with SessionFactory() as session:
            try:
                result = await create_pos_sale(
                    session,
                    business_id=business.id,
                    branch_id=branch.id,
                    warehouse_id=warehouse.id,
                    invoice_no=invoice_no,
                    lines=[SaleLine(product.id, Decimal("1"))],
                    payments=[SalePayment(method="cash", amount=Decimal("100"))],
                )
                return ("ok", result.invoice_id)
            except Exception as exc:
                return ("error", type(exc).__name__)

    results = await asyncio.gather(
        attempt(f"INV-{uuid4().hex[:8]}"),
        attempt(f"INV-{uuid4().hex[:8]}"),
    )
    assert sum(result[0] == "ok" for result in results) == 1

    async with SessionFactory() as session:
        balance = await session.scalar(
            select(StockBalance).where(
                StockBalance.warehouse_id == warehouse.id,
                StockBalance.product_id == product.id,
            )
        )
        assert balance is not None
        assert balance.quantity == Decimal("0")


@pytest.mark.asyncio
async def test_owner_token_cannot_cross_branch_boundary():
    business, branch, warehouse, user = await _bootstrap("BR")
    async with SessionFactory() as session:
        async with session.begin():
            other_branch = Branch(
                business_id=business.id,
                name="Other Branch",
                code=f"OTHER-{uuid4().hex[:6]}",
                active=True,
            )
            session.add(other_branch)
            await session.flush()

            other_warehouse = Warehouse(
                branch_id=other_branch.id,
                code="MAIN",
                name="Other Warehouse",
                active=True,
            )
            session.add(other_warehouse)
            product = Product(
                business_id=business.id,
                branch_id=other_branch.id,
                sku=f"SKU-{uuid4().hex[:8]}",
                name="Other Branch Product",
                unit="pcs",
                sale_price=Decimal("25.00"),
                cost_price=Decimal("10.00"),
                active=True,
            )
            session.add(product)
            await session.flush()
            session.add(
                StockBalance(
                    warehouse_id=other_warehouse.id,
                    product_id=product.id,
                    quantity=Decimal("5"),
                )
            )

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        login = await client.post(
            "/api/v1/auth/login",
            json={
                "business_code": business.code,
                "email": user.email,
                "password": "Correct-Horse-123",
            },
        )
        assert login.status_code == 200
        token = login.json()["access_token"]

        sale = await client.post(
            "/api/v1/sales",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "branch_id": str(other_branch.id),
                "warehouse_id": str(other_warehouse.id),
                "invoice_no": f"INV-{uuid4().hex[:8]}",
                "currency": "MMK",
                "lines": [{"product_id": str(product.id), "quantity": "1"}],
                "payments": [],
            },
        )
        assert sale.status_code == 403
