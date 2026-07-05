# PHASE_2_SUMMARY.md
## VidAuditFlow — Backend Foundation Modernization (Implementation Phase 1)

**Scope:** backend quality only. No user-facing functionality changed, no LangGraph redesign, no frontend, no auth, no database. This phase corresponds to `IMPLEMENTATION_PHASES.md` Phase 0 (secrets hygiene), Phase 1 (async core), Phase 2 (schema consolidation), and Phase 4 (central config/logging), compressed into one session, plus the TD-8 dependency cleanup that `TECHNICAL_DEBT.md` explicitly ties to this same config-centralization work.

---

## Files Changed

### New files
| File | Purpose |
|---|---|
| `backend/src/core/__init__.py` | Package marker |
| `backend/src/core/config.py` | Single `Settings` (Pydantic `BaseSettings`) — the only place env vars are read |
| `backend/src/core/logging.py` | Structured JSON logging, request-id propagation via `contextvars`, one-time configuration |
| `backend/src/core/exceptions.py` | `VidAuditFlowError` + 6 typed subclasses (`ConfigurationError`, `VideoDownloadError`, `VideoIndexerError`, `RetrievalError`, `ComplianceError`, `ValidationError`) |
| `backend/src/schemas/__init__.py` | Package marker |
| `backend/src/schemas/audit.py` | Single definitions of `ComplianceIssue`, `AuditRequest`, `AuditResult`, `AuditResponse` |
| `backend/src/utils/__init__.py` | Package marker |
| `backend/src/utils/urls.py` | `is_supported_video_url()` — extracted, dependency-free URL check |
| `backend/src/services/youtube.py` | YouTube download, wrapped in `asyncio.to_thread`, using a per-job directory |
| `.env.example` | Documents every setting with a placeholder value |

### Rewritten files
| File | What changed |
|---|---|
| `backend/src/services/video_indexer.py` | `requests` → `httpx.AsyncClient`; added timeouts + `tenacity` retry on transient HTTP errors; bounded the polling loop (was `while True`); raises `VideoIndexerError` instead of bare `Exception`; YouTube download logic removed (moved to `services/youtube.py`) |
| `backend/src/graph/nodes.py` | Both nodes are now `async def`; uses `tempfile.TemporaryDirectory()` per invocation instead of a shared hardcoded filename; reads config via `settings`, not `os.getenv`; raises/logs typed exceptions internally, preserving the original "a node never raises out of the graph" contract |
| `backend/src/graph/state.py` | `ComplianceIssue` is now imported from `schemas/audit.py` instead of being redefined as a local `TypedDict` |
| `backend/src/graph/workflow.py` | Docstrings/typing only — topology (`indexer → auditor`) is unchanged |
| `backend/src/api/telemetry.py` | Reads `settings.applicationinsights_connection_string` instead of `os.getenv`; uses `get_logger` |
| `main.py` (root CLI) | Runs via `asyncio.run(...)` + `await app.ainvoke(...)`; removed unused `pprint` import; fixed the `"1.nput Payload"` typo; uses `get_logger` |
| `backend/scripts/index_documents.py` | Reads embedding deployment name (and all other settings) from `core.config.settings` instead of independent `os.getenv` calls — this directly fixes the index/query embedding-model drift risk (TD-15); added a `sys.path` bootstrap so the script remains runnable standalone |
| `pyproject.toml` | Removed 6 unused dependencies + `requests`; added `httpx`, `pydantic-settings`, `tenacity` explicitly |
| `.gitignore` | Now excludes `.env` (was previously trackable) |
| `.env` (local, git-ignored) | Fixed `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` from a blank placeholder to `text-embedding-3-small`, to exactly preserve the original hardcoded behavior once that value became a real, honored setting instead of dead configuration |

### Removed / renamed
| File | Disposition |
|---|---|
| `backend/src/api/server.py` | Renamed to `backend/src/api/main.py` per `FOLDER_STRUCTURE_V2.md`; content rewritten (see below) |

