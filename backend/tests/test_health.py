"""GET /health -- the one unauthenticated, dependency-free endpoint."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_returns_200_with_expected_shape(client: AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["service"]
    assert "version" in body
    assert "uptime_seconds" in body
