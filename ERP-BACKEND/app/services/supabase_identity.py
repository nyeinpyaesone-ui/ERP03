"""Domain service for explicitly linking a verified Supabase identity."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, ForbiddenError
from app.models.identity import User


async def link_supabase_identity(
    session: AsyncSession,
    erp_user: User,
    supabase_user_id: UUID,
    supabase_email: str,
) -> None:
    """Validate ownership and persist the one-to-one identity association.

    Lock the ERP user row so concurrent link attempts cannot overwrite one
    another. The unique database constraint on supabase_user_id remains the
    final arbiter when two ERP users race to claim the same Supabase identity.
    """
    normalized_email = supabase_email.strip().casefold()
    if normalized_email != erp_user.email.strip().casefold():
        raise ForbiddenError("Supabase email must match the authenticated ERP03 user's email")

    locked_user = await session.scalar(
        select(User).where(User.id == erp_user.id, User.active.is_(True)).with_for_update()
    )
    if locked_user is None:
        raise ForbiddenError("Authenticated ERP03 user is no longer active")
    if normalized_email != locked_user.email.strip().casefold():
        raise ForbiddenError("Supabase email must match the authenticated ERP03 user's email")

    existing = await session.scalar(select(User).where(User.supabase_user_id == supabase_user_id))
    if existing is not None and existing.id != locked_user.id:
        raise ConflictError("Supabase identity is already linked to another ERP03 user")
    if locked_user.supabase_user_id not in (None, supabase_user_id):
        raise ConflictError("This ERP03 user already has a different Supabase identity linked")

    locked_user.supabase_user_id = supabase_user_id
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ConflictError("Supabase identity is already linked to another ERP03 user") from exc