### `backend/src/api/main.py` (replaces `server.py`) — new content highlights
- `await compliance_graph.ainvoke(...)` instead of `.invoke()`.
- Request-id middleware (`X-Request-ID` header in/out) bound to `core.logging`'s contextvar, so every log line for a request shares one id.
- Exception handlers for `ValidationError` (→ 400) and the `VidAuditFlowError` base class (→ 502), so application-raised errors never leak raw Python exception text to a client.
- `/health` now returns `status`, `service`, `version`, `environment`, and `uptime_seconds` (previously only `status` and `service`).
- `/audit` response-building logic unchanged in shape; now built from the shared `AuditResponse` schema.

---

## Architecture Improvements

- **Folder structure** now matches `FOLDER_STRUCTURE_V2.md`'s target layout for this phase's scope: `api/`, `core/`, `services/`, `schemas/`, `graph/`, `utils/` all exist with the intended responsibilities. `db/`, `jobs/`, `routers/` (plural) are intentionally **not** created yet — they belong to later phases (auth, persistence, job-based API) that are explicitly out of scope here.
- **Configuration** is centralized: `core/config.py` is the only module that calls `os.getenv`/reads `.env` directly (verified — see Verification section). Every other module imports `settings`.
- **Logging** is centralized: `core/logging.py` is the only module that calls `logging.basicConfig`/configures handlers (verified). All loggers are now named by module path (e.g. `backend.src.graph.nodes`) instead of five inconsistent flat names (`brand-guardian`, `api-server`, `video-indexer`, ...).
- **The backend is fully async** end-to-end on the request path: FastAPI route → `graph.ainvoke()` → node functions → `httpx.AsyncClient` / `asyncio.to_thread`-wrapped `yt-dlp` / `asimilarity_search()` / `llm.ainvoke()`. Verified live: `/health` responds in ~80ms while a real audit is mid-download (see Verification).
- **No duplicated schemas.** `ComplianceIssue` now has exactly one definition (`schemas/audit.py`), imported by both the graph state and the API response model (`AuditResponse` extends `AuditResult`, both from the same module).
- **Typed exceptions** replace bare `Exception` at every raise site added or touched in this phase (video download, Video Indexer calls, retrieval, compliance parsing).

---

## Technical Debt Removed

Cross-referenced to `TECHNICAL_DEBT.md`:

| ID | Item | Status |
|---|---|---|
| TD-1 | Synchronous call blocking the event loop | **Resolved** — `ainvoke()` + async nodes throughout |
| TD-2 | `.env` not git-ignored | **Resolved** — added to `.gitignore`, `.env.example` introduced |
| TD-3 | Shared hardcoded temp filename / race condition | **Resolved** — `tempfile.TemporaryDirectory()` per job |
| TD-6 (partial) | Zero automated tests | **Not resolved** — out of scope for this phase (Phase 5); manual/live verification only (see below) |
| TD-8 | 6 unused dependencies | **Resolved** — `streamlit`, `redis`, `sqlalchemy`, `psycopg2-binary`, `firecrawl-py`, `pandas` removed; `requests` also removed as it's no longer imported anywhere |
| TD-9 | Duplicated `ComplianceIssue` schema | **Resolved** — single definition in `schemas/audit.py` |
| TD-11 | No outbound HTTP timeouts | **Resolved** — every `httpx` call has an explicit timeout |
| TD-12 | No retry policy | **Partially resolved** — `tenacity`-based retry added at the service layer (Video Indexer HTTP calls); LangGraph-native per-node `RetryPolicy` is deferred to the Phase 11 AI-pipeline rebuild per `IMPLEMENTATION_PHASES.md` |
| TD-15 | Hardcoded embedding deployment name drifting from ingestion config | **Resolved** — single setting, single default, used by both `nodes.py` and `index_documents.py` |
| TD-20 | Azure AD token churn in the polling loop | **Not resolved** — still fetches a fresh token every poll iteration; explicitly deferred (see Remaining Debt) |
| TD-23 | Redundant `logging.basicConfig()` calls / inconsistent logger names | **Resolved** |
| TD-24 | Unused `pprint` import, `main.py` typo | **Resolved** |
| C5 (unbounded polling loop) | No timeout on Video Indexer polling | **Resolved** — bounded to `video_indexer_max_poll_attempts` (default 60, ~30 min) |
| Medium: verbose internal error messages returned to clients | Raw exception text in `HTTPException.detail` | **Resolved** — generic external message; full detail only in server logs |

