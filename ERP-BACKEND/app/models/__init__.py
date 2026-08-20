"""ERP Solution SQLAlchemy models.

This package contains all database models organized by domain:
- user: User authentication and profile
- crm: Company, Contact, Deal (Customer Relationship Management)
- inventory: Product, InventoryMovement
- finance: Invoice, InvoiceItem, Payment
- project: Project, Task
- hr: Department, Employee
- workflow: Document, Workflow, WorkflowStep, WorkflowExecution, Webhook, WebhookDelivery, Integration
- system: ActivityLog, Notification, Report, Forecast, Setting
- search: SearchIndex, SearchQuery, SearchSuggestion
"""

from app.models.user import User
from app.models.crm import Company, Contact, Deal
from app.models.inventory import Product, InventoryMovement
from app.models.finance import Invoice, InvoiceItem, Payment
from app.models.project import Project, Task
from app.models.hr import Department, Employee
from app.models.workflow import (
    Document,
    Workflow,
    WorkflowStep,
    WorkflowExecution,
    Webhook,
    WebhookDelivery,
    Integration,
)
from app.models.system import ActivityLog, Notification, Report, Forecast, Setting
from app.models.search import SearchIndex, SearchQuery, SearchSuggestion

# Export all models for backward compatibility
__all__ = [
    # User
    "User",
    # CRM
    "Company",
    "Contact",
    "Deal",
    # Inventory
    "Product",
    "InventoryMovement",
    # Finance
    "Invoice",
    "InvoiceItem",
    "Payment",
    # Project
    "Project",
    "Task",
    # HR
    "Department",
    "Employee",
    # Workflow & Integration
    "Document",
    "Workflow",
    "WorkflowStep",
    "WorkflowExecution",
    "Webhook",
    "WebhookDelivery",
    "Integration",
    # System
    "ActivityLog",
    "Notification",
    "Report",
    "Forecast",
    "Setting",
    # Search
    "SearchIndex",
    "SearchQuery",
    "SearchSuggestion",
]
