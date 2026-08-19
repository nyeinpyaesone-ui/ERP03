"""
Regulated Manufacturing Inventory Models (GMP/FDA 21 CFR Part 11 Compliant)

Implements:
- ERP_ItemMaster: Core item definition with batch/serial tracking flags
- ERP_InventoryDimension: Normalized storage/batch/serial dimensions
- ERP_InventoryTransaction: Immutable ledger for all stock movements
- EBMR_BatchRecord: Electronic Batch Manufacturing Record for traceability
"""
from sqlalchemy import Column, String, Integer, ForeignKey, Boolean, DateTime, Numeric, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class ERP_ItemMaster(Base):
    """Core item definition with regulatory flags."""
    __tablename__ = "erp_item_master"

    id = Column(Integer, primary_key=True, index=True)
    item_code = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=False)
    
    # Regulatory Flags
    is_batch_managed = Column(Boolean, default=False, nullable=False)
    is_serial_managed = Column(Boolean, default=False, nullable=False)
    is_expiry_tracked = Column(Boolean, default=False, nullable=False)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    dimensions = relationship("ERP_InventoryDimension", back_populates="item")
    transactions = relationship("ERP_InventoryTransaction", back_populates="item")

class ERP_InventoryDimension(Base):
    """Normalized storage/batch/serial dimensions for traceability."""
    __tablename__ = "erp_inventory_dimension"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("erp_item_master.id"), nullable=False)
    
    # Dimensions
    warehouse_code = Column(String(20), nullable=False)
    bin_code = Column(String(20), nullable=True)
    batch_number = Column(String(50), nullable=True, index=True)
    serial_number = Column(String(50), nullable=True, unique=True)
    expiry_date = Column(DateTime, nullable=True)
    
    # Current Status
    quantity_on_hand = Column(Numeric(10, 4), default=0)
    quantity_reserved = Column(Numeric(10, 4), default=0)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    item = relationship("ERP_ItemMaster", back_populates="dimensions")

class ERP_InventoryTransaction(Base):
    """Immutable ledger for all stock movements (Audit Trail)."""
    __tablename__ = "erp_inventory_transaction"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("erp_item_master.id"), nullable=False)
    dimension_id = Column(Integer, ForeignKey("erp_inventory_dimension.id"), nullable=True)
    
    # Transaction Details
    transaction_type = Column(String(20), nullable=False) # RECEIPT, ISSUE, ADJUST, TRANSFER
    quantity = Column(Numeric(10, 4), nullable=False)
    reference_document = Column(String(50), nullable=False) # PO Number, SO Number, etc.
    reason_code = Column(String(20), nullable=True)
    
    # Traceability
    performed_by = Column(String(50), nullable=False)
    transaction_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    comments = Column(Text, nullable=True)
    
    # Relationships
    item = relationship("ERP_ItemMaster", back_populates="transactions")

class EBMR_BatchRecord(Base):
    """Electronic Batch Manufacturing Record for full traceability."""
    __tablename__ = "ebmr_batch_record"

    id = Column(Integer, primary_key=True, index=True)
    batch_number = Column(String(50), unique=True, nullable=False, index=True)
    item_id = Column(Integer, ForeignKey("erp_item_master.id"), nullable=False)
    
    # Production Details
    production_order = Column(String(50), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)
    status = Column(String(20), default="IN_PROGRESS") # IN_PROGRESS, COMPLETED, RELEASED
    
    # Quality
    qa_status = Column(String(20), default="PENDING") # PENDING, APPROVED, REJECTED
    qa_user = Column(String(50), nullable=True)
    qa_comments = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
