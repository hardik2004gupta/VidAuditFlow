"""Repository layer -- AuditRepository and ReportRepository against a real (test) database.

These use `db_session` directly (not the HTTP client) so they exercise the
data-access layer in isolation from the API/routing layer above it.
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.db.models import AuditJobStatus
from backend.src.repositories.audit_repository import AuditRepository
from backend.src.repositories.report_repository import ReportRepository


@pytest.mark.asyncio
async def test_create_audit_job_starts_queued(db_session: AsyncSession, video_id: str) -> None:
    repo = AuditRepository(db_session)
    job = await repo.create(video_url="https://youtu.be/abc123", video_id=video_id)

    assert job.id is not None
    assert job.status == AuditJobStatus.QUEUED.value
    assert job.current_stage is None
    assert job.video_id == video_id


@pytest.mark.asyncio
async def test_get_returns_none_for_unknown_job(db_session: AsyncSession) -> None:
    from uuid import uuid4

    assert await AuditRepository(db_session).get(uuid4()) is None


@pytest.mark.asyncio
async def test_status_transitions_running_then_terminal(db_session: AsyncSession, video_id: str) -> None:
    repo = AuditRepository(db_session)
    job = await repo.create(video_url="https://youtu.be/abc123", video_id=video_id)

    await repo.mark_running(job.id)
    refreshed = await repo.get(job.id)
    assert refreshed is not None
    assert refreshed.status == AuditJobStatus.RUNNING.value
    assert refreshed.completed_at is None

    await repo.update_stage(job.id, "Compliance Analysis")
    refreshed = await repo.get(job.id)
    assert refreshed is not None
    assert refreshed.current_stage == "Compliance Analysis"

    await repo.mark_terminal(job.id, status=AuditJobStatus.COMPLETED.value)
    refreshed = await repo.get(job.id)
    assert refreshed is not None
    assert refreshed.status == AuditJobStatus.COMPLETED.value
    assert refreshed.current_stage == "Completed"
    assert refreshed.completed_at is not None


@pytest.mark.asyncio
async def test_mark_failed_sets_error_message_and_failed_stage(
    db_session: AsyncSession, video_id: str
) -> None:
    repo = AuditRepository(db_session)
    job = await repo.create(video_url="https://youtu.be/abc123", video_id=video_id)

    await repo.mark_failed(job.id, error_message="Transcript extraction failed: boom")

    refreshed = await repo.get(job.id)
    assert refreshed is not None
    assert refreshed.status == AuditJobStatus.FAILED.value
    assert refreshed.current_stage == "Failed"
    assert refreshed.error_message == "Transcript extraction failed: boom"


@pytest.mark.asyncio
async def test_list_orders_newest_first_and_respects_status_filter(
    db_session: AsyncSession, video_id: str
) -> None:
    repo = AuditRepository(db_session)
    first = await repo.create(video_url="https://youtu.be/a", video_id=f"{video_id}_a")
    second = await repo.create(video_url="https://youtu.be/b", video_id=f"{video_id}_b")
    await repo.mark_failed(second.id, error_message="nope")

    all_jobs = await repo.list(limit=100)
    ids = [job.id for job in all_jobs]
    assert first.id in ids and second.id in ids
    # newest first
    assert ids.index(second.id) < ids.index(first.id)

    failed_only = await repo.list(status=AuditJobStatus.FAILED.value, limit=100)
    assert second.id in [job.id for job in failed_only]
    assert first.id not in [job.id for job in failed_only]


@pytest.mark.asyncio
async def test_report_create_for_job_persists_structured_state(
    db_session: AsyncSession, video_id: str
) -> None:
    audit_repo = AuditRepository(db_session)
    report_repo = ReportRepository(db_session)
    job = await audit_repo.create(video_url="https://youtu.be/abc123", video_id=video_id)

    final_state = {
        "summary": "## Executive Summary\nAll clear.",
        "compliance_status": "PASS",
        "confidence_score": 96.0,
        "risk_level": "LOW",
        "violations": [],
        "retrieved_rules": [{"content": "policy text", "source": "guide.pdf"}],
        "processing_metadata": [],
        "warnings": [],
        "video_metadata": {"duration": 120, "platform": "youtube"},
    }
    report = await report_repo.create_for_job(job.id, final_state)

    assert report.audit_job_id == job.id
    assert report.final_status == "PASS"
    assert report.confidence_score == 96.0
    assert report.sources == [{"content": "policy text", "source": "guide.pdf"}]

    fetched = await report_repo.get(report.id)
    assert fetched is not None
    assert fetched.id == report.id

    by_job = await report_repo.get_by_job_id(job.id)
    assert by_job is not None
    assert by_job.id == report.id


@pytest.mark.asyncio
async def test_get_report_ids_by_job_id_batches_correctly(db_session: AsyncSession, video_id: str) -> None:
    audit_repo = AuditRepository(db_session)
    report_repo = ReportRepository(db_session)
    job_with_report = await audit_repo.create(video_url="https://youtu.be/a", video_id=f"{video_id}_a")
    job_without_report = await audit_repo.create(video_url="https://youtu.be/b", video_id=f"{video_id}_b")

    await report_repo.create_for_job(
        job_with_report.id,
        {"summary": "done", "compliance_status": "PASS", "violations": [], "retrieved_rules": []},
    )

    mapping = await report_repo.get_report_ids_by_job_id([job_with_report.id, job_without_report.id])
    assert job_with_report.id in mapping
    assert job_without_report.id not in mapping
