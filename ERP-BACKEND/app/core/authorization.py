"""Database-backed RBAC authorization."""

from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import current_claims
from app.db.session import SessionFactory, get_db_session
from app.models.identity import Permission, Role, User, role_permissions, user_roles


async def require_permission(
    permission_code: str,
    *,
    claims: dict,
    session: AsyncSession,
) -> None:
    try:
        user_id = UUID(claims["sub"])
        business_id = UUID(claims["business_id"])
    except (KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization claims",
        ) from exc

    stmt = (
        select(Permission.id)
        .join(role_permissions, role_permissions.c.permission_id == Permission.id)
        .join(Role, Role.id == role_permissions.c.role_id)
        .join(user_roles, user_roles.c.role_id == Role.id)
        .join(User, User.id == user_roles.c.user_id)
        .where(
            User.id == user_id,
            User.business_id == business_id,
            User.active.is_(True),
            Role.business_id == business_id,
            Permission.code == permission_code,
        )
        .limit(1)
    )
    if await session.scalar(stmt) is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied",
        )


def permission_dependency(permission_code: str):
    """Authorize against a short-lived read session.

    Endpoint handlers receive their own request session so authorization reads
    cannot leave an open transaction that prevents a service-owned transaction
    from starting.
    """

    async def dependency(claims: dict = Depends(current_claims)) -> dict:
        async with SessionFactory() as session:
            await require_permission(
                permission_code,
                claims=claims,
                session=session,
            )
        return claims

    return dependency
