"""Atomic first-business bootstrap primitives.

The caller owns the transaction. This service never commits partially-created
tenant state and never resets an existing user's password.
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import BootstrapConflictError, ValidationError
from app.core.security import hash_password
from app.models.erp import Warehouse
from app.models.identity import Branch, Business, User
from app.services.rbac import assign_role, ensure_default_roles


def validate_required(value: str, field: str, maximum: int) -> str:
    """Return ``value`` stripped, or raise ValidationError when blank/oversized."""
    value = value.strip()
    if not value:
        raise ValidationError(f"{field} must not be empty")
    if len(value) > maximum:
        raise ValidationError(f"{field} exceeds maximum length")
    return value


def validate_password_policy(password: str, field: str = "password") -> str:
    """Return ``password`` unchanged when it satisfies the length policy."""
    minimum = settings.password_min_length
    if len(password) < minimum or len(password) > 256:
        raise ValidationError(f"{field} must contain {minimum} to 256 characters")
    return password


async def bootstrap_business(
    session: AsyncSession,
    *,
    business_name: str,
    business_code: str,
    branch_name: str,
    branch_code: str,
    owner_email: str,
    owner_password: str,
    owner_name: str,
    warehouse_name: str | None = None,
    warehouse_code: str = "MAIN",
) -> tuple[Business, Branch, Warehouse, User]:
    """Create a business, first branch/warehouse, and owner atomically.

    Existing business codes are rejected instead of silently mutating another
    tenant. The caller should execute this function inside one DB transaction.
    """
    business_name = validate_required(business_name, "business_name", 200)
    business_code = validate_required(business_code, "business_code", 64)
    branch_name = validate_required(branch_name, "branch_name", 200)
    branch_code = validate_required(branch_code, "branch_code", 64)
    owner_name = validate_required(owner_name, "owner_name", 200)
    owner_email = validate_required(owner_email, "owner_email", 320).lower()
    warehouse_code = validate_required(warehouse_code, "warehouse_code", 64)
    warehouse_name = (
        validate_required(warehouse_name, "warehouse_name", 200)
        if warehouse_name is not None
        else branch_name
    )
    validate_password_policy(owner_password, "owner_password")

    # Serialize concurrent first-tenant provisioning for the same code on
    # PostgreSQL with a transaction-scoped advisory lock; SQLite has no
    # advisory locks and serializes writers instead. The unique constraint on
    # Business.code remains the final invariant on every backend.
    if session.get_bind().dialect.name == "postgresql":
        await session.execute(select(func.pg_advisory_xact_lock(func.hashtext(business_code))))

    existing = await session.scalar(select(Business).where(Business.code == business_code))
    if existing is not None:
        raise BootstrapConflictError("Business code already exists")

    business = Business(
        name=business_name,
        code=business_code,
        default_currency="MMK",
        timezone="Asia/Yangon",
        locale="my-MM",
        active=True,
    )
    session.add(business)
    await session.flush()

    branch = Branch(
        business_id=business.id,
        name=branch_name,
        code=branch_code,
        active=True,
    )
    session.add(branch)
    await session.flush()

    warehouse = Warehouse(
        branch_id=branch.id,
        code=warehouse_code,
        name=warehouse_name,
        active=True,
    )
    session.add(warehouse)

    user = User(
        business_id=business.id,
        branch_id=branch.id,
        email=owner_email,
        password_hash=hash_password(owner_password),
        display_name=owner_name,
        active=True,
    )
    session.add(user)
    await session.flush()

    roles = await ensure_default_roles(session, business_id=business.id)
    owner_role = next(role for role in roles if role.name == "Owner")
    await assign_role(
        session,
        user_id=user.id,
        role_id=owner_role.id,
        business_id=business.id,
    )
    return business, branch, warehouse, user
