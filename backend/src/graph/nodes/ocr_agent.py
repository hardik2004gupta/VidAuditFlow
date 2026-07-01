"""OCR Agent.

Responsibilities (AI_PIPELINE_VISION.md): extract on-screen text from the
*same* Azure Video Indexer payload the Transcript Agent uses -- this agent
never triggers its own upload/poll cycle. It shares that fetch via
``graph.coordination.video_indexer_fetch_group``, keyed by ``video_id``:
whichever of the two agents' nodes reaches the shared fetch first does the
real work; this one just awaits the same result if the Transcript Agent got
there first (or performs it itself, coordinated, if it happens to run
first -- LangGraph does not guarantee ordering between parallel branches).

A failure here is never fatal to the audit (AI_PIPELINE_VISION.md section
13: "If OCR fails: Continue. Mark report: ocr_unavailable.") -- the
Supervisor's join step reads ``ocr_status`` to decide whether to mark the
run degraded.
"""

from __future__ import annotations

from typing import Any, Dict

from backend.src.core.logging import get_logger
from backend.src.graph.coordination import video_indexer_fetch_group
from backend.src.graph.nodes.transcript_agent import fetch_raw_video_insights
from backend.src.graph.observability import make_trace, start_timer
from backend.src.graph.state import VideoAuditState
from backend.src.services.video_indexer import VideoIndexerService

logger = get_logger(__name__)

NODE_NAME = "ocr_agent"


async def ocr_agent(state: VideoAuditState) -> Dict[str, Any]:
    """Populate ``ocr_text`` from the shared Azure Video Indexer payload."""
    t0, started_at = start_timer()
    logger.info("OCR agent started", extra={"video_id": state.video_id})

    try:
        raw_insights = await video_indexer_fetch_group.run(
            state.video_id,
            lambda: fetch_raw_video_insights(state.video_url, state.video_id),
        )
        ocr_text = VideoIndexerService.extract_ocr(raw_insights)

        logger.info("OCR agent completed", extra={"video_id": state.video_id, "ocr_lines": len(ocr_text)})
        return {
            "ocr_text": ocr_text,
            "ocr_status": "success",
            "processing_metadata": [make_trace(NODE_NAME, t0, started_at, "success")],
        }

    except Exception as exc:
        # Graceful degradation: OCR failing never fails the audit outright.
        logger.warning("OCR agent failed; continuing without OCR", extra={"video_id": state.video_id, "error": str(exc)})
        return {
            "ocr_text": [],
            "ocr_status": "failed",
            "warnings": [f"OCR unavailable: {exc}"],
            "processing_metadata": [make_trace(NODE_NAME, t0, started_at, "failed", error=str(exc))],
        }
