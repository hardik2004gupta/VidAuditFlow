"""Shared Pydantic schemas for the audit pipeline and the API.

These are the single source of truth for the audit data contracts. Both the
LangGraph state (``graph/state.py``) and the FastAPI routes (``api/main.py``)
import ``ComplianceIssue`` from here instead of each maintaining their own
copy.

Fixes TECHNICAL_DEBT.md TD-9 (audit finding M4): ``ComplianceIssue`` used to
be defined twice -- once as a ``TypedDict`` in ``graph/state.py`` and again
as a ``pydantic.BaseModel`` in ``api/server.py`` -- with no relationship
between the two, so a field added to one would silently not exist on the
other.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class ComplianceIssue(BaseModel):
    """A single compliance violation identified by the Auditor node."""

    category: str = Field(description="Rule category, e.g. 'Misleading Claims'.")
    severity: str = Field(description="Severity of the violation, e.g. 'CRITICAL' or 'WARNING'.")
    description: str = Field(description="Human-readable explanation of the violation.")
    timestamp: Optional[str] = Field(default=None, description="Video timestamp, if known.")


class AuditRequest(BaseModel):
    """Incoming request to start a compliance audit."""

    video_url: str = Field(description="A YouTube video URL to audit.")


class AuditResult(BaseModel):
    """The core outcome of one audit run, independent of transport."""

    video_id: str
    status: str = Field(description="Overall verdict: 'PASS' or 'FAIL'.")
    final_report: str = Field(description="AI-generated natural-language summary.")
    compliance_results: List[ComplianceIssue] = Field(default_factory=list)


class AuditResponse(AuditResult):
    """API response for a completed audit, including the session id."""

    session_id: str
