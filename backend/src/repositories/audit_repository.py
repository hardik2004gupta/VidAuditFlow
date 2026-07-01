"""Thin data-access layer for :class:`AuditJob` rows.

Every method here is a small, direct database operation -- no orchestration
logic (deciding *when* a job should move to which state lives in
``jobs/audit_runner.py``, not here).
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from backend.src.db.base import utcnow
from backend.src.db.models import AuditJob, AuditJobStatus


class AuditRepository:
    """CRUD + status-transition operations for :class:`AuditJob`."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, *, video_url: str, video_id: str, user_id: Optional[UUID] = None) -> AuditJob:
        job = AuditJob(
            user_id=user_id,
            video_url=video_url,
            video_id=video_id,
            status=AuditJobStatus.QUEUED.value,
        )
        self._session.add(job)
        await self._session.commit()
        await self._session.refresh(job)
        return job

    async def get(self, job_id: UUID) -> Optional[AuditJob]:
        return await self._session.get(AuditJob, job_id)

    async def list(
        self,
        *,
        user_id: Optional[UUID] = None,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[AuditJob]:
        query = select(AuditJob).order_by(AuditJob.created_at.desc()).limit(limit).offset(offset)
        if user_id is not None:
            query = query.where(AuditJob.user_id == user_id)
        if status is not None:
            query = query.where(AuditJob.status == status)
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def mark_running(self, job_id: UUID) -> None:
        await self._update(job_id, status=AuditJobStatus.RUNNING.value)

    async def update_stage(self, job_id: UUID, stage: str) -> None:
        await self._update(job_id, current_stage=stage)

    async def mark_terminal(
        self,
        job_id: UUID,
        *,
        status: str,
        error_message: Optional[str] = None,
    ) -> None:
        """Move a job to a terminal state (completed / completed_degraded / failed).

        Always sets ``completed_at`` -- a job reaching this method is, by
        definition, done running, whatever the outcome.
        """
        await self._update(
            job_id,
            status=status,
            current_stage="Completed" if status != AuditJobStatus.FAILED.value else "Failed",
            error_message=error_message,
            completed_at=utcnow(),
        )

    async def mark_failed(self, job_id: UUID, *, error_message: str) -> None:
        """Convenience wrapper around :meth:`mark_terminal` for the failure path.

        Called from every error-handling branch in ``jobs/audit_runner.py``
        so a job can never be left stuck in "running".
        """
        await self.mark_terminal(job_id, status=AuditJobStatus.FAILED.value, error_message=error_message)

    async def _update(self, job_id: UUID, **fields) -> None:
        job = await self._session.get(AuditJob, job_id)
        if job is None:
            return
        for key, value in fields.items():
            setattr(job, key, value)
        job.updated_at = utcnow()
        self._session.add(job)
        await self._session.commit()
