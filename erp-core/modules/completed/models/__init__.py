# App Models Package - Centralized model imports

# Import domain models from refactored model files
from app.models.user import User
from app.models.crm import Company, Contact, Deal
from app.models.hr import Department, Employee
from app.models.inventory import Product, InventoryMovement
from app.models.finance import Invoice, InvoiceItem, Payment
from app.models.project import Project, Task
from app.models.system import ActivityLog, Notification, Report, Forecast, Setting
from app.models.search import SearchIndex, SearchQuery, SearchSuggestion
from app.models.workflow import (
    Document,
    Workflow,
    WorkflowStep,
    WorkflowExecution,
    Webhook,
    WebhookDelivery,
    Integration
)
from app.models.permissions import (
    Role,
    Permission,
    RolePermission,
    UserRole,
    FieldPermission,
    DataPolicy
)

# Import regulated inventory models (GMP/FDA 21 CFR Part 11 compliant)
from app.models.regulated_inventory import (
    ERPItemMaster,
    ERPInventoryDimension,
    ERPInventoryTransaction,
    EBMRBatchRecord
)

__all__ = [
    # User Management
    "User",
    # CRM Models
    "Company",
    "Contact",
    "Deal",
    # HR Models
    "Department",
    "Employee",
    # Inventory Models
    "Product",
    "InventoryMovement",
    # Finance Models
    "Invoice",
    "InvoiceItem",
    "Payment",
    # Project Management
    "Project",
    "Task",
    # System Models
    "ActivityLog",
    "Notification",
    "Report",
    "Forecast",
    "Setting",
    # Search Models
    "SearchIndex",
    "SearchQuery",
    "SearchSuggestion",
    # Workflow Models
    "Document",
    "Workflow",
    "WorkflowStep",
    "WorkflowExecution",
    "Webhook",
    "WebhookDelivery",
    "Integration",
    # Permission Models
    "Role",
    "Permission",
    "RolePermission",
    "UserRole",
    "FieldPermission",
    "DataPolicy",
    # Regulated Inventory (GMP/FDA Compliant)
    "ERPItemMaster",
    "ERPInventoryDimension",
    "ERPInventoryTransaction",
    "EBMRBatchRecord",
]
