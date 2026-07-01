"""Thin data-access layer for :class:`Report` rows.

The one non-trivial method here is :meth:`create_for_job`, which converts
the LangGraph run's final accumulated state (a plain dict whose list
fields hold Pydantic model instances -- see ``graph/state.py``) into the
JSON-serializable shape the ``reports`` table's columns expect. That
conversion is data plumbing, not business logic, so it stays here rather
than in ``jobs/audit_runner.py``.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from backend.src.db.models import Report
from backend.src.graph.adapters import resolve_external_status


def _to_plain_dict(item: Any) -> Dict[str, Any]:
    """Normalize a Pydantic model instance (or an already-plain dict) to a plain dict."""
    if isinstance(item, BaseModel):
        return item.model_dump(mode="json")
    return dict(item)


class ReportRepository:
    """CRUD operations for :class:`Report`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_for_job(self, job_id: UUID, final_state: Dict[str, Any]) -> Report:
        """Persist the graph's final state as a Report row for ``job_id``.

        Called once, after the LangGraph run finishes (successfully or in a
        gracefully-degraded way) -- see ``jobs/audit_runner.py``. Every
        piece of AI output the graph produced is captured here: the
        Summary Agent's report, score, and risk level; every violation
        with its full Phase 3 detail (confidence/evidence/policy_reference/
        recommendation); retrieval citations; per-node processing traces;
        and any degraded-mode warnings.
        """
        violations: List[Any] = final_state.get("violations", [])
        retrieved_rules: List[Any] = final_state.get("retrieved_rules", [])
        processing_metadata: List[Any] = final_state.get("processing_metadata", [])

        report = Report(
            audit_job_id=job_id,
            final_status=resolve_external_status(final_state.get("compliance_status")),
            final_report=final_state.get("summary") or "No report generated.",
            compliance_results=[_to_plain_dict(v) for v in violations],
            video_metadata=final_state.get("video_metadata") or {},
            processing_metadata=[_to_plain_dict(t) for t in processing_metadata],
            warnings=list(final_state.get("warnings", [])),
            sources=[_to_plain_dict(r) for r in retrieved_rules],
            confidence_score=final_state.get("confidence_score"),
            risk_level=final_state.get("risk_level"),
        )
        self._session.add(report)
        await self._session.commit()
        await self._session.refresh(report)
        return report

    async def get(self, report_id: UUID) -> Optional[Report]:
        return await self._session.get(Report, report_id)

    async def get_by_job_id(self, job_id: UUID) -> Optional[Report]:
        result = await self._session.execute(select(Report).where(Report.audit_job_id == job_id))
        return result.scalar_one_or_none()

    async def get_report_ids_by_job_id(self, job_ids: Sequence[UUID]) -> Dict[UUID, UUID]:
        """Batch-fetch ``{audit_job_id: report_id}`` for several jobs in one query.

        Used by ``GET /api/v1/audits`` to attach each job's ``report_id`` to
        the list response without issuing one ``get_by_job_id`` query per
        row (an N+1 query pattern for any list longer than one job).
        """
        if not job_ids:
            return {}
        result = await self._session.execute(
            select(Report.audit_job_id, Report.id).where(Report.audit_job_id.in_(job_ids))
        )
        return {row.audit_job_id: row.id for row in result.all()}
