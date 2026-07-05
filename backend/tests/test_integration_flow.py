"""Lightweight end-to-end flow: create an audit, poll its status, fetch the
resulting report, then chat about it -- all through the real HTTP/routing/
repository/database stack.

The one thing not real here is the LangGraph run itself: `execute_audit_job`
is replaced with a fake that performs the exact same *observable* side
effects a real completed run has (mark running -> update stage -> mark
terminal -> persist a report), using the real `AuditRepository`/
`ReportRepository`. This exercises the true integration seam this test
cares about -- API -> background task -> repository -> database -> a
subsequent request reflects it -- without needing real Azure credentials
or re-testing the graph's own internals (out of scope: "Do NOT change
LangGraph"). The chat step mocks only the LLM call, the same as
`test_reports_api.py`.
"""

from __future__ import annotations

from types import SimpleNamespace
from uuid import UUID

import pytest
from httpx import AsyncClient

from backend.src.db.session import AsyncSessionFactory
from backend.src.repositories.audit_repository import AuditRepository
from backend.src.repositories.report_repository import ReportRepository


async def _fake_completed_run(job_id: UUID, video_url: str, video_id: str) -> None:
    """Mimics a real `execute_audit_job` run that completes with one warning finding."""
    async with AsyncSessionFactory() as session:
        audit_repo = AuditRepository(session)
        await audit_repo.mark_running(job_id)
        await audit_repo.update_stage(job_id, "Compliance Analysis")

    async with AsyncSessionFactory() as session:
        await AuditRepository(session).mark_terminal(job_id, status="completed")
        await ReportRepository(session).create_for_job(
            job_id,
            {
                "summary": "## Executive Summary\nOne warning-level finding.",
                "compliance_status": "FAIL",
                "confidence_score": 82.0,
                "risk_level": "MEDIUM",
                "violations": [
                    {
                        "category": "On-Screen Disclosure Visibility",
                        "severity": "WARNING",
                        "description": "Disclosure shown for under 3 seconds.",
                        "timestamp": None,
                        "confidence": 0.62,
                        "evidence": "Sponsored text visible ~2.1s.",
                        "policy_reference": None,
                        "recommendation": "Display the disclosure for at least 5 seconds.",
                    }
                ],
                "retrieved_rules": [],
                "processing_metadata": [],
                "warnings": [],
                "video_metadata": {"duration": 245, "platform": "youtube"},
            },
        )


@pytest.mark.asyncio
async def test_full_audit_to_chat_flow(client: AsyncClient, monkeypatch, video_id: str) -> None:
    monkeypatch.setattr("backend.src.api.routers.audits.execute_audit_job", _fake_completed_run)

    # 1. Create the audit.
    create_response = await client.post("/api/v1/audits", json={"video_url": "https://youtu.be/abc123"})
    assert create_response.status_code == 202
    job_id = create_response.json()["id"]

    # 2. Poll its status -- by now the (fake, but real-code-path) background
    #    job has already run to completion.
    status_response = await client.get(f"/api/v1/audits/{job_id}")
    assert status_response.status_code == 200
    status_body = status_response.json()
    assert status_body["status"] == "completed"
    assert status_body["report_id"] is not None
    report_id = status_body["report_id"]

    # 3. Retrieve the resulting report.
    report_response = await client.get(f"/api/v1/reports/{report_id}")
    assert report_response.status_code == 200
    report_body = report_response.json()
    assert report_body["final_status"] == "FAIL"
    assert report_body["risk_level"] == "MEDIUM"
    assert report_body["compliance_results"][0]["category"] == "On-Screen Disclosure Visibility"

    # 4. Chat about the finished report (mocked LLM only -- no real Azure call).
    class _FakeLLM:
        async def ainvoke(self, messages):
            return SimpleNamespace(content="This report has one warning-level finding.")

    monkeypatch.setattr(
        "backend.src.services.report_chat.get_chat_llm", lambda temperature: _FakeLLM()
    )
    chat_response = await client.post(
        f"/api/v1/reports/{report_id}/chat",
        json={"message": "Summarize this report.", "conversation": []},
    )
    assert chat_response.status_code == 200
    assert "warning-level finding" in chat_response.json()["reply"]

    # Also present in the plain audit list.
    list_response = await client.get("/api/v1/audits")
    assert job_id in [job["id"] for job in list_response.json()]


@pytest.mark.asyncio
async def test_failed_run_still_persists_a_degraded_report(
    client: AsyncClient, monkeypatch, video_id: str
) -> None:
    """Mirrors the real pipeline's graceful-degradation contract (see
    jobs/audit_runner.py): a job can be `status=failed` and still have a
    report explaining what went wrong, rather than the client seeing nothing."""

    async def _fake_failed_run(job_id: UUID, video_url: str, vid: str) -> None:
        async with AsyncSessionFactory() as session:
            await AuditRepository(session).mark_running(job_id)
        async with AsyncSessionFactory() as session:
            await AuditRepository(session).mark_terminal(
                job_id, status="failed", error_message="Transcript extraction failed: boom"
            )
            await ReportRepository(session).create_for_job(
                job_id,
                {
                    "summary": "Audit skipped because video processing failed (No Transcript).",
                    "compliance_status": None,
                    "violations": [],
                    "retrieved_rules": [],
                },
            )

    monkeypatch.setattr("backend.src.api.routers.audits.execute_audit_job", _fake_failed_run)

    create_response = await client.post("/api/v1/audits", json={"video_url": "https://youtu.be/broken"})
    job_id = create_response.json()["id"]

    status_response = await client.get(f"/api/v1/audits/{job_id}")
    status_body = status_response.json()
    assert status_body["status"] == "failed"
    assert status_body["error_message"] == "Transcript extraction failed: boom"
    assert status_body["report_id"] is not None

    report_response = await client.get(f"/api/v1/reports/{status_body['report_id']}")
    assert report_response.status_code == 200
    assert report_response.json()["final_status"] == "FAIL"
    assert report_response.json()["confidence_score"] is None
