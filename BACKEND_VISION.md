# BACKEND_VISION.md
## VidAuditFlow — Target Backend Architecture

Guiding principle: **one FastAPI service, fully async, boringly conventional.** Everything in this document is deliberately simple — the goal is a backend that reads clearly top-to-bottom, not one that demonstrates every possible pattern.

---

## Folder Responsibilities

(Full tree in `FOLDER_STRUCTURE_V2.md`; this section explains the *why* behind the backend half.)

- **`api/main.py`** — the only file that constructs `FastAPI()`. Registers CORS, a request-ID middleware, exception handlers, and mounts each router. If you can't find where the app is assembled, you're not looking at this file — that's the bug.
- **`api/deps.py`** — every reusable `Depends()` callable: `get_settings`, `get_db`, `get_current_user`. Routers import from here; they never construct a DB session or parse a JWT themselves.
- **`api/routers/*.py`** — one router per resource (`audits`, `chat`, `reports`, `health`). A router function's body should read like a short paragraph: validate input (Pydantic did this already), call a service/job function, return a response model. If a router function is more than ~20 lines, logic belongs in `services/` or `jobs/` instead.
- **`core/config.py`** — a single Pydantic `BaseSettings` subclass. This is the *only* place `os.getenv` appears anywhere in the backend. Closes the audit finding that env-var access was scattered across `nodes.py`, `server.py`, and `index_documents.py` with inconsistent defaults.
- **`core/logging.py`** — one `setup_logging()` called once at startup from `main.py`. Closes the audit finding of three competing `logging.basicConfig()` calls.
- **`core/security.py`** — Supabase JWT verification (signature + expiry check against Supabase's JWKS), returning a typed `AuthenticatedUser`. Nothing else in the app touches JWTs directly.
- **`db/models.py`** — SQLModel classes are the single source of truth for both the database schema and (where suitable) the API's read models — see `DATABASE_PLAN.md`.
- **`db/session.py`** — one `get_session()` generator, engine created once from `settings.database_url`. SQLite locally, Supabase Postgres in prod, same code path either way.
- **`schemas/*.py`** — Pydantic models for anything that isn't a direct DB row: request bodies, composite response shapes, and the LangGraph state's `ComplianceIssue`/`AuditResult` types. This is the fix for the audit's "`ComplianceIssue` defined twice" finding — one definition, imported by both `graph/state.py` and `api/routers/audits.py`.
- **`graph/`** — the LangGraph pipeline (detailed in `AI_PIPELINE_VISION.md`). Routers and `jobs/` never call Azure SDKs directly — they call the compiled graph.
- **`services/*.py`** — one thin, typed, **async** class or module per external dependency (Video Indexer, yt-dlp, Azure AI Search, Supabase Storage, PDF export). Graph nodes call services; services never import from `graph/` or `api/` (one-directional dependency flow, easy to reason about, easy to mock in tests).
- **`jobs/audit_runner.py`** — the bridge between "an HTTP request created a row" and "the graph is now running in the background." Owns: submitting the background task, updating `audit_jobs.status` as the graph progresses, capturing exceptions into the job row instead of letting them vanish into an unobserved background task.

---

## API Architecture

- **Style:** REST, resource-oriented, versioned under `/api/v1`. Full endpoint-by-endpoint detail lives in `API_PLAN.md`; this section covers architectural conventions.
- **Request lifecycle:** `Router → Depends(get_current_user) → Depends(get_db) → service/job call → Pydantic response model`. No router function talks to Azure SDKs, `httpx`, or the DB session's raw queries directly — always through a `services/`-layer function.
- **Async everywhere.** Every route is `async def`. Every outbound HTTP call (Azure Video Indexer, Azure AI Search, Azure OpenAI, Supabase) uses an async client (`httpx.AsyncClient`, async SDK variants where available). This closes audit finding C1 permanently, not just at the one call site that triggered the original finding.
- **Long-running work is never awaited inline in a request handler.** `POST /api/v1/audits` creates a DB row, schedules the graph run via `BackgroundTasks` (or a minimal in-process asyncio task registry if more control over cancellation is needed), and returns `202 Accepted` immediately with the job id. The client polls `GET /api/v1/audits/{id}` for status.
- **No queue/broker.** At this scale (single backend instance, seconds-to-minutes-per-job, portfolio-level traffic), an external queue (Celery/Redis/RabbitMQ/SQS) would be pure overengineering — explicitly called out as a Non-Goal in `MODERNIZATION_PLAN.md`. In-process background tasks are the correct-sized tool here.

---

## Error Handling

- **A single exception-handling philosophy:** raise a small set of custom exceptions (`NotFoundError`, `ValidationError`, `ExternalServiceError`, `Unauthorized`) from services/jobs; one FastAPI exception handler per type in `main.py` maps each to the right HTTP status and a consistent JSON error shape: `{"error": {"code": "...", "message": "..."}}`.
- **Never leak raw exception text to clients** — closes the audit's Medium finding that `HTTPException(detail=f"...{str(e)}")` echoed internal error strings. Internally, the full exception (with traceback) is logged with a request-id; externally, the client sees a stable, generic message plus an error code they can reference when reporting an issue.
- **Per-node failure isolation in the graph:** each LangGraph node catches its own external-call exceptions and returns a partial-failure state update (e.g., `transcript_status: "failed"`) rather than raising — the supervisor decides whether a partial failure (e.g., OCR failed but transcript succeeded) still allows the pipeline to proceed with reduced confidence, versus a total failure that must stop the run. Detailed per-node behavior in `AI_PIPELINE_VISION.md`.
- **Retry policy:** LangGraph's native `RetryPolicy` (or a small manual retry-with-backoff wrapper in `services/`) applied to nodes making external calls, capped at 2–3 attempts with exponential backoff — closes audit finding M7.
- **Timeouts on every outbound call**, no exceptions — closes audit finding M3. A sensible default (e.g., 30s for LLM calls, 10s for token/status calls) is defined once in `core/config.py` and passed to every client.

---

## Logging

- **Structured JSON logs** (via `structlog` or Python's standard `logging` with a JSON formatter) — every log line carries `request_id`, `user_id` (if authenticated), and `job_id` (if applicable) as fields, not string-interpolated into the message.
- **One logger hierarchy**, named by module path (`vidauditflow.api.audits`, `vidauditflow.graph.compliance_agent`, `vidauditflow.services.video_indexer`) instead of the audit's five inconsistent, flat logger names (`brand-guardian`, `api-server`, `video-indexer`, etc.) — closes audit findings L1/L2.
- **Log levels used deliberately:** `INFO` for pipeline stage transitions and request lifecycle events (the events a demo/ops person actually wants to see), `WARNING` for recovered failures (a retry succeeded, telemetry disabled), `ERROR` for anything that surfaced to the user as a failure, `DEBUG` reserved for local development only (never enabled in the deployed environment by default).
- **Azure Monitor + LangSmith both receive real signal**, not just an env-var toggle: `core/logging.py` explicitly logs (at startup) whether each observability integration is active, and the graph's LangSmith run URLs are captured alongside the job row so a developer can jump straight from a failed job to its trace.

---

## Dependency Injection

FastAPI's built-in `Depends()` system is the *only* DI mechanism used — no additional DI framework. Concretely:

```
get_settings()      -> Settings              (cached, one instance per process)
get_db()             -> Session               (one per request, closed after)
get_current_user()   -> AuthenticatedUser     (verifies Supabase JWT via core/security.py)
get_video_indexer()  -> VideoIndexerService   (constructed once, reused; holds no per-request state)
get_vector_store()   -> VectorStoreService    (same pattern)
```

Services that are safe to share across requests (stateless API clients) are constructed once at startup and injected as singletons; anything per-request (the DB session, the current user) is created fresh per request via `Depends()`. This keeps the mental model simple: **singleton for "a client," fresh for "a request."**

---

## Configuration

- **One `Settings` class** (`core/config.py`), subclassing `pydantic_settings.BaseSettings`, loading from environment variables (and `.env` locally via `python-dotenv`/Pydantic's built-in `.env` support).
- **Every setting is typed and either required or has an explicit, documented default** — no more of the audit's inconsistency where `AZURE_VI_NAME` had a hardcoded fallback while `AZURE_OPENAI_API_VERSION` had none.
- **Fails fast at startup**, not at first use: if a required setting (e.g., `AZURE_OPENAI_ENDPOINT`) is missing, the app refuses to start with a clear message, rather than the audited behavior of failing deep inside a node function mid-request.
- **Environment-aware:** a single `ENVIRONMENT` variable (`local` / `production`) switches `DATABASE_URL` defaults (SQLite file path vs. Supabase Postgres URL) and log verbosity, without needing separate config files per environment.

## Environment Variables (target set)

| Variable | Purpose | Required |
|---|---|---|
| `ENVIRONMENT` | `local` \| `production` | Yes (defaults `local`) |
| `DATABASE_URL` | SQLite path (dev) or Supabase Postgres connection string (prod) | Yes |
| `AZURE_OPENAI_API_KEY` / `AZURE_OPENAI_ENDPOINT` / `AZURE_OPENAI_API_VERSION` | LLM + embeddings | Yes |
| `AZURE_OPENAI_CHAT_DEPLOYMENT` / `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` | Deployment names (no hardcoded fallback in code — closes audit M2) | Yes |
| `AZURE_SEARCH_ENDPOINT` / `AZURE_SEARCH_API_KEY` / `AZURE_SEARCH_INDEX_NAME` | RAG vector store | Yes |
| `AZURE_VI_ACCOUNT_ID` / `AZURE_VI_LOCATION` / `AZURE_SUBSCRIPTION_ID` / `AZURE_RESOURCE_GROUP` / `AZURE_VI_NAME` | Video Indexer | Yes |
| `SUPABASE_URL` / `SUPABASE_SERVICE_ROLE_KEY` | Auth verification + Storage | Yes |
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | Azure Monitor | No (feature disabled gracefully if absent) |
| `LANGCHAIN_TRACING_V2` / `LANGCHAIN_API_KEY` / `LANGCHAIN_PROJECT` | LangSmith | No (feature disabled gracefully if absent) |
| `CORS_ALLOWED_ORIGINS` | Frontend origin(s) allowed to call the API | Yes |
| `MAX_AUDITS_PER_USER_PER_DAY` | Simple quota to protect Azure spend | No (sane default) |

`.env.example` in the repo root documents every one of these with a blank/placeholder value — the actual `.env` is git-ignored (closes audit C2).

---

## Validation & Typed Models

- **Pydantic v2 everywhere data crosses a boundary**: HTTP request bodies, HTTP response bodies, and — critically — **LLM output**. The Compliance Agent's structured output is parsed via a Pydantic model (`ComplianceAnalysisResult`) using LangChain's `.with_structured_output()` (or manual `model_validate_json()` with a repair-retry step), not raw `json.loads()` — closes audit finding M5.
- **SQLModel classes double as the DB schema and, where the shape matches, the read-response model** — reducing (not eliminating) the duplication between "DB row" and "API response," while request-only shapes (e.g., `AuditCreateRequest`) stay plain Pydantic in `schemas/`.
- **URL validation:** `AuditCreateRequest.video_url` uses a Pydantic validator that real-parses the URL (`urllib.parse`) and checks the host against an explicit allow-list (`youtube.com`, `youtu.be`, `www.youtube.com`) rather than the audited substring check — closes the soft-SSRF finding.

---

## Background Tasks

- **Mechanism:** FastAPI's built-in `BackgroundTasks` for the common case (fire the audit graph, update the job row on completion/failure). If finer-grained control is later needed (cancellation, concurrent-job caps per user), a minimal `asyncio.create_task` registry inside `jobs/audit_runner.py` is the escalation path — still no external broker.
- **Job lifecycle states:** `queued → running → {stage name} → completed | failed`. Each transition is written to the `audit_jobs.status` column (see `DATABASE_PLAN.md`) so `GET /api/v1/audits/{id}` always reflects current truth without needing an in-memory cache.
- **Idempotency:** re-submitting the same `video_url` while a job is already `running` for that user returns the existing job instead of starting a duplicate — cheap protection against double-submission from an impatient double-click, and a direct fix for the audited race-condition risk (C3) at the product level, not just the file-naming level.
- **Concurrency cap:** a simple in-memory (or DB-backed, if multiple backend instances are ever run) counter limiting concurrent running jobs per user (e.g., 1 at a time) — enough to prevent one user from accidentally starting five simultaneous multi-minute Azure Video Indexer jobs.
