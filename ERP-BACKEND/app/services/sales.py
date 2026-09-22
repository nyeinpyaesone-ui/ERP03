"""Atomic POS sale application service."""

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.erp import Customer, Invoice, InvoiceItem, Product, Payment
from app.services.inventory import adjust_stock


class SaleValidationError(ValueError):
    """Raised when a POS sale violates a business invariant."""


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


async def create_pos_sale(
    session: AsyncSession,
    *,
    business_id: UUID,
    branch_id: UUID,
    warehouse_id: UUID,
    invoice_no: str,
    lines: list[SaleLine],
    payments: list[SalePayment],
    customer_id: UUID | None = None,
    currency: str = "MMK",
) -> SaleResult:
    """Create invoice, inventory movements and payments in one DB transaction."""
    if not lines:
        raise SaleValidationError("A sale must contain at least one line")
    if any(line.quantity <= 0 for line in lines):
        raise SaleValidationError("Line quantities must be positive")
    if any(line.discount < 0 or line.tax < 0 for line in lines):
        raise SaleValidationError("Discount and tax cannot be negative")
    if any(payment.amount <= 0 for payment in payments):
        raise SaleValidationError("Payment amounts must be positive")
    if any(payment.currency != currency for payment in payments):
        raise SaleValidationError("Payment currency must match invoice currency")

    async with session.begin():
        if customer_id is not None:
            customer = await session.scalar(
                select(Customer).where(
                    Customer.id == customer_id,
                    Customer.business_id == business_id,
                    Customer.branch_id == branch_id,
                    Customer.active.is_(True),
                ).with_for_update()
            )
            if customer is None:
                raise SaleValidationError("Customer is not valid for this branch")

        product_ids = sorted({line.product_id for line in lines}, key=str)
        products_result = await session.execute(
            select(Product).where(
                Product.id.in_(product_ids),
                Product.business_id == business_id,
                Product.branch_id == branch_id,
                Product.active.is_(True),
            ).with_for_update()
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
            raise SaleValidationError("Overpayment is not allowed")

        invoice = Invoice(
            business_id=business_id,
            branch_id=branch_id,
            customer_id=customer_id,
            invoice_no=invoice_no,
            status="paid" if paid == total else ("partial" if paid else "confirmed"),
            currency=currency,
            subtotal=subtotal,
            discount=discount_total,
            tax=tax_total,
            total=total,
            paid=paid,
        )
        session.add(invoice)
        await session.flush()

        # Lock stock rows in deterministic product order to reduce deadlock risk
        # when concurrent cashiers sell overlapping multi-line baskets.
        prepared.sort(key=lambda item: str(item[0].product_id))
        for line, price, line_total in prepared:
            session.add(InvoiceItem(
                invoice_id=invoice.id,
                product_id=line.product_id,
                quantity=line.quantity,
                unit_price=price,
                discount=line.discount,
                tax=line.tax,
                line_total=line_total,
            ))
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
            session.add(Payment(
                business_id=business_id,
                branch_id=branch_id,
                invoice_id=invoice.id,
                method=payment.method,
                currency=payment.currency,
                amount=payment.amount,
                reference=payment.reference,
            ))

        return SaleResult(
            invoice_id=invoice.id,
            total=total,
            paid=paid,
            balance=total - paid,
        )
