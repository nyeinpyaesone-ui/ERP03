"""
Regulated Manufacturing Inventory Models (GMP/FDA 21 CFR Part 11 Compliant)

Implements:
- ERP_ItemMaster: Core item definition with batch/serial tracking flags
- ERP_InventoryDimension: Normalized storage/batch/serial dimensions
- ERP_InventoryTransaction: Immutable ledger for all stock movements
- EBMR_BatchRecord: Electronic Batch Manufacturing Record for traceability
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import (
    Column, String, Integer, Numeric, DateTime, Date, Boolean,
    ForeignKey, UniqueConstraint, Index, Text
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.database import Base


class ERPItemMaster(Base):
    """
    Core Item Master Table
    Defines materials, raw materials, finished goods with tracking requirements.
    """
    __tablename__ = "ERP_ItemMaster"

    ItemId: Mapped[str] = mapped_column(String(50), primary_key=True)
    ItemName: Mapped[str] = mapped_column(String(150), nullable=False)
    ItemType: Mapped[str] = mapped_column(String(30), nullable=False)  # RawMaterial, FinishedGood, Packaging
    BaseUnitOfMeasure: Mapped[str] = mapped_column(String(10), nullable=False)
    ValuationMethod: Mapped[str] = mapped_column(String(20), nullable=False)  # StandardCost, FIFO, WeightedAvg
    IsBatchTracked: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    IsSerialized: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    CreatedDateTime: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    transactions: Mapped[List["ERPInventoryTransaction"]] = relationship(back_populates="ItemMaster")
    batch_records: Mapped[List["EBMRBatchRecord"]] = relationship(back_populates="ProductMaster")


class ERPInventoryDimension(Base):
    """
    Inventory Dimension Hash Table
    Normalizes Site/Warehouse/Location/Batch/Serial combinations.
    InventDimId is a GUID/MD5 hash of the dimension values.
    """
    __tablename__ = "ERP_InventoryDimension"

    InventDimId: Mapped[str] = mapped_column(String(36), primary_key=True)
    SiteId: Mapped[str] = mapped_column(String(20), nullable=False)
    WarehouseId: Mapped[str] = mapped_column(String(20), nullable=False)
    LocationId: Mapped[str] = mapped_column(String(20), nullable=False)
    BatchId: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    SerialNumber: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Relationships
    transactions: Mapped[List["ERPInventoryTransaction"]] = relationship(back_populates="InventoryDimension")

    __table_args__ = (
        Index('idx_dim_site_warehouse', 'SiteId', 'WarehouseId'),
        Index('idx_dim_batch', 'BatchId'),
    )


class ERPInventoryTransaction(Base):
    """
    Immutable Inventory Transactions Ledger (InventTrans Equivalent)
    Records every physical and financial stock movement.
    StatusReceipt: 0=None, 1=Registered, 2=Received, 3=Purchased
    StatusIssue: 0=None, 1=OnOrder, 2=ReservedPhysical, 3=Deducted, 4=Sold
    """
    __tablename__ = "ERP_InventoryTransaction"

    TransactionId: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ItemId: Mapped[str] = mapped_column(String(50), ForeignKey("ERP_ItemMaster.ItemId"), nullable=False)
    InventDimId: Mapped[str] = mapped_column(String(36), ForeignKey("ERP_InventoryDimension.InventDimId"), nullable=False)

    ReferenceCategory: Mapped[str] = mapped_column(String(30), nullable=False)  # PurchaseOrder, ProductionLine, SalesOrder
    ReferenceId: Mapped[str] = mapped_column(String(50), nullable=False)

    Quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    StatusReceipt: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    StatusIssue: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    DatePhysical: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    DateFinancial: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    CostAmountPhysical: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0.0000, nullable=False)
    CostAmountPosted: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0.0000, nullable=False)

    DataAreaId: Mapped[str] = mapped_column(String(4), nullable=False)  # Company/Legal Entity
    SysRowVersion: Mapped[bytes] = mapped_column(type_=String(50))  # RowVersion for concurrency

    # Relationships
    ItemMaster: Mapped["ERPItemMaster"] = relationship(back_populates="transactions")
    InventoryDimension: Mapped["ERPInventoryDimension"] = relationship(back_populates="transactions")

    __table_args__ = (
        Index('idx_trans_item_date', 'ItemId', 'DatePhysical'),
        Index('idx_trans_reference', 'ReferenceCategory', 'ReferenceId'),
    )


class EBMRBatchRecord(Base):
    """
    Electronic Batch Manufacturing Record (EBMR)
    Captures full genealogy from sourcing to production execution.
    Compliant with FDA cGMP and ISO 22000.
    """
    __tablename__ = "EBMR_BatchRecord"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    batchId: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    masterBatchRecordVersion: Mapped[str] = mapped_column(String(20), nullable=False)
    productId: Mapped[str] = mapped_column(String(50), ForeignKey("ERP_ItemMaster.ItemId"), nullable=False)
    productionOrderNumber: Mapped[str] = mapped_column(String(50), nullable=False)
    facilitySiteId: Mapped[str] = mapped_column(String(20), nullable=False)
    complianceFramework: Mapped[str] = mapped_column(String(30), default="FDA_cGMP_ISO22000", nullable=False)

    # JSON blobs for complex nested structures (sourcing & production log)
    sourcingAndProcurement: Mapped[dict] = mapped_column(type_=Text)  # Stored as JSON string
    productionExecutionLog: Mapped[dict] = mapped_column(type_=Text)  # Stored as JSON string

    CreatedDateTime: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    LastModifiedDateTime: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    ProductMaster: Mapped["ERPItemMaster"] = relationship(back_populates="batch_records")
