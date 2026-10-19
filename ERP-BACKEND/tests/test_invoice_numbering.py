"""Coverage for auto invoice numbering and typed payment errors."""

from decimal import Decimal
from uuid import uuid4

import pytest
from app.core.errors import ConflictError
from app.db.session import SessionFactory
from app.main import app
from app.models.erp import Invoice
from app.models.identity import Branch
from app.services.bootstrap import bootstrap_business
from app.services.sales import SaleLine, SalePayment, create_pos_sale, next_invoice_no

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
async def test_sale_without_invoice_no_allocates_sequential_numbers():
    business, branch, warehouse, _user = await _bootstrap("NUM")
    async with SessionFactory() as session, session.begin():
        from app.models.erp import Product, StockBalance

        product = Product(
            business_id=business.id,
            branch_id=branch.id,
            sku=f"SKU-{uuid4().hex[:6]}",
            name="Numbered item",
            sale_price=Decimal("10.00"),
            active=True,
        )
        session.add(product)
        await session.flush()
        session.add(
            StockBalance(warehouse_id=warehouse.id, product_id=product.id, quantity=Decimal("5"))
        )

    numbers = []
    for _ in range(3):
        async with SessionFactory() as session:
            result = await create_pos_sale(
                session,
                business_id=business.id,
                branch_id=branch.id,
                warehouse_id=warehouse.id,
                lines=[SaleLine(product_id=product.id, quantity=Decimal("1"))],
                payments=[],
            )
            await session.commit()
            invoice = await session.get(Invoice, result.invoice_id)
            numbers.append(invoice.invoice_no)
    assert len(set(numbers)) == 3
    suffixes = sorted(int(n.rsplit("-", 1)[1]) for n in numbers)
    assert suffixes == list(range(suffixes[0], suffixes[0] + 3))  # gap-free sequence


@pytest.mark.asyncio
async def test_next_invoice_no_is_branch_scoped():
    business, branch, _warehouse, _user = await _bootstrap("NUM")
    async with SessionFactory() as session, session.begin():
        other = Branch(
            business_id=business.id,
            code="OTHER",
            name="Other Branch",
            active=True,
        )
        session.add(other)
        await session.flush()
        first = await next_invoice_no(session, branch_id=branch.id)
        second = await next_invoice_no(session, branch_id=other.id)
        assert first.endswith("-000001")
        assert second.endswith("-000001")  # independent per-branch sequences


@pytest.mark.asyncio
async def test_overpayment_maps_to_payment_error_code_via_http(client=None):
    """The stable error envelope distinguishes PAYMENT_ERROR from sale errors."""
    import httpx

    business, branch, warehouse, user = await _bootstrap("PAY")
    async with SessionFactory() as session, session.begin():
        from app.models.erp import Product, StockBalance

        product = Product(
            business_id=business.id,
            branch_id=branch.id,
            sku=f"SKU-{uuid4().hex[:6]}",
            name="Paid item",
            sale_price=Decimal("10.00"),
            active=True,
        )
        session.add(product)
        await session.flush()
        session.add(
            StockBalance(warehouse_id=warehouse.id, product_id=product.id, quantity=Decimal("5"))
        )

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as http:
        login = await http.post(
            "/api/v1/auth/login",
            json={
                "business_code": business.code,
                "email": user.email,
                "password": "Correct-Horse-123",
            },
        )
        token = login.json()["access_token"]
        response = await http.post(
            "/api/v1/sales",
            headers={
                "Authorization": f"Bearer {token}",
                "X-Idempotency-Key": f"overpayment-{uuid4().hex}",
            },
            json={
                "branch_id": str(branch.id),
                "warehouse_id": str(warehouse.id),
                "lines": [{"product_id": str(product.id), "quantity": "1"}],
                "payments": [{"method": "cash", "amount": "999.00"}],
            },
        )
        assert response.status_code == 400
        body = response.json()
        assert body["error"]["code"] == "PAYMENT_ERROR"


@pytest.mark.asyncio
async def test_same_idempotency_key_same_payload_replays_invoice():
    """Same key + same fingerprint returns the original invoice result."""
    business, branch, warehouse, user = await _bootstrap("IDEMP")
    async with SessionFactory() as session, session.begin():
        from app.models.erp import Product, StockBalance

        product = Product(
            business_id=business.id,
            branch_id=branch.id,
            sku=f"SKU-{uuid4().hex[:6]}",
            name="Idempotent item",
            sale_price=Decimal("10.00"),
            active=True,
        )
        session.add(product)
        await session.flush()
        session.add(
            StockBalance(warehouse_id=warehouse.id, product_id=product.id, quantity=Decimal("5"))
        )

    key = f"idem-{uuid4().hex}"
    lines = [SaleLine(product_id=product.id, quantity=Decimal("1"))]
    payments = [SalePayment(method="cash", amount=Decimal("10.00"))]

    async with SessionFactory() as session:
        first = await create_pos_sale(
            session,
            business_id=business.id,
            branch_id=branch.id,
            warehouse_id=warehouse.id,
            lines=lines,
            payments=payments,
            idempotency_key=key,
        )
        await session.commit()
    assert first.invoice_id is not None

    async with SessionFactory() as session:
        second = await create_pos_sale(
            session,
            business_id=business.id,
            branch_id=branch.id,
            warehouse_id=warehouse.id,
            lines=lines,
            payments=payments,
            idempotency_key=key,
        )
        await session.commit()
    assert second.invoice_id == first.invoice_id


@pytest.mark.asyncio
async def test_same_idempotency_key_different_payload_returns_conflict():
    """Same key + different fingerprint raises ConflictError within the same DB transaction."""
    business, branch, warehouse, user = await _bootstrap("IDEMC")
    async with SessionFactory() as session, session.begin():
        from app.models.erp import Product, StockBalance

        product = Product(
            business_id=business.id,
            branch_id=branch.id,
            sku=f"SKU-{uuid4().hex[:6]}",
            name="Conflict item",
            sale_price=Decimal("10.00"),
            active=True,
        )
        session.add(product)
        await session.flush()
        session.add(
            StockBalance(warehouse_id=warehouse.id, product_id=product.id, quantity=Decimal("5"))
        )

    key = f"idemc-{uuid4().hex}"
    lines = [SaleLine(product_id=product.id, quantity=Decimal("1"))]
    payments = [SalePayment(method="cash", amount=Decimal("10.00"))]

    async with SessionFactory() as session:
        first = await create_pos_sale(
            session,
            business_id=business.id,
            branch_id=branch.id,
            warehouse_id=warehouse.id,
            lines=lines,
            payments=payments,
            idempotency_key=key,
        )
        await session.commit()
    assert first.invoice_id is not None

    different_lines = [SaleLine(product_id=product.id, quantity=Decimal("2"))]
    different_payments = [SalePayment(method="cash", amount=Decimal("20.00"))]

    async with SessionFactory() as session:
        with pytest.raises(ConflictError):
            await create_pos_sale(
                session,
                business_id=business.id,
                branch_id=branch.id,
                warehouse_id=warehouse.id,
                lines=different_lines,
                payments=different_payments,
                idempotency_key=key,
            )
        await session.commit()
