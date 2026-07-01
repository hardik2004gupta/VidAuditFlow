"""Transcript Agent.

Responsibilities (AI_PIPELINE_VISION.md): download the source video, upload
it to Azure Video Indexer, wait for processing, and extract the transcript.

The download+upload+poll sequence is the single expensive step this
pipeline performs, and the OCR Agent needs the exact same result (Azure
Video Indexer returns transcript and OCR from one indexing job). This
module exposes :func:`fetch_raw_video_insights` specifically so
``ocr_agent.py`` can share it via the single-flight coordinator in
``graph/coordination.py`` -- whichever of the two agents' node functions
happens to run first performs the real fetch; the other reuses its result.
Neither agent duplicates the Azure work.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any, Dict

from backend.src.core.logging import get_logger
from backend.src.graph.coordination import video_indexer_fetch_group
from backend.src.graph.observability import make_trace, start_timer
from backend.src.graph.state import VideoAuditState
from backend.src.services.video_indexer import VideoIndexerService
from backend.src.services.youtube import download_youtube_video

logger = get_logger(__name__)

NODE_NAME = "transcript_agent"


async def fetch_raw_video_insights(video_url: str, video_name: str) -> Dict[str, Any]:
    """Download the video and run it through Azure Video Indexer once.

    Shared, single-flight-coordinated entry point used by both the
    Transcript Agent and the OCR Agent -- see the module docstring.
    """
    with tempfile.TemporaryDirectory(prefix="vidauditflow_") as tmp_dir:
        local_path = await download_youtube_video(video_url, Path(tmp_dir))
        vi_service = VideoIndexerService()
        return await vi_service.fetch_insights(local_path, video_name=video_name)
        # The TemporaryDirectory (and the downloaded video inside it) is
        # removed automatically on exiting this `with` block.


async def transcript_agent(state: VideoAuditState) -> Dict[str, Any]:
    """Populate ``transcript`` and shared ``video_metadata`` from Azure Video Indexer.

    Retries for transient Azure/network failures already happen inside
    ``VideoIndexerService`` (bounded ``tenacity`` retries on HTTP calls,
    bounded polling). This node's own try/except only handles the terminal
    outcome: success, or a failure that should fail the whole audit (per
    AI_PIPELINE_VISION.md section 13, a failed transcript fails the audit --
    there is nothing to analyze without it).
    """
    t0, started_at = start_timer()
    logger.info("Transcript agent started", extra={"video_id": state.video_id})

    try:
        raw_insights = await video_indexer_fetch_group.run(
            state.video_id,
            lambda: fetch_raw_video_insights(state.video_url, state.video_id),
        )
        transcript = VideoIndexerService.extract_transcript(raw_insights)
        video_metadata = VideoIndexerService.extract_video_metadata(raw_insights)

        logger.info("Transcript agent completed", extra={"video_id": state.video_id})
        return {
            "transcript": transcript,
            "transcript_status": "success",
            "video_metadata": video_metadata,
            "processing_metadata": [make_trace(NODE_NAME, t0, started_at, "success")],
        }

    except Exception as exc:
        logger.error("Transcript agent failed", extra={"video_id": state.video_id, "error": str(exc)})
        return {
            "transcript": "",
            "transcript_status": "failed",
            "errors": [f"Transcript extraction failed: {exc}"],
            "processing_metadata": [make_trace(NODE_NAME, t0, started_at, "failed", error=str(exc))],
        }
