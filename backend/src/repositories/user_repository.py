"""Thin data-access layer for :class:`User` rows.

No authentication exists yet in this phase, so nothing in the current
request flow calls this repository -- it exists so the schema and CRUD
surface are ready for a future auth phase to build on, per DATABASE_PLAN.md.
Deliberately just CRUD: no password/session handling, no business logic.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from backend.src.db.models import User


class UserRepository:
    """CRUD operations for :class:`User`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, user_id: UUID) -> Optional[User]:
        return await self._session.get(User, user_id)

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self._session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def create(self, *, email: str) -> User:
        user = User(email=email)
        self._session.add(user)
        await self._session.commit()
        await self._session.refresh(user)
        return user
