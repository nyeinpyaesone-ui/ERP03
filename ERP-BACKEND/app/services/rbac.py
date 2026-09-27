"""Business-scoped RBAC provisioning primitives."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.identity import Permission, Role, User, role_permissions, user_roles


DEFAULT_ROLE_PERMISSIONS: dict[str, tuple[str, ...]] = {
    "Owner": ("sales.create",),
    "Cashier": ("sales.create",),
}


async def ensure_default_roles(session: AsyncSession, *, business_id: UUID) -> list[Role]:
    """Create/update the minimum operational roles for one business.

    This is intentionally business-scoped: roles from another tenant can never
    be reused accidentally. Callers own the surrounding transaction.
    """
    permissions = (
        await session.scalars(
            select(Permission).where(Permission.code.in_(
                {code for codes in DEFAULT_ROLE_PERMISSIONS.values() for code in codes}
            ))
        )
    ).all()
    permission_by_code = {item.code: item for item in permissions}

    missing = [
        code
        for codes in DEFAULT_ROLE_PERMISSIONS.values()
        for code in codes
        if code not in permission_by_code
    ]
    if missing:
        raise RuntimeError(f"Missing permission catalog entries: {sorted(set(missing))}")

    roles: list[Role] = []
    for name, permission_codes in DEFAULT_ROLE_PERMISSIONS.items():
        role = await session.scalar(
            select(Role).where(Role.business_id == business_id, Role.name == name)
        )
        if role is None:
            role = Role(business_id=business_id, name=name)
            session.add(role)
            await session.flush()

        role.permissions = [permission_by_code[code] for code in permission_codes]
        roles.append(role)

    return roles


async def assign_role(
    session: AsyncSession, *, user_id: UUID, role_id: UUID, business_id: UUID
) -> None:
    """Assign a role only when both user and role belong to the same business."""
    user = await session.scalar(
        select(User).where(User.id == user_id, User.business_id == business_id, User.active.is_(True))
    )
    role = await session.scalar(select(Role).where(Role.id == role_id, Role.business_id == business_id))
    if user is None or role is None:
        raise ValueError("User and role must belong to the same active business")

    exists = await session.scalar(
        select(user_roles.c.user_id).where(
            user_roles.c.user_id == user_id,
            user_roles.c.role_id == role_id,
        )
    )
    if exists is None:
        await session.execute(user_roles.insert().values(user_id=user_id, role_id=role_id))
