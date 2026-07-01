"""Programmatic Alembic migration runner, for local-dev auto-bootstrap only.

DATABASE_PLAN.md's migration strategy: "Local dev: SQLite migrations run
automatically on app startup... Production: migrations run as an explicit
deploy step... never auto-run against production on every boot." This
module implements the local-dev half; ``api/main.py``'s startup hook only
calls it when ``settings.environment == "local"``.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from alembic import command
from alembic.config import Config

from backend.src.core.logging import get_logger

logger = get_logger(__name__)

# backend/src/db/migrations.py -> repo root
_REPO_ROOT = Path(__file__).resolve().parents[3]
_ALEMBIC_INI = _REPO_ROOT / "alembic.ini"


def _upgrade_to_head_sync() -> None:
    cfg = Config(str(_ALEMBIC_INI))
    command.upgrade(cfg, "head")


async def run_migrations() -> None:
    """Run ``alembic upgrade head`` in a worker thread (Alembic's command API is synchronous)."""
    logger.info("Running database migrations (alembic upgrade head)")
    await asyncio.to_thread(_upgrade_to_head_sync)
    logger.info("Database migrations complete")