Also fixed as a byproduct of the async rewrite: the soft "verbose error" issue on the `/audit` endpoint (unexpected failures now return a generic message, not `str(e)`).

---

## Remaining Debt (explicitly deferred, tracked in TECHNICAL_DEBT.md / IMPLEMENTATION_PHASES.md)

- **TD-6 — no automated test suite.** This phase's verification was manual/live (see below), not a `pytest` suite. That's `IMPLEMENTATION_PHASES.md` Phase 5, a separate, dedicated phase.
- **TD-13 — soft SSRF via substring URL check.** `utils/urls.is_supported_video_url()` intentionally preserves the original substring check (`"youtube.com" in url`) rather than upgrading to strict host parsing — the docstring says so explicitly. Tightening this is Phase 3's job, not this phase's; changing it now would have been exactly the kind of validation-behavior change this phase was told to avoid.
- **TD-10 (M5/M6) — no structured-output validation on the LLM response.** `audit_content_node` still parses the LLM's JSON with `json.loads()` after regex fence-stripping. This is unchanged from the original logic (per the "do not change prompts / business logic" constraint for this phase) but is still fragile — tracked for Phase 3.
- **TD-16 — deprecated `langchain_community.vectorstores.AzureSearch`.** Still in use; migrating to a maintained integration is scoped to the Phase 11 Retrieval Agent extraction, which is explicitly out of scope here (no LangGraph redesign).
- **TD-20 — Azure AD token churn.** `wait_for_processing()` still calls `_get_account_token_via_arm()` on every poll iteration. Not fixed in this phase to keep the diff focused on async correctness rather than introducing new stateful caching; flagged as a good, low-risk follow-up.
- **LangGraph-native retry/checkpointing.** The `tenacity` retry added here lives in the service layer (HTTP calls), not as a LangGraph `RetryPolicy` on the nodes themselves, and there is still no checkpointer — both are explicitly scoped to the Phase 10/11 AI-pipeline rebuild in `IMPLEMENTATION_PHASES.md`, which this phase was told not to touch.
- **`ValidationError`** (in `core/exceptions.py`) is defined but has no active call site yet — it's ready for Phase 3's stricter URL/input validation work.
- **`backend/scripts/explanation.txt`** (a personal debugging note, not real documentation) was left untouched — out of scope; tracked in `TECHNICAL_DEBT.md` TD-26 for the Phase 20 README pass.
- **`azure_functions/*` and `backend/Dockerfile`** remain empty — untouched, as populating them is Phase 12 (deployment), not this phase.
- **CORS middleware** was intentionally not added — no frontend exists yet to have an origin, and adding it now would be speculative configuration ahead of need.

---

## Migration Notes

- **Run command changed.** The API is now served from `backend.src.api.main:app`, not `backend.src.api.server:app`:
  ```
  uv run uvicorn backend.src.api.main:app --reload
  ```
- **CLI invocation is unchanged** (`uv run python main.py`), but it now runs the graph via `asyncio.run(...)`.
- **New required env vars behavior:** `core/config.py` will raise `ConfigurationError` at import time if a required Azure setting (API keys, endpoints, deployment names, Video Indexer identifiers) is entirely absent from the environment. It will **not** raise if the variable is present but empty (matching every current placeholder in `.env`), so local runs with the existing blank `.env` continue to behave exactly as before — they simply fail later, at the actual Azure call, with the same class of error as previously.
- **`.env.example`** now exists and should be copied to `.env` for any fresh clone; the previously-committed-in-spirit blank `.env` pattern is replaced by this git-ignored-`.env` + committed-`.env.example` pattern.
- **Dependency changes:** run `uv sync` after pulling this change — `pyproject.toml` dropped 6 unused packages and `requests`, and added `httpx`, `pydantic-settings`, `tenacity` as explicit (previously transitive) dependencies.

