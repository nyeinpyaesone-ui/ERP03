from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from app.core.database import Base

class AccountType(str, Enum):
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    REVENUE = "revenue"
    EXPENSE = "expense"

class Account(Base):
    __tablename__ = "finance_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    account_type = Column(SQLEnum(AccountType), nullable=False)
    parent_id = Column(Integer, ForeignKey("finance_accounts.id"))
    balance = Column(Numeric(15, 2), default=0.00)
    currency = Column(String(3), default="USD")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    parent = relationship("Account", remote_side=[id], backref="children")
    journal_entries = relationship("JournalEntry", back_populates="account")

class JournalEntry(Base):
    __tablename__ = "finance_journal_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    entry_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    description = Column(Text)
    reference = Column(String(100))
    posted = Column(Boolean, default=False)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    lines = relationship("JournalLine", back_populates="entry", cascade="all, delete-orphan")
    account = relationship("Account", back_populates="journal_entries")

class JournalLine(Base):
    __tablename__ = "finance_journal_lines"
    
    id = Column(Integer, primary_key=True, index=True)
    entry_id = Column(Integer, ForeignKey("finance_journal_entries.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("finance_accounts.id"), nullable=False)
    debit = Column(Numeric(15, 2), default=0.00)
    credit = Column(Numeric(15, 2), default=0.00)
    description = Column(String(255))
    
    # Relationships
    entry = relationship("JournalEntry", back_populates="lines")
    account = relationship("Account")

class Invoice(Base):
    __tablename__ = "finance_invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(50), unique=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("crm_companies.id"))
    issue_date = Column(DateTime, nullable=False)
    due_date = Column(DateTime, nullable=False)
    subtotal = Column(Numeric(15, 2), default=0.00)
    tax_amount = Column(Numeric(15, 2), default=0.00)
    total_amount = Column(Numeric(15, 2), default=0.00)
    amount_paid = Column(Numeric(15, 2), default=0.00)
    status = Column(String(20), default="draft")  # draft, posted, paid, overdue, cancelled
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    lines = relationship("InvoiceLine", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="invoice")

class InvoiceLine(Base):
    __tablename__ = "finance_invoice_lines"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("finance_invoices.id"), nullable=False)
    description = Column(String(255), nullable=False)
    quantity = Column(Numeric(10, 2), default=1.00)
    unit_price = Column(Numeric(15, 2), nullable=False)
    tax_rate = Column(Numeric(5, 2), default=0.00)
    line_total = Column(Numeric(15, 2))
    
    invoice = relationship("Invoice", back_populates="lines")

class Payment(Base):
    __tablename__ = "finance_payments"
    
    id = Column(Integer, primary_key=True, index=True)
    payment_number = Column(String(50), unique=True, nullable=False)
    invoice_id = Column(Integer, ForeignKey("finance_invoices.id"))
    payment_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    amount = Column(Numeric(15, 2), nullable=False)
    payment_method = Column(String(50))  # cash, bank_transfer, credit_card, etc.
    reference = Column(String(100))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    invoice = relationship("Invoice", back_populates="payments")
