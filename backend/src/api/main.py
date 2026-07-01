"""FastAPI application for VidAuditFlow.

Renamed from ``server.py`` to ``main.py`` to match the planned application
factory layout in FOLDER_STRUCTURE_V2.md. To run:

    uv run uvicorn backend.src.api.main:app --reload

Access points:
    API docs: http://localhost:8000/docs
    Health:   http://localhost:8000/health
    Audit:    POST http://localhost:8000/audit
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Dict

from dotenv import load_dotenv

# Must happen before importing any module that reads configuration.
load_dotenv(override=True)

from fastapi import FastAPI, HTTPException, Request  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402

from backend.src.api.telemetry import setup_telemetry  # noqa: E402
from backend.src.core.config import settings  # noqa: E402
from backend.src.core.exceptions import ValidationError, VidAuditFlowError  # noqa: E402
from backend.src.core.logging import get_logger, set_request_id  # noqa: E402
from backend.src.graph.workflow import app as compliance_graph  # noqa: E402
from backend.src.schemas.audit import AuditRequest, AuditResponse  # noqa: E402

setup_telemetry()

logger = get_logger(__name__)

_START_TIME = time.monotonic()

app = FastAPI(
    title=settings.app_name,
    description="API for auditing video content against brand compliance rules.",
    version=settings.app_version,
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """Bind a request id (from the caller or freshly generated) for the request's lifetime.

    Every log line emitted while handling this request will carry the same
    ``request_id``, and it is echoed back via the ``X-Request-ID`` response
    header for client-side correlation.
    """
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    set_request_id(request_id)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(ValidationError)
async def handle_validation_error(request: Request, exc: ValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={"error": {"code": "validation_error", "message": str(exc)}},
    )


@app.exception_handler(VidAuditFlowError)
async def handle_app_error(request: Request, exc: VidAuditFlowError) -> JSONResponse:
    """Fallback handler for every other application-raised error.

    Never echoes raw internal exception text as the *only* signal to the
    caller's advantage over a stack trace -- the message is still
    domain-specific (e.g. "YouTube download failed: ...") but does not leak
    Python-level internals.
    """
    logger.error("Application error", extra={"error": str(exc), "error_type": type(exc).__name__})
    return JSONResponse(
        status_code=502,
        content={"error": {"code": "upstream_error", "message": str(exc)}},
    )


@app.post("/audit", response_model=AuditResponse)
async def audit_video(request: AuditRequest) -> AuditResponse:
    """Trigger the compliance audit workflow for a YouTube video.

    The LangGraph nodes are designed to catch their own external failures
    and return a ``FAIL`` state rather than raising (see ``graph/nodes.py``),
    so this endpoint's ``try/except`` is a defensive backstop for truly
    unexpected errors, not the primary error path.
    """
    session_id = str(uuid.uuid4())
    video_id_short = f"vid_{session_id[:8]}"

    logger.info(
        "Received audit request",
        extra={"video_url": request.video_url, "session_id": session_id},
    )

    initial_state: Dict[str, Any] = {
        "video_url": request.video_url,
        "video_id": video_id_short,
        "compliance_results": [],
        "errors": [],
    }

    try:
        final_state = await compliance_graph.ainvoke(initial_state)
    except Exception as exc:
        logger.exception("Audit workflow failed unexpectedly")
        raise HTTPException(
            status_code=500,
            detail="Workflow execution failed unexpectedly. Please try again.",
        ) from exc

    return AuditResponse(
        session_id=session_id,
        video_id=final_state.get("video_id", video_id_short),
        status=final_state.get("final_status", "UNKNOWN"),
        final_report=final_state.get("final_report", "No report generated."),
        compliance_results=final_state.get("compliance_results", []),
    )


@app.get("/health")
def health_check() -> Dict[str, Any]:
    """Liveness/readiness probe.

    Returns service status, version, process uptime, and the running
    environment -- useful for confirming which build is deployed and for
    load balancer/uptime checks.
    """
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "uptime_seconds": round(time.monotonic() - _START_TIME, 2),
    }