---

## Known Limitations

- **No live Azure verification was possible in this environment.** The `.env` on disk contains only blank placeholder credentials, so the Video Indexer upload/poll, Azure AI Search retrieval, and Azure OpenAI compliance-judgment steps could not be exercised against real Azure services. What **was** verified live: real YouTube download via the new async `services/youtube.py` path (successfully downloaded a real video into a per-job temp directory, which was then cleaned up automatically), and the full graceful-failure path once the (intentionally blank) Azure credentials are hit.
- **No automated regression tests were added.** Verification for this phase was manual/live (see below) rather than a `pytest` suite, consistent with this phase's scope (test infrastructure is `IMPLEMENTATION_PHASES.md` Phase 5).
- **Token caching for Video Indexer auth was not implemented** (see TD-20 above) — a correctness-neutral, low-priority efficiency gap that was consciously left for a follow-up rather than expanding this phase's diff.
- **`tenacity`-based retry only covers the Video Indexer HTTP client**, not the Azure OpenAI/Azure AI Search calls in `audit_content_node` — those calls rely on the underlying `openai`/`azure-search-documents` SDKs' own internal retry behavior (visible in the verification logs: the OpenAI client itself retried the embeddings call twice before giving up). Adding an explicit `tenacity` layer there as well would be reasonable but was not required to satisfy this phase's stated success criteria and was left out to avoid scope creep.

---

## Verification Performed

1. **Static checks:** every new/changed `.py` file passed `python -m py_compile`. `grep` confirms zero live `os.getenv()` calls outside `core/config.py` and zero live `logging.basicConfig()` calls outside `core/logging.py` (the only matches elsewhere are docstring prose describing the rule, not code).
2. **Dependency install:** `uv sync` completed cleanly after the `pyproject.toml` cleanup (31 packages uninstalled, lockfile regenerated).
3. **Config load:** `Settings()` constructs successfully against the current `.env` (all required-but-blank placeholders satisfy "present", matching original `os.getenv` semantics); confirmed the `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` default now resolves correctly after fixing the local `.env` value.
4. **Graph compiles:** `backend.src.graph.workflow.app` compiles with the unchanged `indexer → auditor` topology.
5. **Server boot + endpoints:**
   - `GET /health` → `200`, returns `status`, `service`, `version`, `environment`, `uptime_seconds`.
   - `GET /docs` / `GET /openapi.json` → `200`.
   - `POST /audit` with a non-YouTube URL → `200`, graceful `FAIL` response (`"Audit skipped because video processing failed (No Transcript)."`), exercising the typed-exception + error-swallowing path with no real network/Azure access needed.
   - `POST /audit` with the real demo YouTube URL (`https://youtu.be/dT7S75eYhcQ`) → real download succeeded via the async `yt-dlp` wrapper into a per-job temp directory (confirmed removed afterward), failed gracefully at the Video Indexer step due to blank Azure credentials, returned a clean `200` `FAIL` response — no crash, no leaked stack trace.
   - **Concurrency check:** fired a real audit request and, while it was mid-download, called `GET /health` — it responded in ~0.08s, proving the event loop is not blocked (direct verification of the C1 fix).
   - Verified structured JSON logs carry one consistent `request_id` across every log line for a single request (API layer → indexer node → auditor node).
6. **CLI:** `uv run python main.py` ran end-to-end via `asyncio.run`, produced the same report format as before (including the "No violations found." / final summary sections), with the typo and unused import fixed.
7. **Ingestion script:** `uv run python backend/scripts/index_documents.py` ran to completion (with blank credentials, exactly as before), logging its configuration and failing gracefully with the same caught, logged error pattern as the original implementation (`"Failed to initialize Azure Search: ..."`), not a crash.
