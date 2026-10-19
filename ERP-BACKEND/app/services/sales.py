"""Atomic POS sale application service."""

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, PaymentError, SaleValidationError
from app.models.erp import Customer, Invoice, InvoiceItem, Payment, Product, Warehouse
from app.models.identity import Branch
from app.services.inventory import adjust_stock


async def _find_idempotent_invoice(
    session: AsyncSession, business_id: UUID, branch_id: UUID, key: str
) -> Invoice | None:
    """Return the invoice already recorded for ``key`` in this tenant scope."""
    return await session.scalar(
        select(Invoice).where(
            Invoice.business_id == business_id,
            Invoice.branch_id == branch_id,
            Invoice.idempotency_key == key,
        )
    )


async def next_invoice_no(session: AsyncSession, *, branch_id: UUID) -> str:
    """Allocate a gap-free per-branch invoice number (``INV-YYYYMM-000001``).

    Callers must invoke this inside the same transaction that inserts the
    invoice; the branch-row lock taken by ``create_pos_sale`` serialises
    allocation per branch so concurrent tills never reuse a number.
    """
    prefix = f"INV-{datetime.now(UTC):%Y%m}-"
    last = await session.scalar(
        select(func.max(Invoice.invoice_no)).where(
            Invoice.branch_id == branch_id, Invoice.invoice_no.like(f"{prefix}%")
        )
    )
    sequence = int(last[len(prefix) :]) + 1 if last else 1
    return f"{prefix}{sequence:06d}"


