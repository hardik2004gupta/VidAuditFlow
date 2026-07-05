"""``/api/v1/reports`` -- fetch a persisted audit report, and chat about it."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.api.deps import get_session
from backend.src.core.exceptions import NotFoundError
from backend.src.core.logging import get_logger
from backend.src.repositories.report_repository import ReportRepository
from backend.src.schemas.jobs import ReportRead
from backend.src.services.report_chat import ChatMessageRequest, ChatMessageResponse, generate_chat_reply

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


@router.get("/{report_id}", response_model=ReportRead)
async def get_report(report_id: UUID, session: AsyncSession = Depends(get_session)) -> ReportRead:
    """Fetch the full persisted report for a completed audit."""
    report = await ReportRepository(session).get(report_id)
    if report is None:
        raise NotFoundError(f"Report {report_id} was not found.")
    return ReportRead.from_report(report)


@router.post("/{report_id}/chat", response_model=ChatMessageResponse)
async def chat_with_report(
    report_id: UUID,
    request: ChatMessageRequest,
    session: AsyncSession = Depends(get_session),
) -> ChatMessageResponse:
    """AI Copilot: answer a question about this specific report.

    Stateless -- ``request.conversation`` is the client's own transcript
    (nothing is persisted here), and every fact the assistant can reference
    comes from this one report row. See ``services/report_chat.py``.
    """
    report = await ReportRepository(session).get(report_id)
    if report is None:
        raise NotFoundError(f"Report {report_id} was not found.")

    logger.info(
        "Report chat request received",
        extra={"report_id": str(report_id), "conversation_turns": len(request.conversation)},
    )
    reply = await generate_chat_reply(report, request.message, request.conversation)
    return ChatMessageResponse(reply=reply)
