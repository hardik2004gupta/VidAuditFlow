"""``/api/v1/audits`` -- create and inspect background audit jobs.

Per BACKEND_VISION.md's router convention, each function here is a short
paragraph: validate input (Pydantic already did), call the repository/job
layer, return a typed response model. The actual pipeline execution lives
in ``jobs/audit_runner.py``; this file only schedules it and reads back
job state.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.api.deps import get_session
from backend.src.core.exceptions import NotFoundError
from backend.src.core.logging import get_logger
from backend.src.db.models import AuditJob, AuditJobStatus
from backend.src.jobs.audit_runner import execute_audit_job
from backend.src.repositories.audit_repository import AuditRepository
from backend.src.repositories.report_repository import ReportRepository
from backend.src.schemas.jobs import AuditJobCreate, AuditJobRead

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/audits", tags=["audits"])


async def _build_job_read(session: AsyncSession, job: AuditJob) -> AuditJobRead:
    """Attach the job's report id (if one exists yet) to the response DTO."""
    report = await ReportRepository(session).get_by_job_id(job.id)
    return AuditJobRead.from_job(job, report_id=report.id if report else None)


@router.post("", response_model=AuditJobRead, status_code=202)
async def create_audit(
    request: AuditJobCreate,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session),
) -> AuditJobRead:
    """Create an audit job and schedule it to run in the background.

    Returns immediately with the job in ``queued`` status; the caller
    polls ``GET /api/v1/audits/{id}`` for progress.
    """
    video_id = f"vid_{uuid4().hex[:8]}"
    job = await AuditRepository(session).create(video_url=request.video_url, video_id=video_id)

    logger.info("Audit job created", extra={"job_id": str(job.id), "video_url": request.video_url})

    background_tasks.add_task(execute_audit_job, job.id, job.video_url, job.video_id)

    return await _build_job_read(session, job)


@router.get("", response_model=List[AuditJobRead])
async def list_audits(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status: Optional[AuditJobStatus] = None,
    session: AsyncSession = Depends(get_session),
) -> List[AuditJobRead]:
    """List audit jobs, newest first.

    ``status``, when given, is validated against the real
    :class:`AuditJobStatus` values (FastAPI rejects anything else with a
    422) rather than silently matching zero rows for a typo'd filter.
    """
    status_value = status.value if status is not None else None
    jobs = await AuditRepository(session).list(status=status_value, limit=limit, offset=offset)

    # One batch lookup instead of one `get_by_job_id` query per job --
    # avoids an N+1 query pattern as the list grows.
    report_ids_by_job = await ReportRepository(session).get_report_ids_by_job_id([job.id for job in jobs])
    return [AuditJobRead.from_job(job, report_id=report_ids_by_job.get(job.id)) for job in jobs]


@router.get("/{job_id}", response_model=AuditJobRead)
async def get_audit(job_id: UUID, session: AsyncSession = Depends(get_session)) -> AuditJobRead:
    """Fetch a single job's current status -- the endpoint a live-tracker UI polls."""
    job = await AuditRepository(session).get(job_id)
    if job is None:
        raise NotFoundError(f"Audit job {job_id} was not found.")
    return await _build_job_read(session, job)
