"""Per-node observability helpers.

AI_PIPELINE_VISION.md asks every node to expose ``start_time``, ``end_time``,
``duration``, ``status``, ``errors``, and ``tokens_used`` (when available).
Rather than duplicating timing/formatting boilerplate in five+ node
functions, each node calls :func:`start_timer` on entry and
:func:`make_trace` at every return point; the resulting :class:`StageTrace`
is appended to the graph state's ``processing_metadata`` list (see
``graph/state.py``).

This is intentionally plain functions, not a decorator -- a decorator would
have to guess a node's domain-level outcome (e.g. "did OCR degrade
gracefully" vs. "did the node crash"), whereas each node already knows its
own outcome precisely at each return point. Explicit calls are easier to
read and debug than implicit wrapping (see AI_PIPELINE_VISION.md's general
"keep it explicit" principle, echoed in this phase's constraints).
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Optional, Tuple

from pydantic import BaseModel, Field

from backend.src.schemas.audit import StageStatus


class StageTrace(BaseModel):
    """A single node's execution record, for observability/LangSmith metadata."""

    node: str
    status: StageStatus
    started_at: str
    ended_at: str
    duration_seconds: float
    error: Optional[str] = None
    tokens_used: Optional[int] = Field(default=None, description="Total LLM tokens used, if this node called one.")


def start_timer() -> Tuple[float, str]:
    """Call at the top of a node. Returns (monotonic_start, iso_started_at)."""
    return time.monotonic(), datetime.now(timezone.utc).isoformat()


def make_trace(
    node: str,
    start: float,
    started_at: str,
    status: StageStatus,
    error: Optional[str] = None,
    tokens_used: Optional[int] = None,
) -> StageTrace:
    """Build the :class:`StageTrace` for a node's return value.

    ``start``/``started_at`` should be whatever :func:`start_timer` returned
    at the top of the same node invocation.
    """
    now = time.monotonic()
    return StageTrace(
        node=node,
        status=status,
        started_at=started_at,
        ended_at=datetime.now(timezone.utc).isoformat(),
        duration_seconds=round(now - start, 3),
        error=error,
        tokens_used=tokens_used,
    )


def extract_token_usage(ai_message) -> Optional[int]:
    """Best-effort extraction of total token usage from a LangChain AIMessage.

    Different model providers/LangChain versions surface this in slightly
    different places, so this checks the common spots and returns ``None``
    (never raises) if usage information isn't available -- token counts are
    a nice-to-have observability signal, not something worth failing a node
    over.
    """
    usage = getattr(ai_message, "usage_metadata", None)
    if usage and usage.get("total_tokens") is not None:
        return usage["total_tokens"]

    response_metadata = getattr(ai_message, "response_metadata", None) or {}
    token_usage = response_metadata.get("token_usage") or {}
    return token_usage.get("total_tokens")
