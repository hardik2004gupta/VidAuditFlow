"""Central, structured logging.

This module is the ONLY place logging is configured for the whole backend.
Every other module must call ``get_logger(__name__)`` instead of calling
``logging.basicConfig`` or building its own handlers/formatters.

Fixes TECHNICAL_DEBT.md TD-23 (audit findings L1/L2): previously
``logging.basicConfig()`` was called independently in ``main.py``,
``server.py``, and ``nodes.py`` (only the first call in a process actually
took effect), and five different ad hoc logger names were used
inconsistently. There is now one configuration path and logger names follow
the module's dotted path.
"""

from __future__ import annotations

import contextvars
import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

from backend.src.core.config import settings

# Per-request id, propagated via contextvars so concurrent asyncio requests
# each see their own value without any locking or shared mutable state.
_request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", default="-"
)

_configured = False


def set_request_id(request_id: str) -> None:
    """Bind a request id to the current async context (e.g. from middleware)."""
    _request_id_ctx.set(request_id)


def get_request_id() -> str:
    """Return the request id bound to the current async context, or ``"-"``."""
    return _request_id_ctx.get()


class _RequestIdFilter(logging.Filter):
    """Attach the current request id to every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True


class _JsonFormatter(logging.Formatter):
    """Render log records as single-line JSON for structured log ingestion."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging() -> None:
    """Configure the root logger exactly once per process.

    Safe to call multiple times (e.g. from several modules at import time);
    only the first call has any effect.
    """
    global _configured
    if _configured:
        return

    level = logging.DEBUG if settings.environment == "local" else logging.INFO

    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(_JsonFormatter())
    handler.addFilter(_RequestIdFilter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    # Quiet noisy third-party loggers rather than suppressing our own signal.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("azure").setLevel(logging.WARNING)
    logging.getLogger("azure.identity").setLevel(logging.WARNING)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Return a module-scoped logger, configuring logging on first use."""
    configure_logging()
    return logging.getLogger(name)
