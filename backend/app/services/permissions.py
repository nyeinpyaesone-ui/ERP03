from functools import wraps
from typing import List, Optional, Dict, Any, Callable
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.database import get_db
from app.models import User, Role, Permission, FieldPermission, DataPolicy
from app.auth import get_current_user

class PermissionDenied(Exception):
    pass

def has_permission(user: User, resource: str, action: str, db: Session) -> bool:
    """Check if user has a specific permission through any of their roles."""
    if not user or not user.is_active:
        return False

    # Superadmin bypass
    if any(r.name == "superadmin" for r in user.roles):
        return True

    # Check all user roles for the permission
    for role in user.roles:
        for perm in role.permissions:
            if perm.resource == resource and perm.action == action:
                return True

    return False

def require_permission(resource: str, action: str):
    """Dependency factory to require a specific permission."""
    def checker(
        request: Request,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        if not has_permission(current_user, resource, action, db):
            raise HTTPException(
                status_code=403,
                detail=f"Permission denied: {resource}.{action}"
            )
        return current_user
    return checker

def get_user_permissions(user: User, db: Session) -> List[str]:
    """Get all permission names for a user."""
    permissions = set()
    for role in user.roles:
        for perm in role.permissions:
            permissions.add(f"{perm.resource}.{perm.action}")
    return list(permissions)

def get_field_permissions(user: User, resource: str, db: Session) -> Dict[str, str]:
    """Get field-level access map for a user on a resource."""
    field_map = {}
    for role in user.roles:
        for fp in role.field_permissions:
            if fp.resource == resource:
                # Higher access wins: write > read > hidden
                existing = field_map.get(fp.field_name, "hidden")
                levels = {"hidden": 0, "read": 1, "write": 2}
                if levels.get(fp.access_level, 0) > levels.get(existing, 0):
                    field_map[fp.field_name] = fp.access_level
    return field_map

def filter_fields(data: Any, user: User, resource: str, db: Session) -> Any:
    """Filter out hidden fields from data based on user's field permissions."""
    field_map = get_field_permissions(user, resource, db)

    if isinstance(data, dict):
        return {k: v for k, v in data.items() if field_map.get(k) != "hidden"}
    elif isinstance(data, list):
        return [filter_fields(item, user, resource, db) for item in data]
    elif hasattr(data, '__dict__'):
        # SQLAlchemy model
        result = {}
        for col in data.__table__.columns:
            if field_map.get(col.name) != "hidden":
                val = getattr(data, col.name)
                result[col.name] = val
        return result
    return data

def check_data_policy(user: User, resource: str, record: Any, db: Session) -> bool:
    """Check if user can access a specific record based on data policies."""
    for role in user.roles:
        policies = db.query(DataPolicy).filter(
            and_(
                DataPolicy.role_id == role.id,
                DataPolicy.resource == resource,
                DataPolicy.is_active == True
            )
        ).order_by(DataPolicy.priority).all()

        for policy in policies:
            if policy.effect == "deny":
                # Check if record matches deny condition
                if policy.condition and matches_condition(record, policy.condition):
                    return False
            elif policy.effect == "allow":
                if policy.condition and matches_condition(record, policy.condition):
                    return True

    return True  # Default allow if no policies match

def matches_condition(record: Any, condition: Dict[str, Any]) -> bool:
    """Simple condition matcher for data policies."""
    if not condition:
        return True

    record_dict = record
    if hasattr(record, '__dict__'):
        record_dict = {c.name: getattr(record, c.name) for c in record.__table__.columns}

    for key, value in condition.items():
        if key == "_and":
            if not all(matches_condition(record, v) for v in value):
                return False
        elif key == "_or":
            if not any(matches_condition(record, v) for v in value):
                return False
        elif key.startswith("_"):
            continue
        else:
            record_val = record_dict.get(key) if isinstance(record_dict, dict) else getattr(record, key, None)
            if isinstance(value, dict):
                # Operator conditions: {"eq": 5}, {"gt": 10}, etc.
                for op, op_val in value.items():
                    if op == "eq" and record_val != op_val:
                        return False
                    elif op == "ne" and record_val == op_val:
                        return False
                    elif op == "gt" and (record_val is None or record_val <= op_val):
                        return False
                    elif op == "gte" and (record_val is None or record_val < op_val):
                        return False
                    elif op == "lt" and (record_val is None or record_val >= op_val):
                        return False
                    elif op == "lte" and (record_val is None or record_val > op_val):
                        return False
                    elif op == "in" and record_val not in op_val:
                        return False
            else:
                if record_val != value:
                    return False

    return True

def permission_required(resource: str, action: str):
    """Decorator for permission checking on route handlers."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract current_user and db from kwargs
            current_user = kwargs.get('current_user')
            db = kwargs.get('db')

            if not current_user or not has_permission(current_user, resource, action, db):
                raise HTTPException(status_code=403, detail=f"Permission denied: {resource}.{action}")

            return await func(*args, **kwargs)
        return wrapper
    return decorator

