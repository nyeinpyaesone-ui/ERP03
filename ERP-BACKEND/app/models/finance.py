"""Finance & Accounting Models"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Date, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.base import TimestampMixin


class Invoice(Base, TimestampMixin):
    """Customer invoices"""
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(100), unique=True, nullable=False)
    contact_id = Column(Integer, ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="SET NULL"), nullable=True)
    issue_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    subtotal = Column(Numeric(15, 2), nullable=False, server_default="0")
    tax_rate = Column(Numeric(5, 2), nullable=False, server_default="0")
    tax_amount = Column(Numeric(15, 2), nullable=False, server_default="0")
    total = Column(Numeric(15, 2), nullable=False, server_default="0")
    amount_paid = Column(Numeric(15, 2), nullable=False, server_default="0")
    status = Column(String(50), nullable=False, server_default="draft")
    notes = Column(Text, nullable=True)
    terms = Column(Text, nullable=True)
    stripe_payment_intent_id = Column(String(255), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    contact = relationship("Contact", back_populates="invoices")
    company = relationship("Company", back_populates="invoices")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="invoice", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Invoice(id={self.id}, number='{self.invoice_number}', total={self.total})>"


class InvoiceItem(Base):
    """Line items for invoices"""
    __tablename__ = "invoice_items"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    description = Column(Text, nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)
    unit_price = Column(Numeric(15, 2), nullable=False)
    total = Column(Numeric(15, 2), nullable=False)

    invoice = relationship("Invoice", back_populates="items")
    product = relationship("Product", back_populates="invoice_items")

    def __repr__(self):
        return f"<InvoiceItem(id={self.id}, invoice_id={self.invoice_id}, total={self.total})>"


class Payment(Base, TimestampMixin):
    """Payment records for invoices"""
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    payment_method = Column(String(50), nullable=False)
    payment_date = Column(Date, nullable=False)
    stripe_payment_intent_id = Column(String(255), nullable=True)
    stripe_charge_id = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False, server_default="completed")
    notes = Column(Text, nullable=True)

    invoice = relationship("Invoice", back_populates="payments")

    def __repr__(self):
        return f"<Payment(id={self.id}, invoice_id={self.invoice_id}, amount={self.amount})>"


class Expense(Base, TimestampMixin):
    """Expense tracking"""
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(100), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    description = Column(Text, nullable=False)
    expense_date = Column(Date, nullable=False)
    vendor = Column(String(255), nullable=True)
    receipt_url = Column(String(500), nullable=True)
    status = Column(String(50), nullable=False, server_default="pending")  # pending, approved, reimbursed
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="SET NULL"), nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    employee = relationship("Employee")
    approver = relationship("User", foreign_keys=[approved_by])

    def __repr__(self):
        return f"<Expense(id={self.id}, category='{self.category}', amount={self.amount})>"


class Account(Base, TimestampMixin):
    """Chart of accounts for accounting"""
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    account_code = Column(String(50), unique=True, nullable=False)
    account_name = Column(String(255), nullable=False)
    account_type = Column(String(50), nullable=False)  # asset, liability, equity, revenue, expense
    parent_account_id = Column(Integer, ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)
    balance = Column(Numeric(15, 2), nullable=False, server_default="0")
    currency = Column(String(3), nullable=False, server_default="USD")
    is_active = Column(Boolean, nullable=False, server_default="true")

    parent = relationship("Account", remote_side=[parent_account_id], backref="children")

    def __repr__(self):
        return f"<Account(id={self.id}, code='{self.account_code}', name='{self.account_name}')>"


class JournalEntry(Base, TimestampMixin):
    """General journal entries for double-entry bookkeeping"""
    __tablename__ = "journal_entries"

    id = Column(Integer, primary_key=True, index=True)
    entry_date = Column(Date, nullable=False)
    description = Column(Text, nullable=False)
    reference = Column(String(100), nullable=True)
    posted = Column(Boolean, nullable=False, server_default="false")
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    creator = relationship("User")
    lines = relationship("JournalEntryLine", back_populates="entry", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<JournalEntry(id={self.id}, date={self.entry_date}, posted={self.posted})>"


class JournalEntryLine(Base):
    """Lines for journal entries (debits and credits)"""
    __tablename__ = "journal_entry_lines"

    id = Column(Integer, primary_key=True, index=True)
    entry_id = Column(Integer, ForeignKey("journal_entries.id", ondelete="CASCADE"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="RESTRICT"), nullable=False)
    debit = Column(Numeric(15, 2), nullable=False, server_default="0")
    credit = Column(Numeric(15, 2), nullable=False, server_default="0")
    description = Column(Text, nullable=True)

    entry = relationship("JournalEntry", back_populates="lines")
    account = relationship("Account")

    def __repr__(self):
        return f"<JournalEntryLine(id={self.id}, entry_id={self.entry_id}, debit={self.debit}, credit={self.credit})>"


class TaxRate(Base, TimestampMixin):
    """Tax rate definitions"""
    __tablename__ = "tax_rates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    rate = Column(Numeric(5, 2), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, server_default="true")
    tax_type = Column(String(50), nullable=False, server_default="sales")  # sales, purchase, use

    def __repr__(self):
        return f"<TaxRate(id={self.id}, name='{self.name}', rate={self.rate}%)>"
