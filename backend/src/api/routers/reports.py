"""``/api/v1/reports`` -- fetch a persisted audit report."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.api.deps import get_session
from backend.src.core.exceptions import NotFoundError
from backend.src.repositories.report_repository import ReportRepository
from backend.src.schemas.jobs import ReportRead

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


@router.get("/{report_id}", response_model=ReportRead)
async def get_report(report_id: UUID, session: AsyncSession = Depends(get_session)) -> ReportRead:
    """Fetch the full persisted report for a completed audit."""
    report = await ReportRepository(session).get(report_id)
    if report is None:
        raise NotFoundError(f"Report {report_id} was not found.")
    return ReportRead.from_report(report)
