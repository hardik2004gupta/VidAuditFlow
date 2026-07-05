# Quality Report — Production Readiness

**Scope:** testing, CI, code quality tooling, and developer experience only. No product features, UI, API behavior, LangGraph, or database schema changed — verified in [Section 7](#7-verification). This is the first phase to introduce automated tests, CI, and linting tooling; prior phases (see [`docs/`](docs/)) built the product itself.

---

## 1. Tests Added

### Backend (`backend/tests/`, pytest) — 33 tests across 7 files

| File | Covers |
|---|---|
| `test_health.py` | `GET /health` |
| `test_config.py` | `Settings` loading from env, field defaults, `CORS_ALLOWED_ORIGINS` parsing |
| `test_graph_state.py` | `VideoAuditState` validation, `operator.add` reducer annotations |
| `test_repositories.py` | `AuditRepository`/`ReportRepository` CRUD and status transitions against a real (test) database |
| `test_audits_api.py` | `POST/GET /api/v1/audits`, `GET /api/v1/audits/{id}` |
| `test_reports_api.py` | `GET /api/v1/reports/{id}`, `POST /api/v1/reports/{id}/chat` (success, conversation replay, 404, LLM failure → 502) |
| `test_integration_flow.py` | Full create → poll → retrieve → chat flow, plus the graceful-degradation (`status=failed` with a report) path |

**No test requires real Azure credentials or makes a real network call.** `conftest.py` sets dummy values for every required `Settings` field and no-ops `dotenv.load_dotenv` before any app module is imported, so a developer's real local `.env` (even one with real keys) can never leak into a test run. Every LLM/graph touchpoint is mocked at a deliberate boundary:
- `execute_audit_job` is patched at its call site in the audits router (not inside `jobs/audit_runner.py`) for the audit-creation and integration-flow tests, since re-running the real LangGraph pipeline in a test would need real Azure services and directly contradicts "Do NOT change LangGraph" (there's nothing to gain by re-testing the graph's internals here).
- `services.report_chat.get_chat_llm` is patched with a fake object exposing an async `.ainvoke()` for every chat test, including one that asserts the report's actual grounding data (violation names, the "Never fabricate" instruction) reaches the model.

A real (not mocked) SQLite database is used for every DB-touching test — a fresh temp file per test session, schema created via `SQLModel.metadata.create_all()` (no Alembic involved, since testing migrations isn't this suite's job).

### Frontend (`frontend/**/*.test.tsx`, Vitest + Testing Library) — 30 tests across 10 files

| File | Covers |
|---|---|
| `app/(marketing)/page.test.tsx` | Landing page renders (hero, every section) |
| `app/(dashboard)/dashboard/page.test.tsx` | Dashboard renders with mocked API data |
| `app/(dashboard)/reports/[id]/page.test.tsx` | Report page renders (async Server Component, awaited directly); `notFound()` on a missing report |
| `features/audits/components/new-audit-form.test.tsx` | Empty-field and non-YouTube-URL validation errors; valid submission calls `createAudit` |
| `features/reports/components/copilot/copilot-panel.test.tsx` | Empty state + suggested prompts, close button, sending a message and rendering the reply, error + retry |
| `features/audits/components/stage-tracker.test.tsx` | Stage labels, elapsed time, progress bar value, the failed-stage visual state |
| `features/audits/components/severity-badge.test.tsx`, `components/shared/{metric-card,empty-state}.test.tsx` | Reusable component contracts |
| `lib/format.test.ts` | Pure formatting helpers (`formatDuration`, `formatStageDuration`, `parseTimestampToSeconds`, `shortId`) |

New test infrastructure: `vitest.config.ts` (jsdom environment, `@/` path alias matching `tsconfig.json`, v8 coverage), `vitest.setup.ts` (`jest-dom` matchers, `matchMedia`/`scrollIntoView` jsdom stubs), and `test/test-utils.tsx` (a `renderWithQueryClient` helper for the many components that call `useQuery`/`useMutation`).

---

## 2. Coverage Summary

Coverage is meaningful, not exhaustive — per this phase's explicit "do not chase 100%, focus on business-critical code."

**Backend: 68% statements** (`uv run pytest --cov`). Where it's concentrated:

| Layer | Coverage | Why |
|---|---|---|
| API routes, repositories, schemas, DB models, config, `services/report_chat.py` | 94–100% | The business-critical, testable-without-Azure surface — exactly this phase's stated priority list |
| LangGraph nodes (`compliance_agent`, `summary_agent`, `retrieval_agent`, `ocr_agent`, `transcript_agent`, `supervisor`, `coordination`) | 29–52% | Deep coverage here would require either mocking LangChain/Azure SDK internals extensively or real credentials (explicitly forbidden) — out of proportion to the value for a "highest-value paths" pass, and this phase's "Do NOT change LangGraph" scope means there's no intent to refactor these nodes based on test findings anyway |

**Frontend: 57% statements / 58% lines / 60% functions** (`npm run test:coverage`). Concentrated in exactly what Part 2 asked for (landing, dashboard, new-audit validation, report page, Copilot panel, stage tracker, a few reusables) at 68–100% each; components not explicitly listed (`site-header`, `site-footer`, `reports-table`, standalone `evidence-card`, `report-actions-menu`, `chat-input` in isolation) are only indirectly exercised as children of tested pages, hence 0% direct coverage in the report — a known, acceptable gap rather than an oversight (see [Section 6](#6-remaining-gaps)).

Both suites generate HTML reports locally (`make coverage`, or `uv run pytest --cov-report=html` / `npm run test:coverage`) — gitignored (`htmlcov/`, `frontend/coverage/`), not committed.

---

## 3. CI Workflow

[`​.github/workflows/ci.yml`](.github/workflows/ci.yml) — two parallel jobs, both required to pass, on every push and pull request:

**`backend`**: install via `uv sync --all-groups` → `ruff check .` → `pytest --cov --cov-report=term-missing` → a backend import sanity check (`from backend.src.api.main import app`). Dummy Azure credentials are set via the workflow's top-level `env:` block (identical values to `conftest.py`'s) so `Settings()` construction never needs real secrets.

**`frontend`**: `npm ci` → `tsc --noEmit` → `npm run lint` → `npm run test:coverage` → `npm run build`.

Either job failing fails the whole run. A `concurrency` group cancels superseded runs on the same branch/PR instead of queuing them.

---

## 4. Code Quality Tooling

- **Ruff** (`[tool.ruff]` in `pyproject.toml`): linting (`E`, `F`, `I`, `B` rule groups) *and* formatting, replacing the need for a separate Black install — **Black was deliberately not added**, since Ruff's formatter is its modern, drop-in successor and running both would just create two tools that could disagree with each other on the same files.
  - **Calibrated to this codebase's existing style, not a generic default.** The obvious first pass (adding pyupgrade's `"UP"` rules) flagged **157 pre-existing call sites** wanting `typing.Dict`/`List`/`Optional` rewritten to built-in generics (`dict`/`list`/`X | None`) — a real, consistent, intentional style choice in this codebase (paired with `from __future__ import annotations` throughout), not an oversight. Turning that rule group on would have meant either touching dozens of unrelated files or shipping a linter config that fails CI on day one. It's left off, with the reasoning recorded directly in `pyproject.toml`'s comments.
  - `B008` (function-call-in-default-argument) is ignored — it's a well-known false positive for FastAPI's own `Depends(...)` dependency-injection idiom, not a bug.
  - Result: `uv run ruff check .` passes clean. The two real, tiny, safe findings it did surface (import ordering in `backend/alembic/env.py`) were fixed.
- **ESLint** (`eslint-config-next`, pre-existing): confirmed still clean (`npm run lint`); no config changes needed.
- **Prettier**: newly added (`.prettierrc.json`, `.prettierignore`, `npm run format` / `format:check`) — matches the codebase's existing conventions (double quotes, semicolons, trailing commas). **Not run with `--write` against the existing codebase**: `prettier --check` flags 43 pre-existing files (mostly shadcn-generated `components/ui/*`, which have their own vendored formatting), and reformatting them wasn't this phase's job ("do not reformat unrelated files"). The config exists for new code going forward and for a deliberate, separate reformatting pass later if wanted.

---

## 5. Developer Experience

- **`Makefile`** — `setup`, `dev-backend`, `dev-frontend`, `test` / `test-backend` / `test-frontend`, `coverage`, `lint` / `lint-backend` / `lint-frontend`, `format`, `build`, `migrate`, `clean`, `help`. Works natively on Linux/macOS/CI; Windows users without `make` (this development environment included) use the equivalent raw commands, which the README now lists side-by-side with each target.
- **README's new "Development" section** documents every Makefile target, its raw-command equivalent, and what CI actually checks.
- **One-command setup**: `make setup` (or `uv sync --all-groups && cd frontend && npm install`) installs everything needed to run, test, and lint both halves of the app.

---

## 6. Remaining Gaps

- **LangGraph node internals are lightly covered** (Section 2) — by design for this phase, but a future phase could add node-level unit tests with `AzureChatOpenAI.ainvoke`/`AzureSearch` mocked directly (rather than mocking the whole node, as this phase's tests do at the `execute_audit_job` boundary), if deeper pipeline-logic regression protection becomes a priority.
- **A handful of frontend components have no direct test** (`site-header`/`site-footer`, `reports-table`, `report-actions-menu`, standalone `evidence-card`, `chat-input` in isolation) — each is exercised indirectly as a child of a tested page, but doesn't have its own focused test file. Reasonable next additions if this suite grows.
- **No end-to-end (browser) tests** — everything here is unit/component/API-level. A real Playwright/Cypress suite hitting a running dev server would be the natural next layer, not attempted here (explicitly out of scope: "lightweight integration tests," not full E2E).
- **`npm audit`'s 2 moderate transitive advisories** (a `postcss` version nested inside `next`'s own dependency tree, first noted in `REPOSITORY_AUDIT.md`) remain — the only "fix" `npm audit fix --force` offers is downgrading Next.js 15 → 9, which is not a fix.
- **Prettier hasn't been applied to the existing codebase** (Section 4) — available for a deliberate future pass, not applied now to avoid an unrelated, repo-wide diff.

---

## 7. Verification

- `uv run ruff check .` — clean.
- `uv run pytest` — 33/33 passed.
- `uv run python -c "from backend.src.api.main import app; ..."` — clean import, 11 routes registered (unchanged from before this phase).
- `npx tsc --noEmit` (frontend) — clean.
- `npm run lint` (frontend) — clean.
- `npx vitest run` — 30/30 passed.
- `npm run build` (frontend) — succeeds; every route's bundle size is byte-for-byte identical to this phase's starting point (no application code changed, only tests/config/tooling were added).
- No product feature, UI, API contract, LangGraph node, or database schema was modified — every backend change in this phase is additive (new test files, new `[tool.*]` config sections) or a 2-line import-order fix; every frontend change is a new test file, new config file, or a doc/README update.

---

## 8. Recommendations

1. Add node-level LangGraph unit tests (mock `AzureChatOpenAI`/`AzureSearch` directly) if pipeline-logic regressions become a concern — see Section 6.
2. Consider a small Playwright smoke suite (one real browser flow: submit an audit → see it in the dashboard) once the app has a stable staging environment to run it against.
3. Run a deliberate, isolated `npm run format` (Prettier) and `make format` (Ruff) pass as their own dedicated commit when the team is ready to absorb a repo-wide formatting diff — don't fold it into a feature change.
4. Wire up branch protection on CI once this repository has a real remote team, so the `backend`/`frontend` CI jobs are required checks before merge.
5. Revisit the coverage thresholds in `pyproject.toml`/`vitest.config.ts` (currently unset/informational-only) once the team agrees on a minimum bar, and enforce it in CI at that point rather than before.
