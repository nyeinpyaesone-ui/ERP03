"""
Models package initialization
Organizes models by domain for better maintainability
"""

from app.models.base import Base, TimestampMixin, SoftDeleteMixin
from app.models.user import User
from app.models.crm import Company, Contact, Deal
from app.models.hr import Department, Employee, LeaveRequest, LeaveBalance, Attendance, PerformanceReview, Payroll
from app.models.inventory import Product, InventoryMovement, StockAdjustment, Warehouse, WarehouseStock
from app.models.finance import Invoice, InvoiceItem, Payment, Expense, Account, JournalEntry, JournalEntryLine, TaxRate
from app.models.projects import Project, Task, TimeEntry, ProjectMilestone, ProjectDocument
from app.models.documents import Document
from app.models.workflows import Workflow, WorkflowStep, WorkflowExecution
from app.models.integrations import Webhook, WebhookDelivery, Integration
from app.models.analytics import ActivityLog, Notification, Report, Forecast
from app.models.settings import Setting

__all__ = [
    # Base
    "Base",
    "TimestampMixin",
    "SoftDeleteMixin",

    # User & Auth
    "User",

    # CRM
    "Company",
    "Contact",
    "Deal",

    # HR
    "Department",
    "Employee",
    "LeaveRequest",
    "LeaveBalance",
    "Attendance",
    "PerformanceReview",
    "Payroll",

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

    # Projects
    "Project",
    "Task",
    "TimeEntry",
    "ProjectMilestone",
    "ProjectDocument",

    # Documents
    "Document",

    # Workflows
    "Workflow",
    "WorkflowStep",
    "WorkflowExecution",

    # Integrations
    "Webhook",
    "WebhookDelivery",
    "Integration",

    # Analytics
    "ActivityLog",
    "Notification",
    "Report",
    "Forecast",

    # Settings
    "Setting",
]
