"""AI Copilot for compliance reports (Phase 8).

A single, isolated service: given a persisted :class:`Report` and a chat
message (plus whatever prior turns the client sends back, since nothing is
persisted server-side -- see the module-level note below), ask the existing
Azure OpenAI chat client to answer grounded *only* in that report's data.

Deliberately NOT part of the LangGraph pipeline (``graph/``) -- this runs
once, synchronously, in response to a user question, not as a pipeline
node, and reuses the pipeline's own cached LLM client (``graph.llm_clients
.get_chat_llm``) rather than constructing a second one. No RAG, no tool
calling, no memory: every fact the assistant can reference is serialized
into the prompt from the report row already fetched for this request, and
conversation history is exactly what the client included in the request
body -- this process holds no state between requests.
"""

from __future__ import annotations

from typing import List, Literal

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from backend.src.core.exceptions import ChatError
from backend.src.core.logging import get_logger
from backend.src.db.models import Report
from backend.src.graph.llm_clients import get_chat_llm
from backend.src.graph.observability import extract_token_usage

logger = get_logger(__name__)

_CHAT_TEMPERATURE = 0.2
_MAX_CONVERSATION_TURNS = 20  # generous cap; client sends full history each call


class ChatTurn(BaseModel):
    """One prior turn in the conversation, as the client remembers it."""

    role: Literal["user", "assistant"]
    content: str


class ChatMessageRequest(BaseModel):
    """Request body for ``POST /api/v1/reports/{id}/chat``."""

    message: str = Field(min_length=1, description="The user's new question.")
    conversation: List[ChatTurn] = Field(
        default_factory=list,
        description="Prior turns, oldest first. Not persisted server-side -- the client is the source of truth.",
    )


class ChatMessageResponse(BaseModel):
    """Response body for ``POST /api/v1/reports/{id}/chat``."""

    reply: str


REPORT_CHAT_SYSTEM_PROMPT = """You are the VidAuditFlow AI Copilot, embedded in a compliance report page.

Your ONLY source of truth is the report data provided below in this system message. Follow these rules strictly:

1. Answer using ONLY the information in the report context below. Do not use outside knowledge about the video, the creator, or general compliance practices beyond what's stated in the report.
2. Never fabricate a violation, policy, citation, or fact that is not present in the report context. If you reference a violation or policy, it must be one that literally appears below.
3. If the user asks something the report doesn't cover (e.g. it's not mentioned in the findings, summary, or sources), say plainly that the report doesn't contain that information -- do not guess or make something plausible up.
4. Keep responses concise: a short paragraph or a tight bullet list. Avoid restating the entire report unless the user explicitly asks for a summary.
5. You may use light Markdown (bold, bullet lists, numbered lists, short code spans) where it improves readability, but don't overuse it.
6. You are answering questions about a compliance audit, not giving legal advice -- if asked something like "am I legally liable," note that this is an automated compliance check, not legal counsel.
"""


def _format_violations(report: Report) -> str:
    if not report.compliance_results:
        return "No violations were detected in this report."
    lines = []
    for index, issue in enumerate(report.compliance_results, start=1):
        timestamp = issue.get("timestamp")
        timestamp_suffix = f" (at {timestamp})" if timestamp else ""
        confidence_pct = round((issue.get("confidence") or 0) * 100)
        lines.append(
            "\n".join(
                [
                    f"{index}. [{issue.get('severity', 'UNKNOWN')}] {issue.get('category', 'Uncategorized')}"
                    f"{timestamp_suffix} -- confidence {confidence_pct}%",
                    f"   Description: {issue.get('description', '—')}",
                    f"   Evidence: {issue.get('evidence', '—')}",
                    f"   Policy: {issue.get('policy_reference') or 'Not cited'}",
                    f"   Recommendation: {issue.get('recommendation', '—')}",
                ]
            )
        )
    return "\n".join(lines)


def _format_sources(report: Report) -> str:
    if not report.sources:
        return "No policy sources were retrieved for this report."
    return "\n".join(
        f"- ({source.get('source', 'unknown source')}) {source.get('content', '')}" for source in report.sources
    )


def _format_warnings(report: Report) -> str:
    if not report.warnings:
        return "None."
    return "\n".join(f"- {warning}" for warning in report.warnings)


def build_report_context(report: Report) -> str:
    """Serialize everything about this report the assistant is allowed to know."""
    return f"""REPORT CONTEXT
==============
Status: {report.final_status}
Risk level: {report.risk_level or "Not scored"}
Compliance score: {report.confidence_score if report.confidence_score is not None else "Not scored"}/100

--- Executive Summary (from the report) ---
{report.final_report}

--- Violations ({len(report.compliance_results)}) ---
{_format_violations(report)}

--- Policy Sources Retrieved ---
{_format_sources(report)}

--- Warnings ---
{_format_warnings(report)}
"""


def _build_messages(report: Report, message: str, conversation: List[ChatTurn]) -> List[BaseMessage]:
    system_content = f"{REPORT_CHAT_SYSTEM_PROMPT}\n{build_report_context(report)}"
    messages: List[BaseMessage] = [SystemMessage(content=system_content)]

    for turn in conversation[-_MAX_CONVERSATION_TURNS:]:
        if turn.role == "user":
            messages.append(HumanMessage(content=turn.content))
        else:
            messages.append(AIMessage(content=turn.content))

    messages.append(HumanMessage(content=message))
    return messages


async def generate_chat_reply(report: Report, message: str, conversation: List[ChatTurn]) -> str:
    """Ask the report-grounded assistant for a reply to ``message``.

    Raises :class:`ChatError` (mapped to a 502 by the existing
    ``VidAuditFlowError`` handler in ``api/main.py``) if the LLM call fails
    -- there is no deterministic fallback here, unlike the pipeline's
    Summary Agent, since a copilot reply with no LLM available has no
    meaningful substitute.
    """
    llm = get_chat_llm(temperature=_CHAT_TEMPERATURE)
    messages = _build_messages(report, message, conversation)

    try:
        response = await llm.ainvoke(messages)
    except Exception as exc:
        logger.error(
            "Report chat LLM call failed",
            extra={"report_id": str(report.id), "error": str(exc)},
        )
        raise ChatError("The AI Copilot couldn't generate a reply. Please try again.") from exc

    reply = (response.content or "").strip()
    if not reply:
        raise ChatError("The AI Copilot returned an empty reply. Please try again.")

    logger.info(
        "Report chat reply generated",
        extra={
            "report_id": str(report.id),
            "tokens_used": extract_token_usage(response),
            "conversation_turns": len(conversation),
        },
    )
    return reply
