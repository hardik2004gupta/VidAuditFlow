"""Adapter between the internal graph state and the stable external API shape.

The graph's internal state (``graph/state.py``) has grown richer in Phase 3
(``job_status``, ``compliance_status``, ``summary``, ``violations``,
``confidence_score``, ...), but AI_PIPELINE_VISION.md/MODERNIZATION_PLAN.md
both require the *external* API contract to stay exactly as it was:
``{video_id, status, final_report, compliance_results}``. This module is
the one place that mapping happens, so both entrypoints (``api/main.py``
and the root ``main.py`` CLI) derive the exact same external result from
the exact same internal state, instead of each re-implementing the
PASS/FAIL logic independently.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from backend.src.schemas.audit import AuditResult


def resolve_external_status(compliance_status: Optional[str]) -> str:
    """Map the internal compliance verdict to the external PASS/FAIL contract.

    Anything other than an explicit "PASS" from the Compliance Agent --  a
    failed transcript, an incomplete compliance analysis, or an explicit
    "FAIL" verdict -- is reported externally as "FAIL". The API never
    claims a video passed unless the Compliance Agent explicitly said so.
    """
    return "PASS" if compliance_status == "PASS" else "FAIL"


def to_audit_result(final_state: Dict[str, Any], fallback_video_id: str) -> AuditResult:
    """Build the stable, unchanged ``AuditResult`` shape from the graph's final state."""
    return AuditResult(
        video_id=final_state.get("video_id") or fallback_video_id,
        status=resolve_external_status(final_state.get("compliance_status")),
        final_report=final_state.get("summary") or "No report generated.",
        compliance_results=final_state.get("violations", []),
    )
