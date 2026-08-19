# App Models Package
from app.models.regulated_inventory import (
    ERP_ItemMaster,
    ERP_InventoryDimension,
    ERP_InventoryTransaction,
    EBMR_BatchRecord
)

# Import legacy models from models_legacy.py for backward compatibility
from app.models_legacy import (
    User,
    Company,
    Contact,
    Deal,
    Project,
    Task,
    Notification,
    ActivityLog,
    Document,
    SearchIndex,
    Employee,
    Department,
    Product,
    InventoryMovement,
    Invoice,
    InvoiceItem,
    Payment,
    Forecast,
    Report,
    Setting,
    Integration,
    Webhook,
    WebhookDelivery,
    Workflow,
    WorkflowExecution,
    WorkflowStep,
    SearchQuery,
    SearchSuggestion
)

__all__ = [
    # Regulated Inventory (GMP/FDA Compliant)
    "ERP_ItemMaster",
    "ERP_InventoryDimension",
    "ERP_InventoryTransaction",
    "EBMR_BatchRecord",
    # Legacy CRM/ERP Models
    "User",
    "Company",
    "Contact",
    "Deal",
    "Project",
    "Task",
    "Notification",
    "ActivityLog",
    "Document",
    "SearchIndex",
    "Employee",
    "Department",
    "Product",
    "InventoryMovement",
    "Invoice",
    "InvoiceItem",
    "Payment",
    "Forecast",
    "Report",
    "Setting",
    "Integration",
    "Webhook",
    "WebhookDelivery",
    "Workflow",
    "WorkflowExecution",
    "WorkflowStep",
    "SearchQuery",
    "SearchSuggestion"
]
