"""Atomic first-business bootstrap primitives.

The caller owns the transaction. This service never commits partially-created
tenant state and never resets an existing user's password.
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.erp import Warehouse
from app.models.identity import Branch, Business, User
from app.services.rbac import assign_role, ensure_default_roles


class BootstrapConflictError(ValueError):
    """Raised when bootstrap would mutate an existing tenant unexpectedly."""


def _required(value: str, field: str, maximum: int) -> str:
    value = value.strip()
    if not value:
        raise ValueError(f"{field} must not be empty")
    if len(value) > maximum:
        raise ValueError(f"{field} exceeds maximum length")
    return value


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
    business_name = _required(business_name, "business_name", 200)
    business_code = _required(business_code, "business_code", 64)
    branch_name = _required(branch_name, "branch_name", 200)
    branch_code = _required(branch_code, "branch_code", 64)
    owner_name = _required(owner_name, "owner_name", 200)
    owner_email = _required(owner_email, "owner_email", 320).lower()
    warehouse_code = _required(warehouse_code, "warehouse_code", 64)
    warehouse_name = (
        _required(warehouse_name, "warehouse_name", 200)
        if warehouse_name is not None
        else branch_name
    )
    if len(owner_password) < 12 or len(owner_password) > 256:
        raise ValueError("owner_password must contain 12 to 256 characters")

    # Serialize concurrent first-tenant provisioning for the same code. The
    # database unique constraint remains the final invariant; this lock keeps
    # concurrent callers deterministic instead of racing on the pre-check.
    await session.execute(select(func.pg_advisory_xact_lock(func.hashtext(business_code))))

    existing = await session.scalar(
        select(Business).where(Business.code == business_code)
    )
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
