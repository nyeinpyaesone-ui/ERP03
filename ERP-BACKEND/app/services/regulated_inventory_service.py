"""
Regulated Inventory Service Implementation
Handles GMP/FDA compliant inventory operations with full traceability.
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
from typing import List, Optional
from app.models.regulated_inventory import (
    ERP_ItemMaster, 
    ERP_InventoryDimension, 
    ERP_InventoryTransaction,
    EBMR_BatchRecord
)

class RegulatedInventoryService:
    """Service layer for regulated inventory operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_item(self, item_code: str, description: str, 
                   is_batch_managed: bool = False, 
                   is_serial_managed: bool = False,
                   is_expiry_tracked: bool = False) -> ERP_ItemMaster:
        """Create a new item master record."""
        item = ERP_ItemMaster(
            item_code=item_code,
            description=description,
            is_batch_managed=is_batch_managed,
            is_serial_managed=is_serial_managed,
            is_expiry_tracked=is_expiry_tracked
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item
    
    def add_inventory(self, item_id: int, warehouse_code: str, 
                     quantity: float, batch_number: Optional[str] = None,
                     serial_number: Optional[str] = None,
                     expiry_date: Optional[datetime] = None,
                     reference_document: str = "",
                     performed_by: str = "") -> ERP_InventoryDimension:
        """Add inventory receipt with full traceability."""
        # Create or find dimension
        dimension = self.db.query(ERP_InventoryDimension).filter(
            and_(
                ERP_InventoryDimension.item_id == item_id,
                ERP_InventoryDimension.warehouse_code == warehouse_code,
                ERP_InventoryDimension.batch_number == batch_number,
                ERP_InventoryDimension.serial_number == serial_number
            )
        ).first()
        
        if not dimension:
            dimension = ERP_InventoryDimension(
                item_id=item_id,
                warehouse_code=warehouse_code,
                batch_number=batch_number,
                serial_number=serial_number,
                expiry_date=expiry_date,
                quantity_on_hand=0,
                quantity_reserved=0
            )
            self.db.add(dimension)
            self.db.flush()
        
        # Update quantity
        dimension.quantity_on_hand += quantity
        
        # Create immutable transaction record
        transaction = ERP_InventoryTransaction(
            item_id=item_id,
            dimension_id=dimension.id,
            transaction_type="RECEIPT",
            quantity=quantity,
            reference_document=reference_document,
            performed_by=performed_by
        )
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(dimension)
        return dimension
    
    def issue_inventory(self, dimension_id: int, quantity: float,
                       reference_document: str, performed_by: str) -> ERP_InventoryTransaction:
        """Issue inventory from stock with audit trail."""
        dimension = self.db.query(ERP_InventoryDimension).filter(
            ERP_InventoryDimension.id == dimension_id
        ).first()
        
        if not dimension:
            raise ValueError(f"Dimension {dimension_id} not found")
        
        if dimension.quantity_on_hand < quantity:
            raise ValueError(f"Insufficient stock. Available: {dimension.quantity_on_hand}")
        
        # Update quantity
        dimension.quantity_on_hand -= quantity
        
        # Create immutable transaction record
        transaction = ERP_InventoryTransaction(
            item_id=dimension.item_id,
            dimension_id=dimension_id,
            transaction_type="ISSUE",
            quantity=-quantity,  # Negative for issues
            reference_document=reference_document,
            performed_by=performed_by
        )
        self.db.add(transaction)
        self.db.commit()
        return transaction
    
    def get_inventory_status(self, item_id: int, warehouse_code: str) -> dict:
        """Get current inventory status for an item in a warehouse."""
        dimensions = self.db.query(ERP_InventoryDimension).filter(
            and_(
                ERP_InventoryDimension.item_id == item_id,
                ERP_InventoryDimension.warehouse_code == warehouse_code
            )
        ).all()
        
        total_on_hand = sum(d.quantity_on_hand for d in dimensions)
        total_reserved = sum(d.quantity_reserved for d in dimensions)
        
        return {
            "item_id": item_id,
            "warehouse_code": warehouse_code,
            "total_on_hand": total_on_hand,
            "total_reserved": total_reserved,
            "available": total_on_hand - total_reserved,
            "batches": [
                {
                    "batch_number": d.batch_number,
                    "quantity": d.quantity_on_hand,
                    "expiry_date": d.expiry_date
                }
                for d in dimensions if d.batch_number
            ]
        }
    
    def create_batch_record(self, batch_number: str, item_id: int, 
                           production_order: str) -> EBMR_BatchRecord:
        """Create Electronic Batch Manufacturing Record."""
        record = EBMR_BatchRecord(
            batch_number=batch_number,
            item_id=item_id,
            production_order=production_order,
            start_date=datetime.utcnow(),
            status="IN_PROGRESS"
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record
    
    def complete_batch_record(self, batch_number: str, qa_user: str, 
                             qa_status: str, qa_comments: str = "") -> EBMR_BatchRecord:
        """Complete and QA approve/reject a batch record."""
        record = self.db.query(EBMR_BatchRecord).filter(
            EBMR_BatchRecord.batch_number == batch_number
        ).first()
        
        if not record:
            raise ValueError(f"Batch record {batch_number} not found")
        
        record.end_date = datetime.utcnow()
        record.status = "COMPLETED"
        record.qa_status = qa_status
        record.qa_user = qa_user
        record.qa_comments = qa_comments
        
        self.db.commit()
        self.db.refresh(record)
        return record
