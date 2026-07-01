"""LangGraph node functions for the video compliance audit workflow.

Two nodes, unchanged in shape from the original implementation:

    indexer  -- downloads the video, runs Azure Video Indexer, extracts
                transcript/OCR.
    auditor  -- retrieves relevant policy chunks and asks the compliance
                LLM to judge the content against them.

Both nodes are now ``async`` (so the workflow must be run via
``graph.ainvoke()``, not ``graph.invoke()``) and follow one invariant that
was already true in the original code and is preserved here: a node never
raises out of the graph. Every external failure is caught and converted into
a state update (``errors`` + ``final_status: "FAIL"``) so the workflow
always completes and returns a usable result.
"""

from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path
from typing import Any, Dict

from langchain_community.vectorstores import AzureSearch
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings

from backend.src.core.config import settings
from backend.src.core.exceptions import ComplianceError, RetrievalError
from backend.src.core.logging import get_logger
from backend.src.graph.state import VideoAuditState
from backend.src.services.video_indexer import VideoIndexerService
from backend.src.services.youtube import download_youtube_video

logger = get_logger(__name__)

_RETRIEVAL_TOP_K = 3


# --- NODE 1: THE INDEXER ---
async def index_video_node(state: VideoAuditState) -> Dict[str, Any]:
    """Download the source video and extract transcript/OCR via Azure Video Indexer.

    Uses a fresh ``tempfile.TemporaryDirectory`` per invocation so concurrent
    audits never collide on a shared filename (PROJECT_AUDIT.md finding C3).
    """
    video_url = state.get("video_url")
    video_name = state.get("video_id", "vid_demo")

    logger.info("Indexer node started", extra={"video_url": video_url})

    vi_service = VideoIndexerService()

    try:
        with tempfile.TemporaryDirectory(prefix="vidauditflow_") as tmp_dir:
            local_path = await download_youtube_video(video_url, Path(tmp_dir))
            azure_video_id = await vi_service.upload_video(local_path, video_name=video_name)
            logger.info("Upload succeeded", extra={"azure_video_id": azure_video_id})

            raw_insights = await vi_service.wait_for_processing(azure_video_id)
            clean_data = vi_service.extract_data(raw_insights)
        # The TemporaryDirectory (and the downloaded video inside it) is
        # removed automatically on exiting the `with` block, regardless of
        # success or failure.

        logger.info("Indexer node completed")
        return clean_data

    except Exception as exc:
        logger.error("Indexer node failed", extra={"error": str(exc)})
        return {
            "errors": [str(exc)],
            "final_status": "FAIL",
            "transcript": "",
            "ocr_text": [],
        }


# --- NODE 2: THE COMPLIANCE AUDITOR ---
async def audit_content_node(state: VideoAuditState) -> Dict[str, Any]:
    """Perform Retrieval-Augmented Generation (RAG) to audit the content."""
    logger.info("Auditor node started")

    transcript = state.get("transcript", "")

    if not transcript:
        logger.warning("No transcript available; skipping audit")
        return {
            "final_status": "FAIL",
            "final_report": "Audit skipped because video processing failed (No Transcript).",
        }

    llm = AzureChatOpenAI(
        azure_deployment=settings.azure_openai_chat_deployment,
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        openai_api_version=settings.azure_openai_api_version,
        temperature=0.0,
    )
    embeddings = AzureOpenAIEmbeddings(
        azure_deployment=settings.azure_openai_embedding_deployment,
        azure_endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        openai_api_version=settings.azure_openai_api_version,
    )
    vector_store = AzureSearch(
        azure_search_endpoint=settings.azure_search_endpoint,
        azure_search_key=settings.azure_search_api_key,
        index_name=settings.azure_search_index_name,
        embedding_function=embeddings.embed_query,
    )

    ocr_text = state.get("ocr_text", [])
    query_text = f"{transcript} {' '.join(ocr_text)}"

    try:
        docs = await vector_store.asimilarity_search(query_text, k=_RETRIEVAL_TOP_K)
    except Exception as exc:
        error = RetrievalError(f"Policy retrieval failed: {exc}")
        logger.error("Auditor node failed during retrieval", extra={"error": str(error)})
        return {"errors": [str(error)], "final_status": "FAIL"}

    retrieved_rules = "\n\n".join(doc.page_content for doc in docs)

    system_prompt = f"""
    You are a Senior Brand Compliance Auditor.

    OFFICIAL REGULATORY RULES:
    {retrieved_rules}

    INSTRUCTIONS:
    1. Analyze the Transcript and OCR text below.
    2. Identify ANY violations of the rules.
    3. Return strictly JSON in the following format:

    {{
        "compliance_results": [
            {{
                "category": "Claim Validation",
                "severity": "CRITICAL",
                "description": "Explanation of the violation..."
            }}
        ],
        "status": "FAIL",
        "final_report": "Summary of findings..."
    }}

    If no violations are found, set "status" to "PASS" and "compliance_results" to [].
    """

    user_message = f"""
    VIDEO METADATA: {state.get('video_metadata', {})}
    TRANSCRIPT: {transcript}
    ON-SCREEN TEXT (OCR): {ocr_text}
    """

    response = None
    try:
        response = await llm.ainvoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=user_message)]
        )

        # --- Clean Markdown fences if present (```json ... ```) ---
        content = response.content
        if "```" in content:
            match = re.search(r"```(?:json)?(.*?)```", content, re.DOTALL)
            if not match:
                raise ComplianceError("LLM response contained an unterminated code block.")
            content = match.group(1)

        audit_data = json.loads(content.strip())

        return {
            "compliance_results": audit_data.get("compliance_results", []),
            "final_status": audit_data.get("status", "FAIL"),
            "final_report": audit_data.get("final_report", "No report generated."),
        }

    except Exception as exc:
        error = ComplianceError(f"Compliance analysis failed: {exc}")
        logger.error(
            "Auditor node failed",
            extra={
                "error": str(error),
                "raw_response": response.content if response is not None else None,
            },
        )
        return {"errors": [str(error)], "final_status": "FAIL"}
