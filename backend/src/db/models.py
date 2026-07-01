"""SQLModel table definitions -- the single source of truth for the database schema.

Exactly three tables, per DATABASE_PLAN.md: :class:`User`, :class:`AuditJob`,
:class:`Report`. No other tables are added in this phase.

Two intentional deviations from DATABASE_PLAN.md's original sketch, both
because that document predates Phase 3's richer graph output and this
phase's explicit "do not implement auth" scope:

- ``AuditJob.user_id`` is **nullable**. DATABASE_PLAN.md assumed Supabase
  Auth would already exist and every job would have an owner; this phase
  explicitly excludes authentication, so there is no user to attach a job
  to yet. The column, index, and foreign key are still here so a future
  auth phase only has to start populating it, not add it.
- ``Report`` gained three JSON columns DATABASE_PLAN.md didn't anticipate
  (``processing_metadata``, ``warnings``, ``sources``) because Phase 3
  introduced per-node tracing, degraded-mode warnings, and retrieval
  citations that didn't exist when DATABASE_PLAN.md was written. Per this
  phase's "do not lose any AI output" requirement, all of it is persisted.
  ``pdf_export_url`` is kept as a reserved, unused column for schema
  fidelity with DATABASE_PLAN.md -- no code in this phase populates it
  (PDF export is explicitly out of scope).
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import JSON, Column, Text
from sqlmodel import Field, SQLModel

from backend.src.db.base import new_uuid, utcnow


class AuditJobStatus(str, Enum):
    """Lifecycle states for an :class:`AuditJob`. Never leave a job in RUNNING."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    COMPLETED_DEGRADED = "completed_degraded"
    FAILED = "failed"
    CANCELLED = "cancelled"  # not settable yet; reserved so the enum is future-safe


class User(SQLModel, table=True):
    """A local user record. No authentication in this phase -- see module docstring."""

    __tablename__ = "users"

    id: UUID = Field(default_factory=new_uuid, primary_key=True)
    email: str = Field(unique=True, index=True)
    created_at: datetime = Field(default_factory=utcnow, nullable=False)


class AuditJob(SQLModel, table=True):
    """The operational record of one audit run."""

    __tablename__ = "audit_jobs"

    id: UUID = Field(default_factory=new_uuid, primary_key=True)
    user_id: Optional[UUID] = Field(default=None, foreign_key="users.id", index=True)
    video_url: str
    video_id: str
    status: str = Field(default=AuditJobStatus.QUEUED.value, index=True)
    current_stage: Optional[str] = Field(default=None)
    # TEXT rather than a default-length VARCHAR -- error messages can be
    # longer than a typical short string column comfortably holds.
    error_message: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    created_at: datetime = Field(default_factory=utcnow, nullable=False, index=True)
    updated_at: datetime = Field(default_factory=utcnow, nullable=False)
    completed_at: Optional[datetime] = Field(default=None)


class Report(SQLModel, table=True):
    """The finished (or gracefully-failed) result of one audit job."""

    __tablename__ = "reports"

    id: UUID = Field(default_factory=new_uuid, primary_key=True)
    audit_job_id: UUID = Field(foreign_key="audit_jobs.id", unique=True, index=True)

    final_status: str  # "PASS" | "FAIL"
    # The Summary Agent's Markdown narrative -- explicitly TEXT (unbounded),
    # not a default-length VARCHAR, since reports can be arbitrarily long.
    final_report: str = Field(sa_column=Column(Text, nullable=False))

    # Structured AI output, stored as JSON -- see DATABASE_PLAN.md's rationale
    # for why these are JSON blobs rather than normalized child tables.
    #
    # The four list-shaped fields are NOT NULL: every row is created through
    # ReportRepository.create_for_job(), which always supplies a (possibly
    # empty) list, so "missing" is represented as `[]`, never `NULL` --
    # matching DATABASE_PLAN.md's explicit "Not null, default []" for
    # compliance_results, extended consistently to the three JSON columns
    # Phase 3/4 added with the same "always-present list" semantics.
    # `video_metadata` is the one DATABASE_PLAN.md documents as nullable.
    compliance_results: List[Dict[str, Any]] = Field(
        default_factory=list, sa_column=Column(JSON, nullable=False)
    )
    video_metadata: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=True))
    processing_metadata: List[Dict[str, Any]] = Field(
        default_factory=list, sa_column=Column(JSON, nullable=False)
    )
    warnings: List[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    sources: List[Dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))

    confidence_score: Optional[float] = Field(default=None)
    risk_level: Optional[str] = Field(default=None)

    # Reserved for a future PDF-export phase; not populated by this phase.
    pdf_export_url: Optional[str] = Field(default=None)

    created_at: datetime = Field(default_factory=utcnow, nullable=False)
