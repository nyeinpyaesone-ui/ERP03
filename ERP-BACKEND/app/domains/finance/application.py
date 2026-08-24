from __future__ import annotations

from datetime import date

from app.models import Invoice, InvoiceItem, Payment
from .domain import InvoiceLine, calculate_invoice_totals, validate_payment
from .infrastructure import FinanceRepository


def create_invoice(db, *, invoice_number: str, contact_id, company_id, issue_date, due_date,
                    tax_rate: float, notes, terms, items: list[dict]) -> Invoice:
    repo = FinanceRepository(db)
    if repo.invoice_number_exists(invoice_number):
        raise ValueError(f"Invoice number '{invoice_number}' already exists")

    lines = [InvoiceLine(description=i["description"], quantity=i["quantity"], unit_price=i["unit_price"])
             for i in items]
    totals = calculate_invoice_totals(lines, tax_rate)

    invoice = Invoice(
        invoice_number=invoice_number,
        contact_id=contact_id,
        company_id=company_id,
        issue_date=issue_date,
        due_date=due_date,
        tax_rate=tax_rate,
        notes=notes,
        terms=terms,
        subtotal=totals.subtotal,
        tax_amount=totals.tax_amount,
        total=totals.total,
        amount_paid=0,
        status="draft",
    )
    invoice_items = [
        InvoiceItem(
            product_id=i.get("product_id"),
            description=i["description"],
            quantity=i["quantity"],
            unit_price=i["unit_price"],
            total=i["quantity"] * i["unit_price"],
        )
        for i in items
    ]
    return repo.save_invoice(invoice, invoice_items)


def record_payment(db, *, invoice_id: int, amount: float, payment_method: str, payment_date: date) -> Payment:
    repo = FinanceRepository(db)
    invoice = repo.get_invoice(invoice_id)
    if invoice is None:
        raise ValueError(f"Invoice {invoice_id} not found")

    validate_payment(amount, invoice.total, invoice.amount_paid)

    payment = Payment(
        invoice_id=invoice_id,
        amount=amount,
        payment_method=payment_method,
        payment_date=payment_date,
    )
    saved = repo.save_payment(payment)

    invoice.amount_paid = float(invoice.amount_paid) + float(amount)
    invoice.status = "paid" if invoice.amount_paid >= float(invoice.total) else "partial"
    db.commit()

    return saved


def get_invoice(db, *, invoice_id: int) -> Invoice | None:
    return FinanceRepository(db).get_invoice(invoice_id)


def list_invoices(db, *, status: str | None = None, contact_id: int | None = None) -> list[Invoice]:
    return FinanceRepository(db).list_invoices(status=status, contact_id=contact_id)


def dashboard(db) -> dict:
    return FinanceRepository(db).dashboard_metrics(today=date.today())
