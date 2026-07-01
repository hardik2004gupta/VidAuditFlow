"""Summary Agent.

Responsibilities (AI_PIPELINE_VISION.md section 7): produce an executive
summary, compliance score, risk level, suggested fixes, and a top-violations
list. Kept deliberately lightweight (section 7: "Keep this lightweight"):

- Compliance score, risk level, top violations, and suggested fixes are all
  computed *deterministically* in plain Python from the already-structured
  ``violations`` list -- no LLM call, no failure surface, instant.
  ``suggested_fixes`` in particular is just the deduplicated
  ``recommendation`` field the Compliance Agent already produced per
  violation; there is no need for a second LLM call to invent fixes that
  already exist in the data.
- Only the natural-language *executive summary* paragraph benefits from an
  LLM, so exactly one small, focused call is made for that -- and if it
  fails, a deterministic template fallback is used instead of failing the
  whole audit over what is, at that point, a "nice to have" narrative.

This node also finalizes ``job_status`` (completed / completed_degraded /
failed), since by this point in the graph every upstream stage's outcome is
already known and this is the last node before END.
"""

from __future__ import annotations

from typing import Any, Dict, List

from langchain_core.messages import HumanMessage, SystemMessage

from backend.src.core.logging import get_logger
from backend.src.graph.llm_clients import get_chat_llm
from backend.src.graph.observability import extract_token_usage, make_trace, start_timer
from backend.src.graph.prompts import SUMMARY_SYSTEM_PROMPT, build_summary_context
from backend.src.graph.state import VideoAuditState
from backend.src.schemas.audit import ComplianceIssue

logger = get_logger(__name__)

NODE_NAME = "summary_agent"

_SEVERITY_PENALTY = {"CRITICAL": 30.0, "WARNING": 10.0}
_SEVERITY_RANK = {"CRITICAL": 0, "WARNING": 1}
_TOP_VIOLATIONS_LIMIT = 5

_TRANSCRIPT_FAILED_REPORT = "Audit skipped because video processing failed (No Transcript)."
_COMPLIANCE_UNAVAILABLE_REPORT = (
    "Automated compliance analysis could not be completed due to a system error. "
    "Manual review is recommended."
)


def _compute_compliance_score(violations: List[ComplianceIssue]) -> float:
    """100, minus a severity- and confidence-weighted penalty per violation."""
    score = 100.0
    for violation in violations:
        penalty = _SEVERITY_PENALTY.get(violation.severity, 10.0) * violation.confidence
        score -= penalty
    return max(0.0, min(100.0, score))


def _compute_risk_level(violations: List[ComplianceIssue]) -> str:
    if any(v.severity == "CRITICAL" for v in violations):
        return "HIGH"
    if violations:
        return "MEDIUM"
    return "LOW"


def _top_violations(violations: List[ComplianceIssue], limit: int = _TOP_VIOLATIONS_LIMIT) -> List[ComplianceIssue]:
    return sorted(violations, key=lambda v: (_SEVERITY_RANK.get(v.severity, 2), -v.confidence))[:limit]


def _suggested_fixes(violations: List[ComplianceIssue]) -> List[str]:
    seen = set()
    fixes = []
    for violation in violations:
        if violation.recommendation and violation.recommendation not in seen:
            seen.add(violation.recommendation)
            fixes.append(violation.recommendation)
    return fixes


def _fallback_executive_summary(violations: List[ComplianceIssue], score: float, risk_level: str) -> str:
    """Deterministic summary used if the narrative LLM call fails or is skipped."""
    if not violations:
        return f"This video passed compliance review with a score of {score:.0f}/100. No violations were found."
    n_critical = sum(1 for v in violations if v.severity == "CRITICAL")
    n_warning = sum(1 for v in violations if v.severity == "WARNING")
    return (
        f"This video scored {score:.0f}/100 with {n_critical} critical and {n_warning} warning "
        f"violation(s) detected. Overall risk level: {risk_level}."
    )


def _render_report(
    executive_summary: str,
    score: float,
    risk_level: str,
    top_violations: List[ComplianceIssue],
    suggested_fixes: List[str],
) -> str:
    """Assemble the final Markdown report -- the public API's ``final_report`` string."""
    if top_violations:
        violations_md = "\n".join(
            f"- **[{v.severity}] {v.category}** (confidence {v.confidence:.2f}): {v.description}"
            for v in top_violations
        )
    else:
        violations_md = "No violations found."

    fixes_md = "\n".join(f"- {fix}" for fix in suggested_fixes) if suggested_fixes else "None needed."

    return f"""\
## Executive Summary
{executive_summary}

## Compliance Score
{score:.0f} / 100

## Risk Level
{risk_level}

## Top Violations
{violations_md}

## Suggested Fixes
{fixes_md}
"""


def _finalize_job_status(state: VideoAuditState) -> str:
    if state.transcript_status != "success":
        return "failed"
    if state.warnings:
        return "completed_degraded"
    return "completed"


async def summary_agent(state: VideoAuditState) -> Dict[str, Any]:
    """Produce the final report, score, risk level, and job status."""
    t0, started_at = start_timer()
    logger.info("Summary agent started", extra={"video_id": state.video_id})

    # --- Case 1: no transcript at all -- nothing to summarize. ---
    if state.transcript_status != "success":
        return {
            "summary": _TRANSCRIPT_FAILED_REPORT,
            "job_status": "failed",
            "processing_metadata": [make_trace(NODE_NAME, t0, started_at, "success")],
        }

    violations = state.violations
    score = _compute_compliance_score(violations)
    risk_level = _compute_risk_level(violations)
    top_violations = _top_violations(violations)
    suggested_fixes = _suggested_fixes(violations)

    # --- Case 2: compliance analysis itself never completed. ---
    if state.compliance_status is None:
        return {
            "summary": _COMPLIANCE_UNAVAILABLE_REPORT,
            "confidence_score": score,
            "risk_level": risk_level,
            "job_status": _finalize_job_status(state),
            "processing_metadata": [make_trace(NODE_NAME, t0, started_at, "success")],
        }

    # --- Case 3: normal path -- try one small LLM call for the narrative. ---
    tokens_used = 0
    try:
        llm = get_chat_llm(temperature=0.3)
        context = build_summary_context(violations, score, risk_level)
        response = await llm.ainvoke(
            [SystemMessage(content=SUMMARY_SYSTEM_PROMPT), HumanMessage(content=context)]
        )
        executive_summary = response.content.strip()
        tokens_used += extract_token_usage(response) or 0
        if not executive_summary:
            raise ValueError("Summary LLM returned an empty response.")
    except Exception as exc:
        logger.warning(
            "Summary agent's narrative LLM call failed; using deterministic fallback",
            extra={"video_id": state.video_id, "error": str(exc)},
        )
        executive_summary = _fallback_executive_summary(violations, score, risk_level)

    report = _render_report(executive_summary, score, risk_level, top_violations, suggested_fixes)
    job_status = _finalize_job_status(state)

    logger.info(
        "Summary agent completed",
        extra={"video_id": state.video_id, "score": score, "risk_level": risk_level, "job_status": job_status},
    )
    return {
        "summary": report,
        "confidence_score": score,
        "risk_level": risk_level,
        "job_status": job_status,
        "processing_metadata": [make_trace(NODE_NAME, t0, started_at, "success", tokens_used=tokens_used)],
    }
