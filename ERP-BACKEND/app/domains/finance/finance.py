"""Finance models: Invoice, InvoiceItem, Payment."""
from sqlalchemy import Column, Integer, String, Text, Numeric, ForeignKey, DateTime, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Invoice(Base):
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
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    contact = relationship("Contact", back_populates="invoices")
    company = relationship("Company", back_populates="invoices")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="invoice", cascade="all, delete-orphan")


class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    description = Column(Text, nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)
    unit_price = Column(Numeric(15, 2), nullable=False)
    total = Column(Numeric(15, 2), nullable=False)

    # Relationships
    invoice = relationship("Invoice", back_populates="items")
    product = relationship("Product", back_populates="invoice_items")


class Payment(Base):
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
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    invoice = relationship("Invoice", back_populates="payments")
