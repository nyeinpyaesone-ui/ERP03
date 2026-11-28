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
from app.models.erp import Customer, Invoice, Product, StockBalance, Warehouse
from app.models.identity import Branch
from app.services.bootstrap import bootstrap_business
from app.services.sales import SaleLine, SalePayment, create_pos_sale
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
                "X-Idempotency-Key": f"sale-{uuid4().hex}",
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

        invoice = await session.scalar(
            select(Invoice).where(Invoice.id == sale.json()["invoice_id"])
        )
        assert invoice is not None
        assert invoice.paid == Decimal("200.00")


@pytest.mark.asyncio
async def test_pos_sale_rollback_restores_stock_after_post_mutation_failure():
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
    async with SessionFactory() as session:
        with pytest.raises(PaymentError):
            await create_pos_sale(
                session,
                business_id=business.id,
                branch_id=branch.id,
                warehouse_id=warehouse.id,
                invoice_no=invoice_no,
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
        assert await session.scalar(select(Invoice).where(Invoice.invoice_no == invoice_no)) is None


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


@pytest.mark.asyncio
async def test_unified_erp_onboarding_catalog_inventory_and_pos():
    """Exercise the product workflow over one async event loop and real DB session."""
    suffix = uuid4().hex[:12]
    business_code = f"TEST-{suffix}"
    email = f"erp-{suffix}@example.com"

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        registered = await client.post(
            "/api/v1/auth/register",
            json={
                "business_code": business_code,
                "business_name": "Integration Test Shop",
                "email": email,
                "password": "LocalTestPass-123",
                "display_name": "Integration Owner",
                "default_currency": "MMK",
                "timezone": "Asia/Yangon",
                "locale": "my-MM",
            },
        )
        assert registered.status_code == 200, registered.text

        logged_in = await client.post(
            "/api/v1/auth/login",
            json={
                "business_code": business_code,
                "email": email,
                "password": "LocalTestPass-123",
            },
        )
        assert logged_in.status_code == 200, logged_in.text
        headers = {"Authorization": f"Bearer {logged_in.json()['access_token']}"}

        context = await client.get("/api/v1/context", headers=headers)
        assert context.status_code == 200, context.text
        branch = context.json()["branches"][0]
        warehouse = context.json()["warehouses"][0]
        assert branch["code"] == "MAIN"
        assert warehouse["code"] == "MAIN"

        product_response = await client.post(
            "/api/v1/products",
            headers=headers,
            json={
                "branch_id": branch["id"],
                "sku": f"SKU-{suffix}",
                "name": "Myanmar Rice 5kg",
                "unit": "bag",
                "sale_price": "1200.00",
                "cost_price": "800.00",
                "min_stock": "2.000",
            },
        )
        assert product_response.status_code == 201, product_response.text
        product = product_response.json()

        customer_response = await client.post(
            "/api/v1/customers",
            headers=headers,
            json={
                "branch_id": branch["id"],
                "code": f"CUS-{suffix}",
                "name": "Walk-in Customer",
                "phone": "09-00000000",
                "credit_limit": "50000.00",
            },
        )
        assert customer_response.status_code == 201, customer_response.text
        customer = customer_response.json()

        receipt = await client.post(
            "/api/v1/purchases/receipts",
            headers=headers,
            json={
                "branch_id": branch["id"],
                "warehouse_id": warehouse["id"],
                "lines": [
                    {
                        "product_id": product["id"],
                        "quantity": "10.000",
                        "unit_cost": "800.00",
                    }
                ],
            },
        )
        assert receipt.status_code == 201, receipt.text

        stock = await client.get("/api/v1/inventory/stock", headers=headers)
        assert stock.status_code == 200, stock.text
        assert stock.json()["items"][0]["quantity"] == "10.000"

        sale = await client.post(
            "/api/v1/sales",
            headers={**headers, "X-Idempotency-Key": f"sale-{suffix}"},
            json={
                "branch_id": branch["id"],
                "warehouse_id": warehouse["id"],
                "customer_id": customer["id"],
                "currency": "MMK",
                "lines": [
                    {
                        "product_id": product["id"],
                        "quantity": "2.000",
                        "unit_price": "1200.00",
                    }
                ],
                "payments": [{"method": "cash", "amount": "1000.00", "currency": "MMK"}],
            },
        )
        assert sale.status_code == 201, sale.text
        assert sale.json()["total"] == "2400.00"
        assert sale.json()["paid"] == "1000.00"
        assert sale.json()["balance"] == "1400.00"

        sales = await client.get("/api/v1/sales?limit=10", headers=headers)
        assert sales.status_code == 200, sales.text
        assert sales.json()["total"] == 1
        assert sales.json()["items"][0]["customer_name"] == "Walk-in Customer"

        summary = await client.get("/api/v1/dashboard/summary", headers=headers)
        assert summary.status_code == 200, summary.text
        assert summary.json()["currency"] == "MMK"
        assert summary.json()["orders_count"] == 1
        assert summary.json()["outstanding_balance"] == "1400.00"

        final_stock = await client.get("/api/v1/inventory/stock", headers=headers)
        assert final_stock.status_code == 200, final_stock.text
        assert final_stock.json()["items"][0]["quantity"] == "8.000"


@pytest.mark.asyncio
async def test_receivable_collection_is_atomic_and_idempotent():
    suffix = uuid4().hex[:12]
    business, branch, warehouse, user = await _bootstrap("RC")
    async with SessionFactory() as session, session.begin():
        customer = Customer(
            business_id=business.id,
            branch_id=branch.id,
            code=f"RC-CUS-{suffix}",
            name="Receivable Test Customer",
            active=True,
        )
        product = Product(
            business_id=business.id,
            branch_id=branch.id,
            sku=f"RC-{suffix}",
            name="Receivable test product",
            unit="pcs",
            sale_price=Decimal("100.00"),
            cost_price=Decimal("50.00"),
            active=True,
        )
        session.add_all([customer, product])
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
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        sale = await client.post(
            "/api/v1/sales",
            headers={**headers, "X-Idempotency-Key": f"rc-sale-{suffix}"},
            json={
                "branch_id": str(branch.id),
                "warehouse_id": str(warehouse.id),
                "customer_id": str(customer.id),
                "currency": "MMK",
                "lines": [{"product_id": str(product.id), "quantity": "1"}],
                "payments": [{"method": "cash", "amount": "40.00", "currency": "MMK"}],
            },
        )
        assert sale.status_code == 201, sale.text
        invoice_id = sale.json()["invoice_id"]
        key = f"rc-collect-{suffix}"
        collect_headers = {**headers, "X-Idempotency-Key": key}
        payload = {
            "invoice_id": invoice_id,
            "amount": "30.00",
            "method": "cash",
            "currency": "MMK",
        }
        first = await client.post(
            "/api/v1/receivables/collect",
            headers=collect_headers,
            json=payload,
        )
        assert first.status_code == 201, first.text
        replay = await client.post(
            "/api/v1/receivables/collect",
            headers=collect_headers,
            json=payload,
        )
        assert replay.status_code == 201, replay.text
        assert replay.json()["payment_id"] == first.json()["payment_id"]
        assert replay.json()["idempotent_replay"] is True
        assert first.json()["balance"] == "30.00"

        outstanding = await client.get("/api/v1/receivables/outstanding", headers=headers)
        assert outstanding.status_code == 200, outstanding.text
        assert outstanding.json()["items"][0]["invoice_id"] == invoice_id
        assert outstanding.json()["items"][0]["balance"] == "30.00"

        overpay = await client.post(
            "/api/v1/receivables/collect",
            headers={**headers, "X-Idempotency-Key": f"over-{suffix}"},
            json={
                "invoice_id": invoice_id,
                "amount": "31.00",
                "method": "cash",
                "currency": "MMK",
            },
        )
        assert overpay.status_code == 422
