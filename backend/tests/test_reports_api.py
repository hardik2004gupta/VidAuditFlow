"""GET /api/v1/reports/{id} and POST /api/v1/reports/{id}/chat."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.repositories.audit_repository import AuditRepository
from backend.src.repositories.report_repository import ReportRepository


async def _seed_report(db_session: AsyncSession, video_id: str):
    job = await AuditRepository(db_session).create(video_url="https://youtu.be/abc123", video_id=video_id)
    report = await ReportRepository(db_session).create_for_job(
        job.id,
        {
            "summary": "## Executive Summary\nOne critical violation found.",
            "compliance_status": "FAIL",
            "confidence_score": 40.0,
            "risk_level": "HIGH",
            "violations": [
                {
                    "category": "Misleading Claims",
                    "severity": "CRITICAL",
                    "description": "Unsubstantiated guarantee.",
                    "timestamp": "00:32",
                    "confidence": 0.9,
                    "evidence": "I guarantee results.",
                    "policy_reference": "FTC Guide 3.2",
                    "recommendation": "Remove the guarantee language.",
                }
            ],
            "retrieved_rules": [{"content": "policy text", "source": "guide.pdf"}],
            "processing_metadata": [],
            "warnings": [],
            "video_metadata": {"duration": 245, "platform": "youtube"},
        },
    )
    return job, report


@pytest.mark.asyncio
async def test_get_report_returns_full_structured_body(
    client: AsyncClient, db_session: AsyncSession, video_id: str
) -> None:
    _job, report = await _seed_report(db_session, video_id)

    response = await client.get(f"/api/v1/reports/{report.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["final_status"] == "FAIL"
    assert body["risk_level"] == "HIGH"
    assert len(body["compliance_results"]) == 1
    assert body["compliance_results"][0]["category"] == "Misleading Claims"
    assert body["sources"][0]["source"] == "guide.pdf"


@pytest.mark.asyncio
async def test_get_report_unknown_id_returns_404(client: AsyncClient) -> None:
    response = await client.get("/api/v1/reports/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


@pytest.mark.asyncio
async def test_chat_with_report_returns_reply_from_mocked_llm(
    client: AsyncClient, db_session: AsyncSession, monkeypatch, video_id: str
) -> None:
    _job, report = await _seed_report(db_session, video_id)

    fake_response = SimpleNamespace(content="The critical violation is Misleading Claims.")

    class _FakeLLM:
        async def ainvoke(self, messages):
            # The report's grounding context must actually reach the model.
            system_content = messages[0].content
            assert "Misleading Claims" in system_content
            assert "Never fabricate" in system_content
            return fake_response

    monkeypatch.setattr(
        "backend.src.services.report_chat.get_chat_llm", lambda temperature: _FakeLLM()
    )

    response = await client.post(
        f"/api/v1/reports/{report.id}/chat",
        json={"message": "What are the critical violations?", "conversation": []},
    )

    assert response.status_code == 200
    assert response.json()["reply"] == "The critical violation is Misleading Claims."


@pytest.mark.asyncio
async def test_chat_with_report_replays_conversation_history(
    client: AsyncClient, db_session: AsyncSession, monkeypatch, video_id: str
) -> None:
    _job, report = await _seed_report(db_session, video_id)
    captured_messages = []

    class _FakeLLM:
        async def ainvoke(self, messages):
            captured_messages.extend(messages)
            return SimpleNamespace(content="Sure -- here's more detail.")

    monkeypatch.setattr(
        "backend.src.services.report_chat.get_chat_llm", lambda temperature: _FakeLLM()
    )

    response = await client.post(
        f"/api/v1/reports/{report.id}/chat",
        json={
            "message": "Can you elaborate?",
            "conversation": [
                {"role": "user", "content": "Summarize this report."},
                {"role": "assistant", "content": "It failed due to one critical violation."},
            ],
        },
    )

    assert response.status_code == 200
    # system + 2 prior turns + new user message
    assert len(captured_messages) == 4
    assert captured_messages[-1].content == "Can you elaborate?"


@pytest.mark.asyncio
async def test_chat_with_unknown_report_returns_404(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/reports/00000000-0000-0000-0000-000000000000/chat",
        json={"message": "hi", "conversation": []},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_chat_llm_failure_returns_502_upstream_error(
    client: AsyncClient, db_session: AsyncSession, monkeypatch, video_id: str
) -> None:
    _job, report = await _seed_report(db_session, video_id)

    class _FailingLLM:
        async def ainvoke(self, messages):
            raise RuntimeError("Azure is unreachable")

    monkeypatch.setattr(
        "backend.src.services.report_chat.get_chat_llm", lambda temperature: _FailingLLM()
    )

    response = await client.post(
        f"/api/v1/reports/{report.id}/chat",
        json={"message": "hi", "conversation": []},
    )

    assert response.status_code == 502
    assert response.json()["error"]["code"] == "upstream_error"
