"""Async SQLModel engine + session factory.

One engine per process, built from ``settings.database_url`` -- identical
code path whether that URL points at a local SQLite file (``aiosqlite``
driver) or a Postgres server (``asyncpg`` driver). This module exposes two
ways to get a session:

- :func:`get_session` -- a FastAPI dependency (``Depends(get_session)``),
  one session per request, closed automatically after the request.
- :data:`AsyncSessionFactory` -- the raw sessionmaker, for code that runs
  *outside* request scope (``jobs/audit_runner.py``'s background task,
  which must never reuse a request-scoped session after the request that
  started it has already returned).
"""

from __future__ import annotations

from typing import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.src.core.config import settings

# `echo=False` even in local dev -- SQL statement logging is a debugging
# opt-in, not something that should spam every request's structured logs.
engine: AsyncEngine = create_async_engine(settings.database_url, echo=False)

AsyncSessionFactory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: one session per request."""
    async with AsyncSessionFactory() as session:
        yield session
