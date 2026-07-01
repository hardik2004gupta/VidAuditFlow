"""Supervisor: pure-Python orchestration, no LLM calls, no external I/O.

AI_PIPELINE_VISION.md is explicit that the Supervisor is not an agent -- it
only fans out to the parallel Transcript/OCR branches, joins their results,
validates state, and routes around failures. Everything here is
deterministic control flow: same input state always produces the same
routing decision, with no autonomous planning, tool-calling, or
self-reflection of any kind.

Two node functions plus one routing function:

- :func:`supervisor_start` -- the graph's entry point. Marks the job
  running and produces the first observability trace. Fans out to the
  Transcript and OCR agents via the graph's edges (see ``graph/workflow.py``)
  -- this function itself does not need to do anything to "cause" the
  fan-out; LangGraph runs every node with an edge from this one
  concurrently.
- :func:`supervisor_join` -- runs after both parallel branches complete.
  Inspects ``transcript_status``/``ocr_status`` and records a warning if
  OCR degraded (section 13: "If OCR fails: Continue. Mark report:
  ocr_unavailable.").
- :func:`route_after_join` -- a conditional-edge routing function (not a
  node itself). If the transcript failed, the audit cannot proceed to
  Retrieval/Compliance (section 13: "If transcript fails: Fail audit."), so
  this routes straight to the Summary Agent, which knows how to render a
  failure report without needing any of the downstream data.
"""

from __future__ import annotations

from typing import Any, Dict

from backend.src.core.logging import get_logger
from backend.src.graph.observability import make_trace, start_timer
from backend.src.graph.state import VideoAuditState

logger = get_logger(__name__)


async def supervisor_start(state: VideoAuditState) -> Dict[str, Any]:
    """Entry point: mark the job running before fanning out to the agents."""
    t0, started_at = start_timer()
    logger.info("Supervisor: starting audit", extra={"video_id": state.video_id, "video_url": state.video_url})
    return {
        "job_status": "running",
        "processing_metadata": [make_trace("supervisor_start", t0, started_at, "success")],
    }


async def supervisor_join(state: VideoAuditState) -> Dict[str, Any]:
    """Join point after the parallel Transcript/OCR branches complete."""
    t0, started_at = start_timer()
    warnings = []

    if state.transcript_status != "success":
        logger.error("Supervisor: transcript unavailable, audit will fail", extra={"video_id": state.video_id})
    elif state.ocr_status != "success":
        warnings.append("ocr_unavailable")
        logger.warning("Supervisor: OCR unavailable, continuing in degraded mode", extra={"video_id": state.video_id})
    else:
        logger.info("Supervisor: transcript and OCR both available", extra={"video_id": state.video_id})

    return {
        "warnings": warnings,
        "processing_metadata": [make_trace("supervisor_join", t0, started_at, "success")],
    }


def route_after_join(state: VideoAuditState) -> str:
    """Conditional-edge routing: skip straight to Summary if transcript failed."""
    if state.transcript_status != "success":
        return "summary_agent"
    return "retrieval_agent"
