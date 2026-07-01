"""Retrieval Agent.

Responsibilities (AI_PIPELINE_VISION.md): embed the transcript/OCR content,
retrieve the most relevant policy chunks from Azure AI Search, and hand the
Compliance Agent clean, citation-preserving context. This is the *only*
node that talks to the vector store -- Phase 2's Compliance Agent used to
do embedding + retrieval + reasoning all in one function; this phase splits
retrieval out entirely (closing PROJECT_AUDIT.md finding M12, where
retrieved-chunk source metadata was fetched and then silently discarded).

Note on "sources"/"citations": AI_PIPELINE_VISION.md asks this agent to
return ``retrieved_rules``, ``sources``, and ``citations``. Every
:class:`RetrievedRule` already carries its own ``source``, so a separate,
redundant "citations" list would just be
``sorted({r.source for r in retrieved_rules})`` -- computed on demand by
whichever node needs it (the Compliance Agent's prompt, via
``graph/prompts.py``) rather than stored as a second, easily-stale copy of
the same information in the graph state.
"""

from __future__ import annotations

from typing import Any, Dict, List

from backend.src.core.logging import get_logger
from backend.src.graph.llm_clients import get_vector_store
from backend.src.graph.observability import make_trace, start_timer
from backend.src.graph.state import VideoAuditState
from backend.src.schemas.audit import RetrievedRule

logger = get_logger(__name__)

NODE_NAME = "retrieval_agent"
_RETRIEVAL_TOP_K = 3


async def retrieval_agent(state: VideoAuditState) -> Dict[str, Any]:
    """Retrieve relevant policy chunks for this video's transcript/OCR content.

    A retrieval failure never fails the audit (AI_PIPELINE_VISION.md
    section 13: "If retrieval fails: Continue with warning."). The
    Compliance Agent is explicitly instructed (see ``graph/prompts.py``) to
    handle an empty ``retrieved_rules`` list honestly rather than inventing
    a policy citation.
    """
    t0, started_at = start_timer()
    logger.info("Retrieval agent started", extra={"video_id": state.video_id})

    try:
        vector_store = get_vector_store()

        query_text = f"{state.transcript or ''} {' '.join(state.ocr_text)}".strip()
        docs = await vector_store.asimilarity_search(query_text, k=_RETRIEVAL_TOP_K)

        retrieved_rules: List[RetrievedRule] = [
            RetrievedRule(content=doc.page_content, source=doc.metadata.get("source", "unknown"))
            for doc in docs
        ]

        logger.info(
            "Retrieval agent completed",
            extra={"video_id": state.video_id, "chunks_retrieved": len(retrieved_rules)},
        )
        return {
            "retrieved_rules": retrieved_rules,
            "retrieval_status": "success",
            "processing_metadata": [make_trace(NODE_NAME, t0, started_at, "success")],
        }

    except Exception as exc:
        logger.warning(
            "Retrieval agent failed; continuing without retrieved policies",
            extra={"video_id": state.video_id, "error": str(exc)},
        )
        return {
            "retrieved_rules": [],
            "retrieval_status": "failed",
            "warnings": [f"Policy retrieval unavailable: {exc}"],
            "processing_metadata": [make_trace(NODE_NAME, t0, started_at, "failed", error=str(exc))],
        }