def _sale_fingerprint(
    *,
    business_id: UUID,
    branch_id: UUID,
    warehouse_id: UUID,
    invoice_no: str | None,
    lines: list["SaleLine"],
    payments: list["SalePayment"],
    customer_id: UUID | None,
    currency: str,
) -> str:
    """Canonical SHA-256 digest of the sale command for idempotency conflict detection."""
    payload = {
        "business_id": str(business_id),
        "branch_id": str(branch_id),
        "warehouse_id": str(warehouse_id),
        "invoice_no": invoice_no,
        "customer_id": str(customer_id) if customer_id else None,
        "currency": currency.upper(),
        "lines": sorted(
            [
                {
                    "product_id": str(line.product_id),
                    "quantity": str(line.quantity),
                    "unit_price": str(line.unit_price) if line.unit_price is not None else None,
                    "discount": str(line.discount),
                    "tax": str(line.tax),
                }
                for line in lines
            ],
            key=lambda item: item["product_id"],
        ),
        "payments": sorted(
            [
                {
                    "method": payment.method,
                    "amount": str(payment.amount),
                    "currency": payment.currency,
                    "reference": payment.reference,
                }
                for payment in payments
            ],
            key=lambda item: item["method"],
        ),
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class SaleLine:
    product_id: UUID
    quantity: Decimal
    unit_price: Decimal | None = None
    discount: Decimal = Decimal("0")
    tax: Decimal = Decimal("0")


@dataclass(frozen=True, slots=True)
class SalePayment:
    method: str
    amount: Decimal
    reference: str | None = None
    currency: str = "MMK"


@dataclass(frozen=True, slots=True)
class SaleResult:
    invoice_id: UUID
    total: Decimal
    paid: Decimal
    balance: Decimal

    @classmethod
    def from_invoice(cls, invoice: Invoice) -> "SaleResult":
        """Build a replay result from an already-persisted invoice."""
        return cls(
            invoice_id=invoice.id,
            total=invoice.total,
            paid=invoice.paid,
            balance=invoice.total - invoice.paid,
        )


async def create_pos_sale(
    session: AsyncSession,
    *,
    business_id: UUID,
    branch_id: UUID,
    warehouse_id: UUID,
    invoice_no: str | None = None,
    lines: list[SaleLine],
    payments: list[SalePayment],
    customer_id: UUID | None = None,
    currency: str = "MMK",
    idempotency_key: str | None = None,
) -> SaleResult:
    """Create invoice, inventory movements and payments in one DB transaction."""
    if not lines:
        raise SaleValidationError("A sale must contain at least one line")
    if invoice_no is not None and (not invoice_no.strip() or len(invoice_no) > 64):
        raise SaleValidationError("invoice_no must be 1-64 characters")
    if any(line.quantity <= 0 for line in lines):
        raise SaleValidationError("Line quantities must be positive")
    if any(line.discount < 0 or line.tax < 0 for line in lines):
        raise SaleValidationError("Discount and tax cannot be negative")
    if any(payment.amount <= 0 for payment in payments):
        raise PaymentError("Payment amounts must be positive")
    if any(not payment.method.strip() or len(payment.method) > 32 for payment in payments):
        raise PaymentError("Payment method must be 1-32 characters")
    if idempotency_key is not None and not idempotency_key.strip():
        raise SaleValidationError("Idempotency key cannot be empty")
    if idempotency_key is not None and len(idempotency_key) > 255:
        raise SaleValidationError("Idempotency key must be <= 255 characters")
    if any(payment.currency.upper() != currency.upper() for payment in payments):
        raise SaleValidationError("Payment currency must match invoice currency")

    # Cheap invariant checks run before acquiring locks or opening a
    # transaction so invalid requests never touch database resources.
    if all(line.unit_price is not None for line in lines):
        requested_total = sum(
            (line.unit_price * line.quantity - line.discount + line.tax for line in lines),
            Decimal("0"),
        )
        requested_paid = sum((payment.amount for payment in payments), Decimal("0"))
        if requested_total >= 0 and requested_paid > requested_total:
            raise PaymentError("Overpayment is not allowed")

    fingerprint = _sale_fingerprint(
        business_id=business_id,
        branch_id=branch_id,
        warehouse_id=warehouse_id,
        invoice_no=invoice_no,
        lines=lines,
        payments=payments,
        customer_id=customer_id,
        currency=currency,
    )

    async with session.begin():
        branch = await session.scalar(
            select(Branch)
            .where(
                Branch.id == branch_id,
                Branch.business_id == business_id,
                Branch.active.is_(True),
            )
            .with_for_update()
        )
        if branch is None:
            raise SaleValidationError("Branch is not valid for this business")

        warehouse = await session.scalar(
            select(Warehouse)
            .where(
                Warehouse.id == warehouse_id,
                Warehouse.branch_id == branch_id,
                Warehouse.active.is_(True),
            )
            .with_for_update()
        )
        if warehouse is None:
            raise SaleValidationError("Warehouse is not valid for this branch")

        if customer_id is not None:
            customer = await session.scalar(
                select(Customer)
                .where(
                    Customer.id == customer_id,
                    Customer.business_id == business_id,
                    Customer.branch_id == branch_id,
                    Customer.active.is_(True),
                )
                .with_for_update()
            )
            if customer is None:
                raise SaleValidationError("Customer is not valid for this branch")

        if invoice_no is None:
            invoice_no = await next_invoice_no(session, branch_id=branch_id)

        product_ids = sorted({line.product_id for line in lines}, key=str)
        products_result = await session.execute(
            select(Product)
            .where(
                Product.id.in_(product_ids),
                Product.business_id == business_id,
                Product.branch_id == branch_id,
                Product.active.is_(True),
            )
            .with_for_update()
        )
        products = {product.id: product for product in products_result.scalars().all()}
        if len(products) != len(product_ids):
            raise SaleValidationError("One or more products are invalid for this branch")

        subtotal = Decimal("0")
        discount_total = Decimal("0")
        tax_total = Decimal("0")
        prepared: list[tuple[SaleLine, Decimal, Decimal]] = []
        for line in lines:
            product = products[line.product_id]
            price = product.sale_price if line.unit_price is None else line.unit_price
            if price < 0:
                raise SaleValidationError("Unit price cannot be negative")
            line_subtotal = price * line.quantity
            line_total = line_subtotal - line.discount + line.tax
            if line.discount > line_subtotal or line_total < 0:
                raise SaleValidationError("Invalid line discount/tax")
            subtotal += line_subtotal
            discount_total += line.discount
            tax_total += line.tax
            prepared.append((line, price, line_total))

        total = subtotal - discount_total + tax_total
        paid = sum((payment.amount for payment in payments), Decimal("0"))
        if paid > total:
            raise PaymentError("Overpayment is not allowed")

        if idempotency_key is not None:
            existing = await session.scalar(
                select(Invoice)
                .where(
                    Invoice.business_id == business_id,
                    Invoice.branch_id == branch_id,
                    Invoice.idempotency_key == idempotency_key,
                )
                .with_for_update()
            )
            if existing is not None:
                if (
                    existing.request_fingerprint is not None
                    and existing.request_fingerprint != fingerprint
                ):
                    raise ConflictError("Idempotency key was already used for a different sale")
                return SaleResult.from_invoice(existing)

        invoice = Invoice(
            business_id=business_id,
            branch_id=branch_id,
            customer_id=customer_id,
            invoice_no=invoice_no,
            idempotency_key=idempotency_key,
            request_fingerprint=fingerprint,
            status="paid" if paid == total else ("partial" if paid else "confirmed"),
            currency=currency.upper(),
            subtotal=subtotal,
            discount=discount_total,
            tax=tax_total,
            total=total,
            paid=paid,
        )
        try:
            async with session.begin_nested():
                session.add(invoice)
                await session.flush()
        except IntegrityError as exc:
            # The savepoint rolled back only the invoice insert; the outer
            # transaction is still usable. A concurrent request may have
            # committed the same idempotency key first — replay its result
            # instead of failing. Any other constraint violation (e.g. a
            # duplicate invoice_no) surfaces as a typed conflict.
            if idempotency_key is not None:
                existing = await _find_idempotent_invoice(
                    session, business_id, branch_id, idempotency_key
                )
                if existing is not None:
                    return SaleResult.from_invoice(existing)
            raise ConflictError("Invoice number already exists for this branch") from exc

        prepared.sort(key=lambda item: str(item[0].product_id))
        for line, price, line_total in prepared:
            session.add(
                InvoiceItem(
                    invoice_id=invoice.id,
                    product_id=line.product_id,
                    quantity=line.quantity,
                    unit_price=price,
                    discount=line.discount,
                    tax=line.tax,
                    line_total=line_total,
                )
            )
            await adjust_stock(
                session,
                warehouse_id=warehouse_id,
                product_id=line.product_id,
                quantity_delta=-line.quantity,
                movement_type="sale",
                unit_cost=products[line.product_id].cost_price,
                reference_type="invoice",
                reference_id=invoice.id,
            )

        for payment in payments:
            # Flush inside a savepoint so a rejected payment row (e.g. a
            # database-level DataError/IntegrityError) rolls back only this
            # statement; the outer transaction stays usable and the caller's
            # rollback restores every earlier mutation (stock included).
            async with session.begin_nested():
                session.add(
                    Payment(
                        business_id=business_id,
                        branch_id=branch_id,
                        invoice_id=invoice.id,
                        method=payment.method,
                        currency=payment.currency.upper(),
                        amount=payment.amount,
                        reference=payment.reference,
                    )
                )
                await session.flush()

        return SaleResult(
            invoice_id=invoice.id,
            total=total,
            paid=paid,
            balance=total - paid,
        )
