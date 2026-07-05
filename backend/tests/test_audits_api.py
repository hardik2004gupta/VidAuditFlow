"""POST/GET /api/v1/audits, GET /api/v1/audits/{id}.

`execute_audit_job` is patched at its import site inside the router module
(`api.routers.audits.execute_audit_job`, not `jobs.audit_runner
.execute_audit_job` -- patching where a name is *used*, not where it's
*defined*) so these tests exercise the endpoint's own request/response
contract without ever invoking the real LangGraph pipeline or needing
Azure credentials. `TestClient`/`AsyncClient` runs `BackgroundTasks`
synchronously before the request call returns, so the patched fake below
has already run by the time each test makes its assertions.
"""

from __future__ import annotations

from uuid import UUID

import pytest
from httpx import AsyncClient


async def _noop_background_job(job_id: UUID, video_url: str, video_id: str) -> None:
    """Stands in for the real graph run -- does nothing, leaves the job queued."""


@pytest.mark.asyncio
async def test_create_audit_returns_202_with_queued_job(
    client: AsyncClient, monkeypatch, video_id: str
) -> None:
    monkeypatch.setattr("backend.src.api.routers.audits.execute_audit_job", _noop_background_job)

    response = await client.post("/api/v1/audits", json={"video_url": "https://youtu.be/abc123"})

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "queued"
    assert body["video_url"] == "https://youtu.be/abc123"
    assert body["report_id"] is None
    UUID(body["id"])  # well-formed UUID


@pytest.mark.asyncio
async def test_get_audit_by_id_returns_created_job(client: AsyncClient, monkeypatch) -> None:
    monkeypatch.setattr("backend.src.api.routers.audits.execute_audit_job", _noop_background_job)

    created = await client.post("/api/v1/audits", json={"video_url": "https://youtu.be/xyz789"})
    job_id = created.json()["id"]

    response = await client.get(f"/api/v1/audits/{job_id}")

    assert response.status_code == 200
    assert response.json()["id"] == job_id


@pytest.mark.asyncio
async def test_get_audit_unknown_id_returns_404(client: AsyncClient) -> None:
    response = await client.get("/api/v1/audits/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


@pytest.mark.asyncio
async def test_list_audits_includes_created_job(client: AsyncClient, monkeypatch) -> None:
    monkeypatch.setattr("backend.src.api.routers.audits.execute_audit_job", _noop_background_job)

    created = await client.post("/api/v1/audits", json={"video_url": "https://youtu.be/list-me"})
    job_id = created.json()["id"]

    response = await client.get("/api/v1/audits")

    assert response.status_code == 200
    ids = [job["id"] for job in response.json()]
    assert job_id in ids


@pytest.mark.asyncio
async def test_list_audits_status_filter_rejects_invalid_value(client: AsyncClient) -> None:
    response = await client.get("/api/v1/audits", params={"status": "not-a-real-status"})

    assert response.status_code == 422
