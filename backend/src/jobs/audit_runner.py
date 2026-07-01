"""Bridge between an HTTP request and the LangGraph compliance pipeline.

Owns:

- Streaming the graph's real per-node progress into ``AuditJob.current_stage``
  via ``astream_events`` -- which fires the moment a node *starts*, not
  just when it finishes. This matters most for ``transcript_agent``: it is
  the one node whose own multi-minute Azure Video Indexer wait would
  otherwise leave a polling client staring at a stale stage label for the
  bulk of the run.
- Persisting the final :class:`Report` once the graph finishes.
- Marking the job failed with a safe error message if anything goes wrong
  -- a job is never left stuck in "running".

This module makes **zero** changes to ``graph/workflow.py`` or any node
function; all progress tracking is done by observing the compiled graph's
own event stream from the outside, exactly as this phase requires
("the existing LangGraph pipeline should remain unchanged").

:func:`execute_audit_job` is safe to call either awaited inline (the
backward-compatible synchronous ``/audit`` endpoint, see ``api/main.py``)
or scheduled via FastAPI ``BackgroundTasks`` (the new
``POST /api/v1/audits`` endpoint, see ``api/routers/audits.py``) -- it has
no opinion about how it's invoked, only about what happens once it runs.
"""

from __future__ import annotations

import operator
from typing import Any, Dict, Set
from uuid import UUID

from backend.src.core.logging import get_logger
from backend.src.db.session import AsyncSessionFactory
from backend.src.graph.state import VideoAuditState
from backend.src.graph.workflow import app as compliance_graph
from backend.src.repositories.audit_repository import AuditRepository
from backend.src.repositories.report_repository import ReportRepository

logger = get_logger(__name__)

# Maps each real graph node to a human-readable stage label. Node names not
# present here (LangGraph's top-level "LangGraph" run, and the
# "route_after_join" conditional-edge function) are deliberately ignored --
# see `_STAGE_LABELS.get(node_name)` below.
#
# `transcript_agent` covers both "Downloading Video" and "Extracting
# Transcript" from AI_PIPELINE_VISION.md's example stage list in a single
# label: that node performs download + upload + poll + extraction as one
# atomic unit (see graph/nodes/transcript_agent.py), and this module only
# observes whole-node start/end events, not sub-steps within a node --
# splitting it further would require changing the node itself, which this
# phase's "existing LangGraph pipeline unchanged" constraint rules out.
_STAGE_LABELS: Dict[str, str] = {
    "supervisor_start": "Starting Audit",
    "transcript_agent": "Downloading Video & Extracting Transcript",
    "ocr_agent": "Extracting OCR",
    "supervisor_join": "Validating Results",
    "retrieval_agent": "Retrieving Policies",
    "compliance_agent": "Compliance Analysis",
    "summary_agent": "Generating Summary",
}


def _accumulating_fields() -> Set[str]:
    """Field names whose graph-state reducer is ``operator.add`` (see graph/state.py).

    Derived by inspecting the Pydantic model directly (rather than
    hardcoding the list here) so this can never silently drift out of sync
    if ``graph/state.py`` gains or loses an accumulating field later.
    """
    fields = set()
    for name, field_info in VideoAuditState.model_fields.items():
        if operator.add in getattr(field_info, "metadata", []):
            fields.add(name)
    return fields


_ACCUMULATING_FIELDS = _accumulating_fields()


def _merge_partial(accumulated: Dict[str, Any], partial: Dict[str, Any]) -> None:
    """Fold one node's state update into the running total.

    Replicates ``graph/state.py``'s own reducers -- list-concatenation for
    accumulating fields (``violations``, ``warnings``, ``errors``,
    ``processing_metadata``), last-write-wins for everything else --
    without re-invoking the graph a second time just to get its final
    state (which would duplicate every Azure/LLM call it already made).
    """
    for key, value in partial.items():
        if key in _ACCUMULATING_FIELDS:
            accumulated[key] = accumulated.get(key, []) + list(value)
        else:
            accumulated[key] = value


async def execute_audit_job(job_id: UUID, video_url: str, video_id: str) -> None:
    """Run the compliance graph for one job, persisting progress and the final report."""
    async with AsyncSessionFactory() as session:
        await AuditRepository(session).mark_running(job_id)

    logger.info("Audit job started", extra={"job_id": str(job_id), "video_id": video_id})

    accumulated_state: Dict[str, Any] = {"video_url": video_url, "video_id": video_id}
    run_config = {
        "run_name": f"audit-{video_id}",
        "tags": ["vidauditflow", "audit"],
        "metadata": {"job_id": str(job_id), "video_id": video_id},
    }

    try:
        async for event in compliance_graph.astream_events(
            {"video_url": video_url, "video_id": video_id}, version="v2", config=run_config
        ):
            node_name = event.get("name")
            stage_label = _STAGE_LABELS.get(node_name)
            if stage_label is None:
                continue

            if event["event"] == "on_chain_start":
                async with AsyncSessionFactory() as session:
                    await AuditRepository(session).update_stage(job_id, stage_label)

            elif event["event"] == "on_chain_end":
                output = event["data"].get("output")
                if isinstance(output, dict):
                    _merge_partial(accumulated_state, output)

    except Exception as exc:
        logger.exception("Audit job failed unexpectedly", extra={"job_id": str(job_id)})
        async with AsyncSessionFactory() as session:
            await AuditRepository(session).mark_failed(job_id, error_message=str(exc))
        return

    job_status = accumulated_state.get("job_status", "failed")

    # Stabilization fix (Phase 4.5): nodes accumulate hard-failure messages
    # into `state.errors` (e.g. transcript_agent's "Transcript extraction
    # failed: ..."), but nothing previously read that field back out --
    # `AuditJob.error_message` stayed `None` even for a job whose
    # `status == "failed"`. Surface it here, in the one place both the
    # background and synchronous (`/audit`) call paths pass through.
    node_errors = accumulated_state.get("errors") or []
    error_message = "; ".join(node_errors) if node_errors else None

    async with AsyncSessionFactory() as session:
        audit_repo = AuditRepository(session)
        await audit_repo.mark_terminal(job_id, status=job_status, error_message=error_message)

        # The Summary Agent always produces *some* report text -- even a
        # failure explanation (see graph/nodes/summary_agent.py) -- so
        # there is something worth persisting whenever the graph ran to
        # completion, regardless of the terminal job_status. Only a true
        # infrastructure crash (caught above, before summary_agent ever
        # ran) skips report creation entirely.
        if accumulated_state.get("summary"):
            await ReportRepository(session).create_for_job(job_id, accumulated_state)

    logger.info("Audit job finished", extra={"job_id": str(job_id), "job_status": job_status})
