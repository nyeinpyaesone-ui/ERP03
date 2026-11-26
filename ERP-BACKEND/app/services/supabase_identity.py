"""Domain service for explicitly linking a verified Supabase identity."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, ForbiddenError
from app.models.identity import User


async def link_supabase_identity(
    session: AsyncSession,
    erp_user: User,
    supabase_user_id: UUID,
    supabase_email: str,
) -> None:
    """Validate ownership and persist the one-to-one identity association."""
    if supabase_email.strip().casefold() != erp_user.email.strip().casefold():
        raise ForbiddenError(
            "Supabase email must match the authenticated ERP03 user's email"
        )

    existing = await session.scalar(
        select(User).where(User.supabase_user_id == supabase_user_id)
    )
    if existing is not None and existing.id != erp_user.id:
        raise ConflictError(
            "Supabase identity is already linked to another ERP03 user"
        )
    if erp_user.supabase_user_id not in (None, supabase_user_id):
        raise ConflictError(
            "This ERP03 user already has a different Supabase identity linked"
        )

    erp_user.supabase_user_id = supabase_user_id
    await session.commit()
