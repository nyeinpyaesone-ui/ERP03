import asyncio
import os
from decimal import Decimal
from uuid import uuid4

import app.models  # noqa: F401  (ensures all mappers are configured)
import httpx
import pytest
from app.core.errors import PaymentError
from app.db.session import SessionFactory
from app.main import app
from app.models.erp import Invoice, Product, StockBalance, Warehouse
from app.models.identity import Branch
from app.models.operations import Operation, OperationState
from app.services import sales as sales_service
from app.services.bootstrap import bootstrap_business
from app.services.inventory import adjust_stock as real_adjust_stock
from app.services.sales import SaleLine, SalePayment, create_pos_sale, sale_operation_id
from sqlalchemy import select

pytestmark = pytest.mark.integration  # migrated DB provisioned by conftest (SQLite or PostgreSQL)

# Concurrency guard: SQLite serialises writers at the file level, so the
# oversell test only proves row-lock semantics on a real client/server DB.
_requires_concurrent_db = pytest.mark.skipif(
    os.environ.get("DATABASE_URL", "").startswith("sqlite"),
    reason="concurrent row-lock semantics require PostgreSQL (SQLite serialises writers)",
)


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
async def test_bootstrap_login_and_pos_sale_round_trip():
    business, branch, warehouse, user = await _bootstrap("IT")

    async with SessionFactory() as session, session.begin():
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

    key = f"sale-{uuid4().hex}"
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
            headers={
                "Authorization": f"Bearer {token}",
                "X-Idempotency-Key": key,
            },
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
        operation = await session.scalar(
            select(Operation).where(
                Operation.operation_id
                == sale_operation_id(business.id, branch.id, f"{business.id}:{key}")
            )
        )
        assert operation is not None
        assert operation.state == OperationState.COMMITTED
        assert operation.result_json == {
            "invoice_id": sale.json()["invoice_id"],
            "total": "200.00",
            "paid": "200.00",
            "balance": "0.00",
        }

        invoice = await session.scalar(
            select(Invoice).where(Invoice.id == sale.json()["invoice_id"])
        )
        assert invoice is not None
        assert invoice.paid == Decimal("200.00")


