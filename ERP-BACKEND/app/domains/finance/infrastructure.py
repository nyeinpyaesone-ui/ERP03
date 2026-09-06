from __future__ import annotations

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Invoice, InvoiceItem, Payment


class FinanceRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def invoice_number_exists(self, invoice_number: str) -> bool:
        return self.db.query(Invoice).filter(Invoice.invoice_number == invoice_number).first() is not None

    def next_invoice_number(self) -> str:
        count = self.db.query(Invoice).count() + 1
        return f"INV-{count:06d}"

    def save_invoice(self, invoice: Invoice, items: list[InvoiceItem]) -> Invoice:
        self.db.add(invoice)
        self.db.flush()
        for item in items:
            item.invoice_id = invoice.id
            self.db.add(item)
        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def get_invoice(self, invoice_id: int) -> Invoice | None:
        return self.db.query(Invoice).filter(Invoice.id == invoice_id).first()

    def list_invoices(self, *, status: str | None = None, contact_id: int | None = None) -> list[Invoice]:
        query = self.db.query(Invoice)
        if status:
            query = query.filter(Invoice.status == status)
        if contact_id:
            query = query.filter(Invoice.contact_id == contact_id)
        return query.all()

    def save_payment(self, payment: Payment) -> Payment:
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        return payment

    def dashboard_metrics(self, *, today) -> dict:
        total_invoices = self.db.query(Invoice).count()
        total_revenue = self.db.query(func.sum(Invoice.amount_paid)).scalar() or 0
        outstanding = (
            self.db.query(func.sum(Invoice.total - Invoice.amount_paid))
            .filter(Invoice.status != "paid")
            .scalar()
            or 0
        )
        overdue = self.db.query(Invoice).filter(Invoice.due_date < today, Invoice.status != "paid").count()
        return {
            "total_invoices": total_invoices,
            "total_revenue": total_revenue,
            "outstanding": outstanding,
            "overdue": overdue,
        }
