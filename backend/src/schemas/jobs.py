"""Pydantic request/response models for the job-based audit API (Phase 4).

Kept separate from ``schemas/audit.py`` (the AI pipeline's own contracts --
``ComplianceIssue``, ``AuditRequest``/``AuditResponse`` for the
backward-compatible synchronous ``/audit`` endpoint) since these describe
the *persistence* layer's HTTP surface instead. Per this phase's section 9
("Remove untyped dictionaries"), every field here is a concrete type, not
a loose ``dict`` -- ``compliance_results``/``sources``/``processing_metadata``
reuse the exact same typed models the graph itself produces
(``ComplianceIssue``, ``RetrievedRule``, ``StageTrace``), so there is no
second, looser copy of those shapes.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from backend.src.db.models import AuditJob, Report
from backend.src.graph.observability import StageTrace
from backend.src.schemas.audit import ComplianceIssue, RetrievedRule


class AuditJobCreate(BaseModel):
    """Request body for ``POST /api/v1/audits``."""

    video_url: str = Field(description="A YouTube video URL to audit.")


class AuditJobRead(BaseModel):
    """Response shape for job creation/list/status endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: str
    current_stage: Optional[str] = None
    video_url: str
    video_id: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    report_id: Optional[UUID] = Field(
        default=None, description="Set once the job has a persisted Report to fetch."
    )

    @classmethod
    def from_job(cls, job: AuditJob, report_id: Optional[UUID] = None) -> "AuditJobRead":
        """Build the response DTO from an ORM row plus its (separately looked-up) report id."""
        return cls(
            id=job.id,
            status=job.status,
            current_stage=job.current_stage,
            video_url=job.video_url,
            video_id=job.video_id,
            error_message=job.error_message,
            created_at=job.created_at,
            updated_at=job.updated_at,
            completed_at=job.completed_at,
            report_id=report_id,
        )


class ReportSummary(BaseModel):
    """Lightweight report shape -- omits the large report body/violations list."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    audit_job_id: UUID
    final_status: str
    confidence_score: Optional[float] = None
    risk_level: Optional[str] = None
    created_at: datetime

    @classmethod
    def from_report(cls, report: Report) -> "ReportSummary":
        return cls.model_validate(report)


class ReportRead(ReportSummary):
    """Full report detail, per ``GET /api/v1/reports/{id}``.

    Inherits :meth:`ReportSummary.from_report` unchanged -- the classmethod
    already binds ``cls`` to whichever subclass calls it, so
    ``ReportRead.from_report(report)`` correctly returns a ``ReportRead``
    without needing its own duplicate override.
    """

    final_report: str
    compliance_results: List[ComplianceIssue] = Field(default_factory=list)
    video_metadata: Dict[str, Any] = Field(default_factory=dict)
    processing_metadata: List[StageTrace] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    sources: List[RetrievedRule] = Field(default_factory=list)
