"""
RBAC Engine - Role-Based Access Control
Permission evaluation and role management
"""
from typing import List, Dict, Any, Optional
from functools import lru_cache


class Role:
    """Represents a role with associated permissions"""
    
    def __init__(self, role_id: str, name: str, permissions: List[str]):
        self.role_id = role_id
        self.name = name
        self.permissions = set(permissions)
    
    def has_permission(self, permission: str) -> bool:
        """Check if role has a specific permission"""
        return permission in self.permissions
    
    def add_permission(self, permission: str):
        """Add a permission to the role"""
        self.permissions.add(permission)
    
    def remove_permission(self, permission: str):
        """Remove a permission from the role"""
        self.permissions.discard(permission)


class RBACEngine:
    """Role-Based Access Control Engine"""
    
    def __init__(self):
        self.roles: Dict[str, Role] = {}
        self.user_roles: Dict[int, List[str]] = {}  # user_id -> role_ids
    
    def register_role(self, role: Role):
        """Register a role in the system"""
        self.roles[role.role_id] = role
    
    def get_role(self, role_id: str) -> Optional[Role]:
        """Get a role by ID"""
        return self.roles.get(role_id)
    
    def assign_role_to_user(self, user_id: int, role_id: str):
        """Assign a role to a user"""
        if role_id not in self.roles:
            raise ValueError(f"Role '{role_id}' does not exist")
        
        if user_id not in self.user_roles:
            self.user_roles[user_id] = []
        
        if role_id not in self.user_roles[user_id]:
            self.user_roles[user_id].append(role_id)
    
    def remove_role_from_user(self, user_id: int, role_id: str):
        """Remove a role from a user"""
        if user_id in self.user_roles and role_id in self.user_roles[user_id]:
            self.user_roles[user_id].remove(role_id)
    
    def get_user_roles(self, user_id: int) -> List[Role]:
        """Get all roles for a user"""
        role_ids = self.user_roles.get(user_id, [])
        return [self.roles[rid] for rid in role_ids if rid in self.roles]
    
    def has_permission(self, user_id: int, permission: str) -> bool:
        """Check if a user has a specific permission through any of their roles"""
        user_role_ids = self.user_roles.get(user_id, [])
        
        for role_id in user_role_ids:
            role = self.roles.get(role_id)
            if role and role.has_permission(permission):
                return True
        
        return False
    
    def has_any_permission(self, user_id: int, permissions: List[str]) -> bool:
        """Check if user has any of the specified permissions"""
        return any(self.has_permission(user_id, perm) for perm in permissions)
    
    def has_all_permissions(self, user_id: int, permissions: List[str]) -> bool:
        """Check if user has all of the specified permissions"""
        return all(self.has_permission(user_id, perm) for perm in permissions)


# Global RBAC engine instance
rbac_engine = RBACEngine()


def init_default_roles():
    """Initialize default system roles"""
    # Admin role with full access
    admin_role = Role(
        role_id="admin",
        name="Administrator",
        permissions=["*"]  # Wildcard for all permissions
    )
    
    # Finance role
    finance_role = Role(
        role_id="finance_manager",
        name="Finance Manager",
        permissions=[
            "finance.read",
            "finance.write",
            "finance.approve",
            "reports.read"
        ]
    )
    
    # HR role
    hr_role = Role(
        role_id="hr_manager",
        name="HR Manager",
        permissions=[
            "hcm.read",
            "hcm.write",
            "employees.read",
            "employees.write"
        ]
    )
    
    # Inventory role
    inventory_role = Role(
        role_id="inventory_manager",
        name="Inventory Manager",
        permissions=[
            "inventory.read",
            "inventory.write",
            "products.read",
            "products.write"
        ]
    )
    
    # Register all roles
    rbac_engine.register_role(admin_role)
    rbac_engine.register_role(finance_role)
    rbac_engine.register_role(hr_role)
    rbac_engine.register_role(inventory_role)


# Initialize default roles on module load
init_default_roles()

