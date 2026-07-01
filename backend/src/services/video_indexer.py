"""Azure Video Indexer client.

Handles ARM/account token exchange, uploading a local video file, polling
for indexing completion, and extracting transcript/OCR text from the
resulting insights payload.

This module was rewritten from a synchronous ``requests``-based client to
an async ``httpx``-based one (PROJECT_AUDIT.md C1/M1), with:

- explicit timeouts and bounded retries on every HTTP call (M3, M7),
- a bounded polling loop instead of an unbounded ``while True`` (C5),
- typed exceptions instead of bare ``Exception`` (see ``core/exceptions``).

The YouTube download responsibility that used to live in this class has
moved to ``services/youtube.py`` -- this class now only talks to Azure.

Phase 3 change (AI_PIPELINE_VISION.md): :meth:`fetch_insights` combines the
upload+poll steps into the one shared call both the Transcript Agent and
OCR Agent make (coalesced via ``graph/coordination.py`` so it only actually
runs once per audit). The old single ``extract_data`` helper that returned
transcript+OCR+metadata bundled together is replaced by three focused
static extractors (:meth:`extract_transcript`, :meth:`extract_ocr`,
:meth:`extract_video_metadata`) so each agent reads only what it owns.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Dict, List

import httpx
from azure.identity.aio import DefaultAzureCredential
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from backend.src.core.config import settings
from backend.src.core.exceptions import VideoIndexerError
from backend.src.core.logging import get_logger

logger = get_logger(__name__)

# Retries only on transient HTTP transport errors (timeouts, connection
# resets). Non-200 responses are treated as definitive Azure-side failures
# and raise VideoIndexerError immediately without retrying.
_retry_on_transient_http_error = retry(
    reraise=True,
    stop=stop_after_attempt(settings.http_max_retries),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(httpx.HTTPError),
)


class VideoIndexerService:
    """Thin async client around the Azure Video Indexer REST API."""

    def __init__(self) -> None:
        self.account_id = settings.azure_vi_account_id
        self.location = settings.azure_vi_location
        self.subscription_id = settings.azure_subscription_id
        self.resource_group = settings.azure_resource_group
        self.vi_name = settings.azure_vi_name
        self._timeout = settings.http_timeout_seconds

    async def _get_access_token(self) -> str:
        """Fetch an ARM access token via ``DefaultAzureCredential``.

        Auth failures are not retried -- they usually indicate a real
        credential/config problem rather than a transient blip.
        """
        try:
            async with DefaultAzureCredential() as credential:
                token = await credential.get_token("https://management.azure.com/.default")
                return token.token
        except Exception as exc:
            raise VideoIndexerError(f"Failed to acquire Azure access token: {exc}") from exc

    @_retry_on_transient_http_error
    async def _get_account_token(self, client: httpx.AsyncClient, arm_access_token: str) -> str:
        """Exchange an ARM token for a Video Indexer account token."""
        url = (
            f"https://management.azure.com/subscriptions/{self.subscription_id}"
            f"/resourceGroups/{self.resource_group}"
            f"/providers/Microsoft.VideoIndexer/accounts/{self.vi_name}"
            f"/generateAccessToken?api-version=2024-01-01"
        )
        headers = {"Authorization": f"Bearer {arm_access_token}"}
        payload = {"permissionType": "Contributor", "scope": "Account"}
        response = await client.post(url, headers=headers, json=payload, timeout=self._timeout)
        if response.status_code != 200:
            raise VideoIndexerError(f"Failed to get Video Indexer account token: {response.text}")
        return response.json().get("accessToken")

    async def _get_account_token_via_arm(self, client: httpx.AsyncClient) -> str:
        """Full token exchange: ARM token -> Video Indexer account token."""
        arm_token = await self._get_access_token()
        return await self._get_account_token(client, arm_token)

    @_retry_on_transient_http_error
    async def upload_video(self, video_path: Path, video_name: str) -> str:
        """Upload a local video file to Azure Video Indexer and return its video id."""
        async with httpx.AsyncClient() as client:
            vi_token = await self._get_account_token_via_arm(client)

            api_url = f"https://api.videoindexer.ai/{self.location}/Accounts/{self.account_id}/Videos"
            params = {
                "accessToken": vi_token,
                "name": video_name,
                "privacy": "Private",
                "indexingPreset": "Default",
            }

            file_bytes = await asyncio.to_thread(video_path.read_bytes)
            logger.info("Uploading video to Azure Video Indexer", extra={"video_name": video_name})

            response = await client.post(
                api_url,
                params=params,
                files={"file": (video_path.name, file_bytes)},
                timeout=self._timeout * 4,  # uploads take longer than typical calls
            )

        if response.status_code != 200:
            raise VideoIndexerError(f"Azure Video Indexer upload failed: {response.text}")

        return response.json().get("id")

    @_retry_on_transient_http_error
    async def _fetch_index_status(
        self, client: httpx.AsyncClient, video_id: str, vi_token: str
    ) -> Dict[str, Any]:
        """Fetch the current indexing status/insights payload for one poll iteration."""
        url = f"https://api.videoindexer.ai/{self.location}/Accounts/{self.account_id}/Videos/{video_id}/Index"
        response = await client.get(url, params={"accessToken": vi_token}, timeout=self._timeout)
        if response.status_code != 200:
            raise VideoIndexerError(f"Failed to fetch Video Indexer status: {response.text}")
        return response.json()

    async def wait_for_processing(self, video_id: str) -> Dict[str, Any]:
        """Poll Video Indexer until the video finishes processing.

        Bounded by ``settings.video_indexer_max_poll_attempts`` -- unlike the
        original ``while True`` loop, this can never hang a request forever
        (PROJECT_AUDIT.md finding C5).
        """
        logger.info("Waiting for Video Indexer processing", extra={"azure_video_id": video_id})

        async with httpx.AsyncClient() as client:
            for attempt in range(1, settings.video_indexer_max_poll_attempts + 1):
                vi_token = await self._get_account_token_via_arm(client)
                data = await self._fetch_index_status(client, video_id, vi_token)
                state = data.get("state")

                if state == "Processed":
                    return data
                if state == "Failed":
                    raise VideoIndexerError("Video indexing failed in Azure Video Indexer.")
                if state == "Quarantined":
                    raise VideoIndexerError(
                        "Video quarantined by Azure (copyright/content policy violation)."
                    )

                logger.info(
                    "Video Indexer still processing",
                    extra={"state": state, "attempt": attempt},
                )
                await asyncio.sleep(settings.video_indexer_poll_interval_seconds)

        raise VideoIndexerError(
            "Video Indexer did not finish processing within "
            f"{settings.video_indexer_max_poll_attempts} attempts."
        )

    async def fetch_insights(self, video_path: Path, video_name: str) -> Dict[str, Any]:
        """Upload the video and wait for indexing to complete.

        Returns the raw Video Indexer insights payload. This is the one
        expensive, shared step -- callers should invoke it through
        ``graph.coordination.video_indexer_fetch_group`` so two agents
        auditing the same video never trigger it twice (see that module's
        docstring for why).
        """
        azure_video_id = await self.upload_video(video_path, video_name)
        return await self.wait_for_processing(azure_video_id)

    @staticmethod
    def extract_transcript(vi_json: Dict[str, Any]) -> str:
        """Extract the full speech-to-text transcript from an insights payload."""
        lines: List[str] = []
        for video in vi_json.get("videos", []):
            insights = video.get("insights", {})
            lines.extend(item.get("text") for item in insights.get("transcript", []))
        return " ".join(lines)

    @staticmethod
    def extract_ocr(vi_json: Dict[str, Any]) -> List[str]:
        """Extract recognized on-screen text lines from an insights payload."""
        lines: List[str] = []
        for video in vi_json.get("videos", []):
            insights = video.get("insights", {})
            lines.extend(item.get("text") for item in insights.get("ocr", []))
        return lines

    @staticmethod
    def extract_video_metadata(vi_json: Dict[str, Any]) -> Dict[str, Any]:
        """Extract basic video metadata (duration, platform) from an insights payload."""
        return {
            "duration": vi_json.get("summarizedInsights", {}).get("duration", {}).get("seconds"),
            "platform": "youtube",
        }
