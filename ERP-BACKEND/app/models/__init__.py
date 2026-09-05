"""ERP erp03 SQLAlchemy models.

This package contains all database models organized by domain:
- user: User authentication and profile
- crm: Company, Contact, Deal (Customer Relationship Management)
- inventory: Product, InventoryMovement, StockAdjustment, Warehouse, WarehouseStock
- finance: Invoice, InvoiceItem, Payment, Expense, Account, JournalEntry, JournalEntryLine, TaxRate
- project: Project, Task, TimeEntry, ProjectMilestone, ProjectDocument
- hr: Department, Employee, LeaveRequest, LeaveBalance, Attendance, PerformanceReview, Payroll
- workflow: Document, Workflow, WorkflowStep, WorkflowExecution, Webhook, WebhookDelivery, Integration
- system: ActivityLog, Notification, Report, Forecast, Setting
- search: SearchIndex, SearchQuery, SearchSuggestion
- permissions: Role, Permission, RolePermission, UserRole, FieldPermission, DataPolicy
"""

from app.models.base import Base, TimestampMixin, SoftDeleteMixin
from app.models.user import User
from app.models.crm import Company, Contact, Deal
from app.models.inventory import Product, InventoryMovement, StockAdjustment, Warehouse, WarehouseStock
from app.models.finance import Invoice, InvoiceItem, Payment, Expense, Account, JournalEntry, JournalEntryLine, TaxRate
from app.models.project import Project, Task
from app.models.hr import Department, Employee, LeaveRequest, LeaveBalance, Attendance, PerformanceReview, Payroll
from app.models.workflow import (
    Document,
    Workflow,
    WorkflowStep,
    WorkflowExecution,
    Webhook,
    WebhookDelivery,
    Integration,
)
from app.models.permissions import Role, Permission, RolePermission, UserRole, FieldPermission, DataPolicy
from app.models.system import ActivityLog, Notification, Report, Forecast, Setting
from app.models.search import SearchIndex, SearchQuery, SearchSuggestion

# Export all models for backward compatibility
__all__ = [
    # Base
    "Base",
    "TimestampMixin",
    "SoftDeleteMixin",

    # User
    "User",

    # CRM
    "Company",
    "Contact",
    "Deal",

    # Inventory
    "Product",
    "InventoryMovement",
    "StockAdjustment",
    "Warehouse",
    "WarehouseStock",

    # Finance
    "Invoice",
    "InvoiceItem",
    "Payment",
    "Expense",
    "Account",
    "JournalEntry",
    "JournalEntryLine",
    "TaxRate",

    # Project
    "Project",
    "Task",

    # HR
    "Department",
    "Employee",
    "LeaveRequest",
    "LeaveBalance",
    "Attendance",
    "PerformanceReview",
    "Payroll",

    # Workflow & Integration
    "Document",
    "Workflow",
    "WorkflowStep",
    "WorkflowExecution",
    "Webhook",
    "WebhookDelivery",
    "Integration",

    # Permissions & RBAC
    "Role",
    "Permission",
    "RolePermission",
    "UserRole",
    "FieldPermission",
    "DataPolicy",

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
