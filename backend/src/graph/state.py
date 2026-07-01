"""LangGraph state schema for the video compliance audit workflow.

Phase 3 change (AI_PIPELINE_VISION.md section 1): the state is now a
strongly typed Pydantic model instead of a ``TypedDict``. LangGraph accepts
a Pydantic ``BaseModel`` as a graph's state schema natively -- nodes receive
a validated model instance (attribute access, not ``.get()``), and partial
dict updates returned by nodes are still merged and re-validated the same
way ``TypedDict`` updates were. Reducers (``Annotated[..., operator.add]``)
work identically for both.

Every field below is either explicitly requested by AI_PIPELINE_VISION.md
or is minimally necessary to implement the failure-routing/degraded-mode
rules it also asks for (the three ``*_status`` fields exist because the
Supervisor cannot make routing decisions -- "did transcript succeed?" --
without somewhere to read that from). ``local_file_path``, which Phase 2's
state carried, is gone: the Transcript Agent's temp directory is now fully
local to its own function scope and never needs to be shared state.
"""

from __future__ import annotations

import operator
from typing import Annotated, Any, Dict, List, Optional

from pydantic import BaseModel, Field

from backend.src.graph.observability import StageTrace
from backend.src.schemas.audit import (
    ComplianceIssue,
    IngestStatus,
    JobStatus,
    RetrievedRule,
)

__all__ = ["ComplianceIssue", "RetrievedRule", "StageTrace", "VideoAuditState"]


class VideoAuditState(BaseModel):
    """The data schema shared across every node in the LangGraph execution."""

    # --- Input Parameters ---
    video_url: str
    video_id: str

    # --- Transcript Agent output ---
    transcript: Optional[str] = None
    transcript_status: IngestStatus = "pending"

    # --- OCR Agent output ---
    ocr_text: List[str] = Field(default_factory=list)
    ocr_status: IngestStatus = "pending"

    # --- Shared ingestion metadata (duration, platform); populated once by the Transcript Agent ---
    video_metadata: Dict[str, Any] = Field(default_factory=dict)

    # --- Retrieval Agent output ---
    retrieved_rules: List[RetrievedRule] = Field(default_factory=list)
    retrieval_status: IngestStatus = "pending"

    # --- Compliance Agent output ---
    # Annotated with operator.add so a future re-run of the node (e.g. a
    # retry) appends rather than silently overwriting prior findings.
    violations: Annotated[List[ComplianceIssue], operator.add] = Field(default_factory=list)
    compliance_status: Optional[str] = None  # "PASS" | "FAIL", mirrors ComplianceAnalysis.overall_status

    # --- Summary Agent output ---
    summary: Optional[str] = None  # Full Markdown report (executive summary + score + fixes + top violations)
    confidence_score: Optional[float] = None  # Overall compliance score, 0-100
    risk_level: Optional[str] = None  # "LOW" | "MEDIUM" | "HIGH"

    # --- Orchestration / observability (owned by the Supervisor) ---
    job_status: JobStatus = "pending"
    warnings: Annotated[List[str], operator.add] = Field(default_factory=list)
    errors: Annotated[List[str], operator.add] = Field(default_factory=list)
    processing_metadata: Annotated[List[StageTrace], operator.add] = Field(default_factory=list)
