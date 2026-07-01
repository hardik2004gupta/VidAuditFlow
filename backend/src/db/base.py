"""Shared SQLModel base utilities.

Small, dependency-free helpers used by every table in ``db/models.py`` --
kept separate from the table definitions themselves so `models.py` stays
focused purely on schema.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4


def new_uuid() -> UUID:
    """Default factory for every table's primary key."""
    return uuid4()


def utcnow() -> datetime:
    """Default factory for every timestamp column -- always timezone-aware UTC."""
    return datetime.now(timezone.utc)
