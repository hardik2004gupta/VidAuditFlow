"""Shared Pydantic schemas for the audit pipeline and the API.

These are the single source of truth for the audit data contracts. The
LangGraph state (``graph/state.py``), the specialist agent nodes
(``graph/nodes/*``), and the FastAPI routes (``api/main.py``) all import
from here instead of each maintaining their own copy.

Phase 3 note (AI_PIPELINE_VISION.md / TECHNICAL_DEBT.md TD-9, M12): the
Compliance Agent now produces ``ComplianceIssue`` directly as validated,
structured LLM output (see ``graph/nodes/compliance_agent.py``), and that
exact same model is what flows into both the LangGraph state's
``violations`` field and the public API's ``compliance_results`` field --
there has never been more than one definition of this model, and this
phase keeps it that way while extending it with the confidence/evidence/
policy_reference/recommendation fields requested by AI_PIPELINE_VISION.md.
This is an additive, backward-compatible schema change: every field that
existed before (category, severity, description, timestamp) is unchanged;
new fields are added, none are removed or retyped.
"""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

Severity = Literal["CRITICAL", "WARNING"]
JobStatus = Literal["pending", "running", "degraded", "completed", "completed_degraded", "failed"]
StageStatus = Literal["success", "failed", "skipped"]
IngestStatus = Literal["pending", "success", "failed"]


class ComplianceIssue(BaseModel):
    """A single compliance violation identified by the Compliance Agent.

    This is the ONE definition used everywhere: the Compliance Agent's
    structured LLM output target (as an item of ``ComplianceAnalysis``),
    the LangGraph state's ``violations`` field, and the public API's
    ``compliance_results`` response field.
    """

    # --- Original fields (Phase 2), unchanged in name/type ---
    category: str = Field(description="Rule category, e.g. 'Misleading Claims'.")
    severity: Severity = Field(description="Severity of the violation.")
    description: str = Field(description="Clear explanation of why this is a violation.")
    timestamp: Optional[str] = Field(default=None, description="Approximate video timestamp, if known.")

    # --- New in Phase 3 (additive; see module docstring) ---
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Model's confidence in this specific finding, from 0.0 to 1.0.",
    )
    evidence: str = Field(
        description="The exact quote or on-screen text that triggered this finding."
    )
    policy_reference: Optional[str] = Field(
        default=None,
        description="Which retrieved policy/source this violates, if one was clearly identifiable.",
    )
    recommendation: str = Field(
        description="A concrete, actionable fix for this specific violation."
    )


class ComplianceAnalysis(BaseModel):
    """Structured-output contract for the Compliance Agent's single LLM call.

    Internal only -- never returned directly by the API. The Compliance
    Agent uses ``llm.with_structured_output(ComplianceAnalysis)`` so the
    model's response is parsed and validated by Pydantic directly, with no
    manual ``json.loads()`` or regex Markdown-fence stripping.
    """

    overall_status: Literal["PASS", "FAIL"] = Field(
        description="'FAIL' if any violation was found, 'PASS' otherwise."
    )
    violations: List[ComplianceIssue] = Field(default_factory=list)


class RetrievedRule(BaseModel):
    """One policy/regulation chunk retrieved from the Azure AI Search knowledge base."""

    content: str = Field(description="The retrieved policy text chunk.")
    source: str = Field(description="The source document this chunk came from, for citation.")


class AuditRequest(BaseModel):
    """Incoming request to start a compliance audit. Unchanged from Phase 2."""

    video_url: str = Field(description="A YouTube video URL to audit.")


class AuditResult(BaseModel):
    """The core outcome of one audit run, independent of transport. Unchanged from Phase 2."""

    video_id: str
    status: str = Field(description="Overall verdict: 'PASS' or 'FAIL'.")
    final_report: str = Field(description="AI-generated natural-language summary.")
    compliance_results: List[ComplianceIssue] = Field(default_factory=list)


class AuditResponse(AuditResult):
    """API response for a completed audit, including the session id. Unchanged from Phase 2."""

    session_id: str
