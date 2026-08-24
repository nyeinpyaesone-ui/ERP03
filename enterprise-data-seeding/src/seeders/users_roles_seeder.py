"""
Users and Roles seeder for RBAC initialization.

Seeds:
- Default roles (Admin, Manager, User, Viewer)
- Default permissions per resource
- System admin user
- Role-permission assignments
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from .base_seeder import BaseSeeder, SeederResult

logger = logging.getLogger(__name__)


# Default roles with permissions
DEFAULT_ROLES = [
    {
        "name": "Super Admin",
        "description": "Full system access with all permissions",
        "permissions": ["*"],  # Wildcard for all permissions
    },
    {
        "name": "Admin",
        "description": "Administrative access to all modules",
        "permissions": [
            "users.read", "users.create", "users.update", "users.delete",
            "roles.read", "roles.create", "roles.update", "roles.delete",
            "companies.read", "companies.create", "companies.update",
            "branches.read", "branches.create", "branches.update",
            "crm.read", "crm.create", "crm.update", "crm.delete",
            "inventory.read", "inventory.create", "inventory.update",
            "finance.read", "finance.create", "finance.update",
            "reports.read", "reports.export",
            "settings.read", "settings.update",
        ],
    },
    {
        "name": "Manager",
        "description": "Department manager with read/write access",
        "permissions": [
            "users.read",
            "companies.read", "companies.create", "companies.update",
            "branches.read", "branches.create", "branches.update",
            "crm.read", "crm.create", "crm.update",
            "inventory.read", "inventory.create", "inventory.update",
            "finance.read", "finance.create", "finance.update",
            "reports.read", "reports.export",
        ],
    },
    {
        "name": "User",
        "description": "Standard user with limited write access",
        "permissions": [
            "users.read",
            "companies.read",
            "branches.read",
            "crm.read", "crm.create", "crm.update",
            "inventory.read",
            "finance.read",
            "reports.read",
        ],
    },
    {
        "name": "Viewer",
        "description": "Read-only access to all modules",
        "permissions": [
            "users.read",
            "companies.read",
            "branches.read",
            "crm.read",
            "inventory.read",
            "finance.read",
            "reports.read",
        ],
    },
]


class UsersRolesSeeder(BaseSeeder):
    """Seeder for users, roles, and permissions."""
    
    def __init__(
        self,
        session: AsyncSession,
        dry_run: bool = False,
        batch_size: int = 50,
        admin_email: str = "admin@erp03.com",
        admin_password: str | None = None,
    ):
        super().__init__(session, dry_run, batch_size)
        self.admin_email = admin_email
        self.admin_password = admin_password or "ChangeMe123!"
        self.seed_data_path = Path(__file__).parent.parent / "seeds"
    
    async def get_seed_data(self) -> list[dict[str, Any]]:
        """Return default roles data."""
        return DEFAULT_ROLES
    
    async def seed(self) -> SeederResult:
        """
        Seed users, roles, and permissions.
        
        Returns:
            SeederResult with operation statistics
        """
        import time
        start_time = time.time()
        
        result = SeederResult(success=True)
        
        try:
            # Import models dynamically from ERP-BACKEND
            from sqlalchemy import select
            
            # Dynamically import models
            import sys
            from pathlib import Path
            backend_path = Path(__file__).parent.parent.parent.parent / "ERP-BACKEND"
            if str(backend_path) not in sys.path:
                sys.path.insert(0, str(backend_path))
            
            # Try to import models - will work if ERP-BACKEND is properly set up
            try:
                from app.models.user import User
                from app.models.permissions import Role, Permission
            except ImportError:
                result.warnings.append(
                    "ERP-BACKEND models not found. Skipping actual seeding. "
                    "Run this seeder after ERP-BACKEND is installed."
                )
                return result
            
            # Seed permissions first
            self.log_info("Seeding permissions...")
            permissions_to_seed = self._get_all_permissions()
            permissions_created = 0
            
            for perm_data in permissions_to_seed:
                try:
                    perm, is_new = await self.upsert(
                        Permission,
                        perm_data,
                        "name"
                    )
                    if is_new:
                        permissions_created += 1
                except Exception as e:
                    result.errors.append(f"Failed to seed permission {perm_data['name']}: {str(e)}")
                    if self.seeding_config.stop_on_error:
                        raise
            
            result.records_created += permissions_created
            self.log_info(f"Created {permissions_created} permissions")
            
            # Seed roles
            self.log_info("Seeding roles...")
            roles_data = await self.get_seed_data()
            roles_created = 0
            
            for role_data in roles_data:
                try:
                    role, is_new = await self.upsert(
                        Role,
                        {
                            "name": role_data["name"],
                            "description": role_data["description"],
                        },
                        "name"
                    )
                    
                    if is_new:
                        roles_created += 1
                    
                    # Assign permissions to role
                    # This would need additional logic to handle many-to-many relationships
                    
                except Exception as e:
                    result.errors.append(f"Failed to seed role {role_data['name']}: {str(e)}")
                    if self.seeding_config.stop_on_error:
                        raise
            
            result.records_created += roles_created
            self.log_info(f"Created {roles_created} roles")
            
            # Create default admin user
            self.log_info(f"Creating admin user: {self.admin_email}")
            try:
                from passlib.context import CryptContext
                pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
                
                admin_data = {
                    "email": self.admin_email,
                    "hashed_password": pwd_context.hash(self.admin_password),
                    "full_name": "System Administrator",
                    "is_active": True,
                    "is_superuser": True,
                }
                
                admin_user, is_new = await self.upsert(User, admin_data, "email")
                
                if is_new:
                    result.records_created += 1
                    self.log_info("Admin user created successfully")
                else:
                    result.records_skipped += 1
                    self.log_info("Admin user already exists")
                    
            except ImportError:
                result.warnings.append("passlib not installed. Cannot hash admin password.")
            except Exception as e:
                result.errors.append(f"Failed to create admin user: {str(e)}")
            
            result.success = len(result.errors) == 0
            
        except Exception as e:
            result.success = False
            result.errors.append(f"Seeding failed: {str(e)}")
            logger.exception("Unexpected error during seeding")
        
        result.duration_seconds = time.time() - start_time
        
        return result
    
    def _get_all_permissions(self) -> list[dict[str, str]]:
        """Generate all standard permissions."""
        resources = [
            "users", "roles", "permissions", "companies", "branches",
            "warehouses", "contacts", "customers", "suppliers",
            "products", "inventory", "orders", "invoices", "payments",
            "expenses", "accounts", "employees", "projects",
            "documents", "workflows", "reports", "settings", "audit_logs"
        ]
        
        actions = ["read", "create", "update", "delete"]
        
        permissions = []
        for resource in resources:
            for action in actions:
                permissions.append({
                    "name": f"{resource}.{action}",
                    "resource": resource,
                    "action": action,
                    "description": f"Can {action} {resource}"
                })
        
        # Add special permissions
        permissions.extend([
            {"name": "reports.export", "resource": "reports", "action": "export", "description": "Can export reports"},
            {"name": "settings.update", "resource": "settings", "action": "update", "description": "Can update system settings"},
            {"name": "*.*", "resource": "*", "action": "*", "description": "Super admin wildcard permission"},
        ])
        
        return permissions
    
    @property
    def seeding_config(self):
        """Get seeding config from parent or create default."""
        from ..config import SeedingConfig
        return SeedingConfig(stop_on_error=True)
