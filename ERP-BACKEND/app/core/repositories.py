"""
Repository Implementations for Core ERP Entities

Concrete repository classes implementing the Repository pattern
for type-safe data access across the ERP system.
"""
from typing import Type
from sqlalchemy.orm import Session

from app.core.repository import RepositoryBase
from app.models import (
    User, Product, InventoryMovement, Contact, Deal,
    Invoice, Payment, Project, Task, Document, Workflow, ActivityLog
)


class UserRepository(RepositoryBase[User]):
    """Repository for User entity operations."""
    
    @property
    def model(self) -> Type[User]:
        return User
    
    def get_by_email(self, email: str) -> User | None:
        """Get user by email address."""
        return self.get_by_field("email", email)
    
    def get_by_username(self, username: str) -> User | None:
        """Get user by username."""
        return self.get_by_field("username", username)
    
    def get_active_users(self) -> list[User]:
        """Get all active users."""
        return self.filter({"is_active": True}, limit=1000)


class ProductRepository(RepositoryBase[Product]):
    """Repository for Product entity operations."""
    
    @property
    def model(self) -> Type[Product]:
        return Product
    
    def get_by_sku(self, sku: str) -> Product | None:
        """Get product by SKU."""
        return self.get_by_field("sku", sku)
    
    def get_low_stock_products(self) -> list[Product]:
        """Get products at or below reorder level."""
        return self.db.query(Product).filter(
            Product.quantity_in_stock <= Product.reorder_level
        ).all()
    
    def get_out_of_stock_products(self) -> list[Product]:
        """Get products with zero stock."""
        return self.db.query(Product).filter(
            Product.quantity_in_stock == 0
        ).all()
    
    def get_products_by_category(self, category: str) -> list[Product]:
        """Get products in a specific category."""
        return self.filter({"category": category}, limit=1000)
    
    def get_total_stock_value(self) -> float:
        """Calculate total inventory value."""
        from sqlalchemy import func
        result = self.db.query(
            func.sum(Product.quantity_in_stock * Product.unit_price)
        ).scalar()
        return float(result) if result else 0.0


class InventoryMovementRepository(RepositoryBase[InventoryMovement]):
    """Repository for InventoryMovement entity operations."""
    
    @property
    def model(self) -> Type[InventoryMovement]:
        return InventoryMovement
    
    def get_by_product(self, product_id: int, limit: int = 100) -> list[InventoryMovement]:
        """Get movements for a specific product."""
        return self.filter(
            {"product_id": product_id},
            limit=limit,
            order_by="created_at",
            desc=True
        )


class CustomerRepository(RepositoryBase[Contact]):
    """Repository for Customer entity operations (using Contact model)."""
    
    @property
    def model(self) -> Type[Contact]:
        return Contact
    
    def get_by_email(self, email: str) -> Contact | None:
        """Get customer by email."""
        return self.get_by_field("email", email)
    
    def search_customers(self, query: str) -> list[Contact]:
        """Search customers by name or email."""
        return self.db.query(Contact).filter(
            (Contact.name.ilike(f"%{query}%")) |
            (Contact.email.ilike(f"%{query}%"))
        ).limit(100).all()


class SupplierRepository(RepositoryBase[Contact]):
    """Repository for Supplier entity operations (using Contact model)."""
    
    @property
    def model(self) -> Type[Contact]:
        return Contact
    
    def get_by_name(self, name: str) -> Contact | None:
        """Get supplier by name."""
        return self.get_by_field("name", name)


class SalesOrderRepository(RepositoryBase[Deal]):
    """Repository for SalesOrder entity operations (using Deal model)."""
    
    @property
    def model(self) -> Type[Deal]:
        return Deal
    
    def get_by_customer(self, customer_id: int) -> list[Deal]:
        """Get orders for a specific customer."""
        return self.filter({"contact_id": customer_id}, limit=100)


class PurchaseOrderRepository(RepositoryBase[Deal]):
    """Repository for PurchaseOrder entity operations (using Deal model)."""
    
    @property
    def model(self) -> Type[Deal]:
        return Deal
    
    def get_by_supplier(self, supplier_id: int) -> list[Deal]:
        """Get purchase orders for a specific supplier."""
        return self.filter({"contact_id": supplier_id}, limit=100)


class InvoiceRepository(RepositoryBase[Invoice]):
    """Repository for Invoice entity operations."""
    
    @property
    def model(self) -> Type[Invoice]:
        return Invoice
    
    def get_unpaid_invoices(self) -> list[Invoice]:
        """Get all unpaid invoices."""
        return self.filter({"paid": False}, limit=100)


class PaymentRepository(RepositoryBase[Payment]):
    """Repository for Payment entity operations."""
    
    @property
    def model(self) -> Type[Payment]:
        return Payment
    
    def get_by_invoice(self, invoice_id: int) -> list[Payment]:
        """Get payments for a specific invoice."""
        return self.filter({"invoice_id": invoice_id}, limit=100)


class ProjectRepository(RepositoryBase[Project]):
    """Repository for Project entity operations."""
    
    @property
    def model(self) -> Type[Project]:
        return Project
    
    def get_active_projects(self) -> list[Project]:
        """Get all active projects."""
        return self.filter({"status": "active"}, limit=100)


class TaskRepository(RepositoryBase[Task]):
    """Repository for Task entity operations."""
    
    @property
    def model(self) -> Type[Task]:
        return Task
    
    def get_by_project(self, project_id: int) -> list[Task]:
        """Get tasks for a specific project."""
        return self.filter({"project_id": project_id}, limit=500)


class DocumentRepository(RepositoryBase[Document]):
    """Repository for Document entity operations."""
    
    @property
    def model(self) -> Type[Document]:
        return Document
    
    def get_by_entity(self, entity_type: str, entity_id: int) -> list[Document]:
        """Get documents attached to a specific entity."""
        return self.filter({
            "entity_type": entity_type,
            "entity_id": entity_id
        }, limit=100)


class WorkflowRepository(RepositoryBase[Workflow]):
    """Repository for Workflow entity operations."""
    
    @property
    def model(self) -> Type[Workflow]:
        return Workflow
    
    def get_active_workflows(self) -> list[Workflow]:
        """Get all active workflows."""
        return self.filter({"is_active": True}, limit=100)


class ActivityLogRepository(RepositoryBase[ActivityLog]):
    """Repository for ActivityLog entity operations."""
    
    @property
    def model(self) -> Type[ActivityLog]:
        return ActivityLog
    
    def get_by_user(self, user_id: int, limit: int = 100) -> list[ActivityLog]:
        """Get activity log entries for a specific user."""
        return self.filter(
            {"user_id": user_id},
            limit=limit,
            order_by="timestamp",
            desc=True
        )


# Factory function to get repositories
def get_repository(repo_class: type, db: Session):
    """
    Factory function to instantiate repositories.
    
    Args:
        repo_class: Repository class to instantiate
        db: Database session
        
    Returns:
        Repository instance
    """
    return repo_class(db)
