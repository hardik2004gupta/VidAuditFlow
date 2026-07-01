"""Shared FastAPI dependencies.

Routers import from here rather than constructing a DB session (or, in a
future auth phase, parsing a JWT) themselves -- see BACKEND_VISION.md's
Dependency Injection section.
"""

from __future__ import annotations

from backend.src.db.session import get_session

__all__ = ["get_session"]