@pytest.mark.asyncio
async def test_pos_sale_rollback_restores_stock_and_operation_after_post_mutation_failure(
    monkeypatch,
):
    business, branch, warehouse, _ = await _bootstrap("RB")
    async with SessionFactory() as session, session.begin():
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

    invoice_no = f"INV-{uuid4().hex[:8]}"
    key = f"rollback-{uuid4().hex}"

    async def fail_after_stock(*args, **kwargs):
        await real_adjust_stock(*args, **kwargs)
        raise PaymentError("injected failure after stock mutation")

    monkeypatch.setattr(sales_service, "adjust_stock", fail_after_stock)
    async with SessionFactory() as session:
        with pytest.raises(PaymentError, match="injected failure"):
            await create_pos_sale(
                session,
                business_id=business.id,
                branch_id=branch.id,
                warehouse_id=warehouse.id,
                invoice_no=invoice_no,
                lines=[SaleLine(product.id, Decimal("1"))],
                payments=[SalePayment(method="cash", amount=Decimal("50"))],
                idempotency_key=f"{business.id}:{key}",
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
        assert await session.scalar(select(Invoice).where(Invoice.invoice_no == invoice_no)) is None
        operation = await session.scalar(
            select(Operation).where(
                Operation.operation_id
                == sale_operation_id(business.id, branch.id, f"{business.id}:{key}")
            )
        )
        assert operation is None


@pytest.mark.asyncio
@_requires_concurrent_db
async def test_concurrent_sales_cannot_oversell_stock():
    business, branch, warehouse, _ = await _bootstrap("CC")
    async with SessionFactory() as session, session.begin():
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


@pytest.mark.skipif(
    os.environ.get("DATABASE_URL", "").startswith("sqlite"),
    reason="concurrent idempotency replay requires PostgreSQL row locks",
)
@pytest.mark.asyncio
async def test_concurrent_replay_with_same_idempotency_key_commits_once():
    """Concurrent delivery of one request returns one invoice and one stock decrement."""
    business, branch, warehouse, _user = await _bootstrap("IDCC")
    async with SessionFactory() as session, session.begin():
        product = Product(
            business_id=business.id,
            branch_id=branch.id,
            sku=f"SKU-{uuid4().hex[:8]}",
            name="Concurrent Idempotency Product",
            unit="pcs",
            sale_price=Decimal("100.00"),
            cost_price=Decimal("60.00"),
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

    key = f"{business.id}:concurrent-{uuid4().hex}"
    invoice_no = f"INV-{uuid4().hex[:12]}"

    async def attempt():
        async with SessionFactory() as session:
            return await create_pos_sale(
                session,
                business_id=business.id,
                branch_id=branch.id,
                warehouse_id=warehouse.id,
                invoice_no=invoice_no,
                lines=[SaleLine(product.id, Decimal("1"))],
                payments=[SalePayment(method="cash", amount=Decimal("100.00"))],
                idempotency_key=key,
            )

    first, second = await asyncio.gather(attempt(), attempt())
    assert first.invoice_id == second.invoice_id

    async with SessionFactory() as session:
        balance = await session.scalar(
            select(StockBalance).where(
                StockBalance.warehouse_id == warehouse.id,
                StockBalance.product_id == product.id,
            )
        )
        invoices = (
            await session.scalars(
                select(Invoice).where(
                    Invoice.business_id == business.id,
                    Invoice.branch_id == branch.id,
                    Invoice.idempotency_key == key,
                )
            )
        ).all()
        operation = await session.scalar(
            select(Operation).where(
                Operation.operation_id == sale_operation_id(business.id, branch.id, key)
            )
        )
    assert balance is not None and balance.quantity == Decimal("4")
    assert len(invoices) == 1
    assert operation is not None and operation.state == OperationState.COMMITTED

@pytest.mark.asyncio
async def test_owner_token_cannot_cross_branch_boundary():
    business, branch, warehouse, user = await _bootstrap("BR")
    async with SessionFactory() as session, session.begin():
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


@pytest.mark.asyncio
async def test_pos_sale_idempotency_replays_same_invoice_without_double_stock():
    business, branch, warehouse, user = await _bootstrap("ID")
    async with SessionFactory() as session, session.begin():
        product = Product(
            business_id=business.id,
            branch_id=branch.id,
            sku=f"SKU-{uuid4().hex[:8]}",
            name="Idempotency Product",
            unit="pcs",
            sale_price=Decimal("100.00"),
            cost_price=Decimal("60.00"),
            active=True,
        )
        session.add(product)
        await session.flush()
        session.add(
            StockBalance(warehouse_id=warehouse.id, product_id=product.id, quantity=Decimal("5"))
        )

    key = f"retry-{uuid4().hex}"
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
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
        headers = {"Authorization": f"Bearer {token}", "X-Idempotency-Key": key}
        payload = {
            "branch_id": str(branch.id),
            "warehouse_id": str(warehouse.id),
            "invoice_no": f"INV-{uuid4().hex[:8]}",
            "currency": "MMK",
            "lines": [{"product_id": str(product.id), "quantity": "2"}],
            "payments": [{"method": "cash", "amount": "200.00", "currency": "MMK"}],
        }
        first = await client.post("/api/v1/sales", headers=headers, json=payload)
        assert first.status_code == 201, first.text
        second = await client.post("/api/v1/sales", headers=headers, json=payload)
        assert second.status_code == 201, second.text
        assert second.json()["invoice_id"] == first.json()["invoice_id"]

    async with SessionFactory() as session:
        balance = await session.scalar(
            select(StockBalance).where(
                StockBalance.warehouse_id == warehouse.id,
                StockBalance.product_id == product.id,
            )
        )
        assert balance is not None
        assert balance.quantity == Decimal("3")
