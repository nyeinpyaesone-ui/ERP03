"""Atomic first-business bootstrap primitives.

The caller owns the transaction. This service never commits partially-created
tenant state and never resets an existing user's password.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.erp import Warehouse
from app.models.identity import Branch, Business, Role, User
from app.services.rbac import assign_role, ensure_default_roles


class BootstrapConflictError(ValueError):
    """Raised when bootstrap would mutate an existing tenant unexpectedly."""


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
    existing = await session.scalar(
        select(Business).where(Business.code == business_code)
    )
    if existing is not None:
        raise BootstrapConflictError("Business code already exists")

    business = Business(
        name=business_name.strip(),
        code=business_code.strip(),
        default_currency="MMK",
        timezone="Asia/Yangon",
        locale="my-MM",
        active=True,
    )
    session.add(business)
    await session.flush()

    branch = Branch(
        business_id=business.id,
        name=branch_name.strip(),
        code=branch_code.strip(),
        active=True,
    )
    session.add(branch)
    await session.flush()

    warehouse = Warehouse(
        branch_id=branch.id,
        code=warehouse_code.strip(),
        name=(warehouse_name or branch_name).strip(),
        active=True,
    )
    session.add(warehouse)

    user = User(
        business_id=business.id,
        branch_id=branch.id,
        email=owner_email.strip().lower(),
        password_hash=hash_password(owner_password),
        display_name=owner_name.strip(),
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
