# Regulated Manufacturing Inventory Module

## Overview
Production-grade inventory management system compliant with **FDA 21 CFR Part 11**, **GMP (Good Manufacturing Practice)**, and **ISO 22000** standards for regulated manufacturing environments.

## Standards Compliance
- **FDA 21 CFR Part 11**: Electronic records and signatures
- **GMP (cGMP)**: Current Good Manufacturing Practice
- **ISO 22000**: Food safety management
- **APICS SCOR**: Supply chain operations reference
- **ISA-95**: Enterprise-control system integration

## Architecture

### Data Models (`app/models/regulated_inventory.py`)

| Table | Purpose | Key Fields |
| :--- | :--- | :--- |
| `ERP_ItemMaster` | Core item definition | ItemId, ItemType, IsBatchTracked, ValuationMethod |
| `ERP_InventoryDimension` | Normalized storage dimensions | InventDimId (hash), SiteId, WarehouseId, BatchId |
| `ERP_InventoryTransaction` | Immutable movement ledger | TransactionId, StatusReceipt, StatusIssue, CostAmount |
| `EBMR_BatchRecord` | Electronic batch record | batchId, sourcingAndProcurement (JSON), productionExecutionLog (JSON) |

### Service Layer (`app/services/regulated_inventory_service.py`)

#### Core Operations
- `register_item_master()` - Create new item in master data
- `process_goods_receipt()` - Inbound logistics (GRN)
- `process_goods_issue()` - Outbound consumption/shipment
- `allocate_inventory_fefo()` - First-Expired-First-Out allocation
- `release_quality_hold()` - Quality release sign-off

#### EBMR & Traceability
- `create_ebmr_batch_record()` - Create electronic batch record
- `generate_genealogy_report()` - Full upstream/downstream traceability
- `get_stock_by_batch()` - Query inventory by batch
- `query_near_expiry_lots()` - Expiry alerts

## Usage Examples

### Register Raw Material
```python
from app.services.regulated_inventory_service import RegulatedInventoryService

service = RegulatedInventoryService(db_session)

# Register API active ingredient
item = service.register_item_master(
    item_id="RM-API-5510",
    item_name="Active Pharmaceutical Ingredient X",
    item_type="RawMaterial",
    base_uom="KG",
    valuation_method="FIFO",
    is_batch_tracked=True
)
```

### Process Goods Receipt
```python
from decimal import Decimal

transaction = service.process_goods_receipt(
    item_id="RM-API-5510",
    quantity=Decimal("250.00"),
    site_id="SITE-EU-01",
    warehouse_id="WH-RM-01",
    location_id="LOC-A-001",
    batch_id="LOT-SUP-98214",
    reference_document_id="GRN-2026-004812",
    supplier_id="SUP-BIOMED-GLOBAL",
    cost_amount=Decimal("12500.00")
)
```

### Create EBMR Record
```python
ebmr = service.create_ebmr_batch_record(
    batch_id="BATCH-REG-2026-0817-099X",
    product_id="SKU-PHARMA-99201",
    production_order_number="PO-PROD-778392",
    facility_site_id="SITE-EU-01",
    master_batch_record_version="MBR-REV-4.2",
    sourcing_and_procurement=[
        {
            "materialId": "RM-API-5510",
            "supplierId": "SUP-BIOMED-GLOBAL",
            "supplierLotNumber": "LOT-SUP-98214",
            "erpReceiptDocumentId": "GRN-2026-004812",
            "certificateOfAnalysisId": "COA-2026-991",
            "quantityDispensed": 250.00,
            "unitOfMeasure": "KG"
        }
    ],
    production_execution_log=[
        {
            "stepId": "STEP-01",
            "operationName": "Weighing and Dispensing",
            "timestamp": "2026-08-17T06:30:00Z",
            "criticalProcessParameters": {
                "temperatureCelsius": 21.5,
                "pressureBar": 1.02
            },
            "operatorId": "OP-8821",
            "supervisorSignOffId": "SUPV-104",
            "deviationLogged": False
        }
    ]
)
```

### Generate Genealogy Report
```python
report = service.generate_genealogy_report(batch_id="BATCH-REG-2026-0817-099X")

# Returns full traceability:
# - Upstream: raw materials, suppliers, CoA references
# - Downstream: production steps, operators, CPP data
# - Compliance: FDA/ISO status, electronic signatures
```

## Database Migration

Add to Alembic migration script:
```python
def upgrade():
    op.create_table('ERP_ItemMaster',
        sa.Column('ItemId', sa.String(50), nullable=False),
        sa.Column('ItemName', sa.String(150), nullable=False),
        # ... additional columns
        sa.PrimaryKeyConstraint('ItemId')
    )
    
    op.create_table('ERP_InventoryDimension',
        sa.Column('InventDimId', sa.String(36), nullable=False),
        # ... additional columns
        sa.PrimaryKeyConstraint('InventDimId')
    )
    
    op.create_table('ERP_InventoryTransaction',
        sa.Column('TransactionId', sa.Integer, autoincrement=True, nullable=False),
        # ... additional columns
        sa.PrimaryKeyConstraint('TransactionId')
    )
    
    op.create_table('EBMR_BatchRecord',
        sa.Column('id', sa.Integer, autoincrement=True, nullable=False),
        # ... additional columns
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('batchId')
    )

def downgrade():
    op.drop_table('EBMR_BatchRecord')
    op.drop_table('ERP_InventoryTransaction')
    op.drop_table('ERP_InventoryDimension')
    op.drop_table('ERP_ItemMaster')
```

## Key Features

### 1. Immutable Transaction Ledger
Every stock movement recorded with:
- StatusReceipt (0=None, 1=Registered, 2=Received, 3=Purchased)
- StatusIssue (0=None, 1=OnOrder, 2=Reserved, 3=Deducted, 4=Sold)
- DatePhysical / DateFinancial separation
- Cost tracking (Physical vs Posted)

### 2. FEFO Allocation
Automatic First-Expired-First-Out allocation for perishable goods:
- Minimizes waste due to expiry
- Compliant with pharma/food regulations
- Configurable exclusion lists (quarantined batches)

### 3. Electronic Batch Records (EBMR)
Complete digital thread from sourcing to shipment:
- Raw material genealogy with supplier lot numbers
- Certificate of Analysis (CoA) tracking
- Production step execution with timestamps
- Critical Process Parameters (CPP) logging
- Operator and supervisor electronic signatures

### 4. Regulatory Compliance
- **21 CFR Part 11**: Electronic signatures, audit trails
- **GMP**: Quality holds, batch release workflows
- **ISO 22000**: Hazard analysis, traceability
- **Audit Ready**: Instant genealogy reports for recalls

## Testing

```bash
cd ERP-BACKEND
pytest tests/test_regulated_inventory.py -v --cov=app/services/regulated_inventory_service
```

## Next Steps
1. Create API router endpoints (`routers/regulated_inventory.py`)
2. Implement Pydantic schemas for request/response validation
3. Write integration tests for FEFO and EBMR workflows
4. Create Alembic migration for database tables
5. Integrate with Quality Management module for release workflows
