"""CRM models: Company, Contact, Deal."""
from sqlalchemy import Column, Integer, String, Text, Numeric, ForeignKey, DateTime, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    industry = Column(String(100), nullable=True)
    size = Column(String(50), nullable=True)
    website = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    phone = Column(String(50), nullable=True)
    logo_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    contacts = relationship("Contact", back_populates="company")
    deals = relationship("Deal", back_populates="company")
    invoices = relationship("Invoice", back_populates="company")


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), index=True, nullable=True)
    phone = Column(String(50), nullable=True)
    title = Column(String(100), nullable=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(50), nullable=False, server_default="lead")
    source = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    assigned_to = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    lifetime_value = Column(Numeric(15, 2), nullable=False, server_default="0")
    last_activity = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    company = relationship("Company", back_populates="contacts")
    assigned_user = relationship("User", back_populates="contacts", foreign_keys=[assigned_to])
    deals = relationship("Deal", back_populates="contact")
    invoices = relationship("Invoice", back_populates="contact")


class Deal(Base):
    __tablename__ = "deals"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    contact_id = Column(Integer, ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="SET NULL"), nullable=True)
    value = Column(Numeric(15, 2), nullable=False, server_default="0")
    stage = Column(String(50), nullable=False, server_default="prospect")
    probability = Column(Integer, nullable=False, server_default="0")
    expected_close_date = Column(Date, nullable=True)
    actual_close_date = Column(Date, nullable=True)
    assigned_to = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    contact = relationship("Contact", back_populates="deals")
    company = relationship("Company", back_populates="deals")
    assigned_user = relationship("User", back_populates="deals", foreign_keys=[assigned_to])
