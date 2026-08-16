from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models import User, Role, Permission, RolePermission, UserRole, FieldPermission, DataPolicy
from app.auth import get_current_user, require_admin, require_superadmin, has_permission, get_user_permissions
from app.services.activity_log import log_activity

router = APIRouter(prefix="/api/v1/permissions", tags=["Permissions & RBAC"])

# Schemas
class RoleCreate(BaseModel):
    name: str
    display_name: str
    description: Optional[str] = None

class RoleUpdate(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None

class PermissionAssign(BaseModel):
    permission_ids: List[int]

class UserRoleAssign(BaseModel):
    role_ids: List[int]

class FieldPermissionCreate(BaseModel):
    role_id: int
    resource: str
    field_name: str
    access_level: str = "read"  # read, write, hidden

class DataPolicyCreate(BaseModel):
    name: str
    resource: str
    role_id: int
    condition: Optional[Dict[str, Any]] = None
    effect: str = "allow"  # allow, deny
    priority: int = 100

class PermissionResponse(BaseModel):
    id: int
    name: str
    resource: str
    action: str
    description: Optional[str]

    class Config:
        from_attributes = True

class RoleResponse(BaseModel):
    id: int
    name: str
    display_name: str
    description: Optional[str]
    is_system: bool
    permissions: List[PermissionResponse] = []

    class Config:
        from_attributes = True

class FieldPermissionResponse(BaseModel):
    id: int
    role_id: int
    resource: str
    field_name: str
    access_level: str

    class Config:
        from_attributes = True

class DataPolicyResponse(BaseModel):
    id: int
    name: str
    resource: str
    role_id: int
    condition: Optional[Dict[str, Any]]
    effect: str
    priority: int
    is_active: bool

    class Config:
        from_attributes = True

# ==================== ROLES ====================

@router.get("/roles", response_model=List[RoleResponse])
def list_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """List all roles with their permissions. Admin only."""
    roles = db.query(Role).all()
    result = []
    for role in roles:
        role_data = RoleResponse(
            id=role.id,
            name=role.name,
            display_name=role.display_name,
            description=role.description,
            is_system=role.is_system,
            permissions=[
                PermissionResponse(id=p.id, name=p.name, resource=p.resource, action=p.action, description=p.description)
                for p in role.permissions
            ]
        )
        result.append(role_data)
    return result

@router.post("/roles", response_model=RoleResponse)
def create_role(
    data: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Create a new role. Admin only."""
    existing = db.query(Role).filter(Role.name == data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Role name already exists")

    role = Role(name=data.name, display_name=data.display_name, description=data.description)
    db.add(role)
    db.commit()
    db.refresh(role)

    log_activity(db, user_id=current_user.id, action="role_created", entity_type="role", entity_id=role.id)
    return RoleResponse(id=role.id, name=role.name, display_name=role.display_name, description=role.description, is_system=role.is_system)

@router.get("/roles/{role_id}", response_model=RoleResponse)
def get_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get role details with permissions. Admin only."""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    return RoleResponse(
        id=role.id,
        name=role.name,
        display_name=role.display_name,
        description=role.description,
        is_system=role.is_system,
        permissions=[
            PermissionResponse(id=p.id, name=p.name, resource=p.resource, action=p.action, description=p.description)
            for p in role.permissions
        ]
    )

@router.put("/roles/{role_id}", response_model=RoleResponse)
def update_role(
    role_id: int,
    data: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update role details. Admin only. System roles cannot be modified."""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    if role.is_system:
        raise HTTPException(status_code=400, detail="Cannot modify system roles")

    if data.display_name:
        role.display_name = data.display_name
    if data.description is not None:
        role.description = data.description

    db.commit()
    db.refresh(role)
    return RoleResponse(id=role.id, name=role.name, display_name=role.display_name, description=role.description, is_system=role.is_system)

@router.delete("/roles/{role_id}")
def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superadmin)
):
    """Delete a role. Superadmin only. System roles cannot be deleted."""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    if role.is_system:
        raise HTTPException(status_code=400, detail="Cannot delete system roles")

    db.delete(role)
    db.commit()
    log_activity(db, user_id=current_user.id, action="role_deleted", entity_type="role", entity_id=role_id)
    return {"message": "Role deleted"}

# ==================== PERMISSIONS ====================

@router.get("/permissions", response_model=List[PermissionResponse])
def list_permissions(
    resource: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """List all permissions. Admin only."""
    query = db.query(Permission)
    if resource:
        query = query.filter(Permission.resource == resource)
    return query.all()

@router.post("/roles/{role_id}/permissions")
def assign_permissions_to_role(
    role_id: int,
    data: PermissionAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Assign permissions to a role. Admin only."""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    # Clear existing and add new
    db.query(RolePermission).filter(RolePermission.role_id == role_id).delete()

    for perm_id in data.permission_ids:
        perm = db.query(Permission).filter(Permission.id == perm_id).first()
        if perm:
            rp = RolePermission(role_id=role_id, permission_id=perm_id)
            db.add(rp)

    db.commit()
    log_activity(db, user_id=current_user.id, action="permissions_assigned", entity_type="role", entity_id=role_id, details={"permission_ids": data.permission_ids})
    return {"message": f"Assigned {len(data.permission_ids)} permissions to role"}

# ==================== USER ROLES ====================

@router.get("/users/{user_id}/roles")
def get_user_roles(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get roles assigned to a user. Admin only."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "user_id": user_id,
        "roles": [
            {"id": r.id, "name": r.name, "display_name": r.display_name}
            for r in user.roles
        ]
    }

@router.post("/users/{user_id}/roles")
def assign_roles_to_user(
    user_id: int,
    data: UserRoleAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Assign roles to a user. Admin only."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Clear existing roles (except system default)
    db.query(UserRole).filter(UserRole.user_id == user_id).delete()

    for role_id in data.role_ids:
        role = db.query(Role).filter(Role.id == role_id).first()
        if role:
            ur = UserRole(user_id=user_id, role_id=role_id)
            db.add(ur)

    db.commit()
    log_activity(db, user_id=current_user.id, action="roles_assigned", entity_type="user", entity_id=user_id, details={"role_ids": data.role_ids})
    return {"message": f"Assigned {len(data.role_ids)} roles to user"}

# ==================== FIELD PERMISSIONS ====================

@router.get("/field-permissions", response_model=List[FieldPermissionResponse])
def list_field_permissions(
    role_id: Optional[int] = None,
    resource: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """List field-level permissions. Admin only."""
    query = db.query(FieldPermission)
    if role_id:
        query = query.filter(FieldPermission.role_id == role_id)
    if resource:
        query = query.filter(FieldPermission.resource == resource)
    return query.all()

@router.post("/field-permissions", response_model=FieldPermissionResponse)
def create_field_permission(
    data: FieldPermissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Create a field-level permission. Admin only."""
    role = db.query(Role).filter(Role.id == data.role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    # Check if already exists
    existing = db.query(FieldPermission).filter(
        FieldPermission.role_id == data.role_id,
        FieldPermission.resource == data.resource,
        FieldPermission.field_name == data.field_name
    ).first()

    if existing:
        existing.access_level = data.access_level
        db.commit()
        db.refresh(existing)
        return existing

    fp = FieldPermission(**data.dict())
    db.add(fp)
    db.commit()
    db.refresh(fp)

    log_activity(db, user_id=current_user.id, action="field_permission_created", entity_type="field_permission", entity_id=fp.id)
    return fp

@router.delete("/field-permissions/{fp_id}")
def delete_field_permission(
    fp_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Delete a field permission. Admin only."""
    fp = db.query(FieldPermission).filter(FieldPermission.id == fp_id).first()
    if not fp:
        raise HTTPException(status_code=404, detail="Field permission not found")
    db.delete(fp)
    db.commit()
    return {"message": "Field permission deleted"}

# ==================== DATA POLICIES ====================

@router.get("/data-policies", response_model=List[DataPolicyResponse])
def list_data_policies(
    resource: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """List data policies (row-level access). Admin only."""
    query = db.query(DataPolicy)
    if resource:
        query = query.filter(DataPolicy.resource == resource)
    return query.all()

@router.post("/data-policies", response_model=DataPolicyResponse)
def create_data_policy(
    data: DataPolicyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Create a data policy. Admin only."""
    role = db.query(Role).filter(Role.id == data.role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    policy = DataPolicy(**data.dict())
    db.add(policy)
    db.commit()
    db.refresh(policy)

    log_activity(db, user_id=current_user.id, action="data_policy_created", entity_type="data_policy", entity_id=policy.id)
    return policy

@router.put("/data-policies/{policy_id}/toggle")
def toggle_data_policy(
    policy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Toggle a data policy active/inactive. Admin only."""
    policy = db.query(DataPolicy).filter(DataPolicy.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    policy.is_active = not policy.is_active
    db.commit()
    db.refresh(policy)
    return policy

@router.delete("/data-policies/{policy_id}")
def delete_data_policy(
    policy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Delete a data policy. Admin only."""
    policy = db.query(DataPolicy).filter(DataPolicy.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    db.delete(policy)
    db.commit()
    return {"message": "Data policy deleted"}

# ==================== MY PERMISSIONS ====================

@router.get("/me")
def get_my_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current user's permissions and roles."""
    permissions = get_user_permissions(current_user, db)
    roles = [r.name for r in current_user.roles]

    # Get field permissions for all resources
    field_perms = {}
    for role in current_user.roles:
        for fp in role.field_permissions:
            key = f"{fp.resource}.{fp.field_name}"
            if key not in field_perms:
                field_perms[key] = fp.access_level
            else:
                # Higher access wins
                levels = {"hidden": 0, "read": 1, "write": 2}
                if levels.get(fp.access_level, 0) > levels.get(field_perms[key], 0):
                    field_perms[key] = fp.access_level

    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "roles": roles,
        "permissions": permissions,
        "field_permissions": field_perms,
        "is_admin": "admin" in roles or "superadmin" in roles,
        "is_superadmin": "superadmin" in roles
    }

