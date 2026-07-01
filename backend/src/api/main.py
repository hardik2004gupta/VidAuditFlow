"""FastAPI application for VidAuditFlow.

To run:

    uv run uvicorn backend.src.api.main:app --reload

Access points:
    API docs:      http://localhost:8000/docs
    Health:        http://localhost:8000/health
    Audit (async): POST http://localhost:8000/api/v1/audits
    Audit (sync):  POST http://localhost:8000/audit  (backward-compatible, see below)

Phase 4 adds persistence and background execution (DATABASE_PLAN.md /
BACKEND_VISION.md) without changing the LangGraph pipeline or its AI
behavior. The original synchronous ``POST /audit`` endpoint is kept
working exactly as before for backward compatibility -- it now runs
through the same ``jobs.audit_runner.execute_audit_job`` function the new
async endpoints use (awaited inline instead of backgrounded), so every
audit, old endpoint or new, is persisted.
"""

from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager
from typing import Any, Dict

from dotenv import load_dotenv

# Must happen before importing any module that reads configuration.
load_dotenv(override=True)

from fastapi import FastAPI, HTTPException, Request  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402

from backend.src.api.routers import audits, reports  # noqa: E402
from backend.src.api.telemetry import setup_telemetry  # noqa: E402
from backend.src.core.config import settings  # noqa: E402
from backend.src.core.exceptions import (  # noqa: E402
    NotFoundError,
    ValidationError,
    VidAuditFlowError,
)
from backend.src.core.logging import get_logger, set_request_id  # noqa: E402
from backend.src.db.migrations import run_migrations  # noqa: E402
from backend.src.db.session import AsyncSessionFactory, engine  # noqa: E402
from backend.src.jobs.audit_runner import execute_audit_job  # noqa: E402
from backend.src.repositories.audit_repository import AuditRepository  # noqa: E402
from backend.src.repositories.report_repository import ReportRepository  # noqa: E402
from backend.src.schemas.audit import AuditRequest, AuditResponse  # noqa: E402

setup_telemetry()

logger = get_logger(__name__)

_START_TIME = time.monotonic()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown hook.

    Startup only auto-runs migrations in `local` -- see DATABASE_PLAN.md's
    migration strategy and `db/migrations.py`'s docstring. Production
    deploys run `alembic upgrade head` as an explicit pre-deploy step.

    Shutdown disposes the database engine's connection pool cleanly
    instead of leaving open connections for process exit to reap.
    """
    if settings.environment == "local":
        await run_migrations()
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    description="API for auditing video content against brand compliance rules.",
    version=settings.app_version,
    lifespan=lifespan,
)

app.include_router(audits.router)
app.include_router(reports.router)


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


@app.exception_handler(NotFoundError)
async def handle_not_found_error(request: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={"error": {"code": "not_found", "message": str(exc)}},
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
    """Trigger the compliance audit workflow for a YouTube video (backward-compatible).

    Kept working exactly as it did before Phase 4: synchronous request/
    response, identical shape. Internally, it now creates a persisted
    ``AuditJob``/``Report`` pair by awaiting the same
    ``jobs.audit_runner.execute_audit_job`` the new ``POST /api/v1/audits``
    endpoint schedules in the background -- so every audit is now part of
    persistent history, regardless of which endpoint triggered it. New
    integrations should prefer ``POST /api/v1/audits`` (returns
    immediately; see ``api/routers/audits.py``).
    """
    session_id = str(uuid.uuid4())
    video_id_short = f"vid_{session_id[:8]}"

    logger.info(
        "Received audit request",
        extra={"video_url": request.video_url, "session_id": session_id},
    )

    async with AsyncSessionFactory() as session:
        job = await AuditRepository(session).create(video_url=request.video_url, video_id=video_id_short)

    try:
        await execute_audit_job(job.id, job.video_url, job.video_id)
    except Exception as exc:
        logger.exception("Audit workflow failed unexpectedly")
        raise HTTPException(
            status_code=500,
            detail="Workflow execution failed unexpectedly. Please try again.",
        ) from exc

    async with AsyncSessionFactory() as session:
        refreshed_job = await AuditRepository(session).get(job.id)
        report = await ReportRepository(session).get_by_job_id(job.id)

    if report is not None:
        return AuditResponse(
            session_id=session_id,
            video_id=video_id_short,
            status=report.final_status,
            final_report=report.final_report,
            compliance_results=report.compliance_results,
        )

    # No report was persisted -- execute_audit_job hit an unexpected error
    # before the graph ever reached the Summary Agent (see
    # jobs/audit_runner.py's except-block). Degrade gracefully with the
    # job's own recorded error, matching the original endpoint's behavior
    # of never raising for a pipeline-level failure.
    return AuditResponse(
        session_id=session_id,
        video_id=video_id_short,
        status="FAIL",
        final_report=(refreshed_job.error_message if refreshed_job else None) or "No report generated.",
        compliance_results=[],
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
