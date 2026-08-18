from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass
class InvoiceLine:
    description: str
    quantity: float
    unit_price: float

    @property
    def line_total(self) -> float:
        return self.quantity * self.unit_price


@dataclass
class InvoiceTotals:
    subtotal: float
    tax_amount: float
    total: float


def calculate_invoice_totals(lines: list[InvoiceLine], tax_rate: float) -> InvoiceTotals:
    if tax_rate < 0:
        raise ValueError("tax_rate cannot be negative")
    subtotal = sum(line.line_total for line in lines)
    tax_amount = subtotal * (tax_rate / 100)
    return InvoiceTotals(subtotal=subtotal, tax_amount=tax_amount, total=subtotal + tax_amount)


def is_overdue(due_date: date, status: str, *, today: date) -> bool:
    return status != "paid" and due_date < today


def validate_payment(amount: float, invoice_total: float, amount_already_paid: float) -> None:
    if amount <= 0:
        raise ValueError("Payment amount must be positive")
    if amount_already_paid + amount > invoice_total + 1e-6:
        raise ValueError("Payment would exceed invoice total")
