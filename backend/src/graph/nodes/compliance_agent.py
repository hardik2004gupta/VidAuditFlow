"""Compliance Agent.

Responsibilities (AI_PIPELINE_VISION.md): reasoning ONLY. Given the
transcript, OCR text, and the Retrieval Agent's already-fetched policy
chunks, produce a validated :class:`ComplianceAnalysis`. This node does not
embed anything, does not query Azure AI Search, and does not hand-parse
JSON -- it binds ``ComplianceAnalysis`` directly via
``with_structured_output()``, so a well-formed response is guaranteed to be
a valid Pydantic instance before this function ever sees it.

Retry policy: per AI_PIPELINE_VISION.md/section 12's distinction between
"transient failure" retries (network/timeouts, handled by the tenacity
retries already inside the Azure service clients) and this section 6's
"malformed LLM output" retry -- these are different situations. The same
prompt sent to a non-deterministic model can produce a differently-shaped
response on a second try, so retrying a schema-validation failure here
*is* worth doing, unlike retrying a deterministic input-validation failure
(which never changes on retry and is correctly excluded by section 12).
This node retries the LLM call at most once, with the validation error fed
back to the model, then degrades gracefully (see below) rather than
raising if the second attempt also fails.
"""

from __future__ import annotations

from typing import Any, Dict

from langchain_core.messages import HumanMessage, SystemMessage

from backend.src.core.logging import get_logger
from backend.src.graph.llm_clients import get_chat_llm
from backend.src.graph.observability import extract_token_usage, make_trace, start_timer
from backend.src.graph.prompts import COMPLIANCE_SYSTEM_PROMPT, build_compliance_context
from backend.src.graph.state import VideoAuditState
from backend.src.schemas.audit import ComplianceAnalysis

logger = get_logger(__name__)

NODE_NAME = "compliance_agent"


async def compliance_agent(state: VideoAuditState) -> Dict[str, Any]:
    """Judge the transcript/OCR content against the retrieved policies."""
    t0, started_at = start_timer()
    logger.info("Compliance agent started", extra={"video_id": state.video_id})

    if not state.transcript:
        # Defensive only: the Supervisor's conditional routing (see
        # graph/supervisor.py) sends a failed transcript straight to the
        # Summary Agent, bypassing this node entirely. This guard exists so
        # a future routing change fails loudly here instead of silently
        # calling the LLM with nothing to analyze.
        logger.warning("Compliance agent invoked with no transcript; skipping analysis")
        return {
            "warnings": ["compliance_analysis_skipped_no_transcript"],
            "processing_metadata": [make_trace(NODE_NAME, t0, started_at, "skipped")],
        }

    tokens_used = 0

    try:
        llm = get_chat_llm(temperature=0.0)
        structured_llm = llm.with_structured_output(ComplianceAnalysis, include_raw=True)

        context = build_compliance_context(
            transcript=state.transcript,
            ocr_text=state.ocr_text,
            retrieved_rules=state.retrieved_rules,
            video_metadata=state.video_metadata,
        )
        messages = [SystemMessage(content=COMPLIANCE_SYSTEM_PROMPT), HumanMessage(content=context)]

        result = await structured_llm.ainvoke(messages)
        tokens_used += extract_token_usage(result["raw"]) or 0

        if result["parsing_error"] is not None:
            logger.warning(
                "Compliance agent got malformed structured output; retrying once",
                extra={"video_id": state.video_id, "error": str(result["parsing_error"])},
            )
            retry_messages = [
                *messages,
                HumanMessage(
                    content=(
                        "Your previous response did not match the required output "
                        f"schema and could not be parsed: {result['parsing_error']}\n\n"
                        "Please respond again, strictly following the schema."
                    )
                ),
            ]
            result = await structured_llm.ainvoke(retry_messages)
            tokens_used += extract_token_usage(result["raw"]) or 0

        if result["parsing_error"] is not None or result["parsed"] is None:
            error_message = f"Compliance analysis returned malformed output twice: {result['parsing_error']}"
            logger.error(
                "Compliance agent failed after retry", extra={"video_id": state.video_id, "error": error_message}
            )
            return {
                "warnings": ["compliance_analysis_unavailable"],
                "errors": [error_message],
                "processing_metadata": [
                    make_trace(NODE_NAME, t0, started_at, "failed", error=error_message, tokens_used=tokens_used)
                ],
            }

        analysis: ComplianceAnalysis = result["parsed"]

        logger.info(
            "Compliance agent completed",
            extra={
                "video_id": state.video_id,
                "status": analysis.overall_status,
                "violation_count": len(analysis.violations),
            },
        )
        return {
            "violations": analysis.violations,
            "compliance_status": analysis.overall_status,
            "processing_metadata": [make_trace(NODE_NAME, t0, started_at, "success", tokens_used=tokens_used)],
        }

    except Exception as exc:
        # A genuine call failure (network, auth, rate limit) rather than a
        # malformed response -- degrade gracefully rather than failing the
        # whole audit, consistent with the retrieval-failure handling above.
        logger.error("Compliance agent call failed", extra={"video_id": state.video_id, "error": str(exc)})
        return {
            "warnings": ["compliance_analysis_unavailable"],
            "errors": [f"Compliance analysis failed: {exc}"],
            "processing_metadata": [
                make_trace(NODE_NAME, t0, started_at, "failed", error=str(exc), tokens_used=tokens_used)
            ],
        }
