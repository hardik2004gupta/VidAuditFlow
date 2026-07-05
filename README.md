# VidAuditFlow

AI-powered video compliance auditing. Paste a YouTube URL, and a Supervisor-orchestrated LangGraph pipeline transcribes the video, reads its on-screen text, retrieves relevant advertising/platform policy, and produces a citation-backed compliance report — viewable in a live-updating Next.js dashboard.

```
Supervisor
  ├─ Transcript Agent   (download video, transcribe)
  ├─ OCR Agent          (read on-screen text)
  ├─ Retrieval Agent    (RAG over a policy knowledge base)
  ├─ Compliance Agent   (flag violations by category/severity)
  └─ Summary Agent      (executive summary + suggested fixes)
```

---

## Tech Stack

| Layer | Stack |
|---|---|
| AI pipeline | LangGraph (Supervisor + 5 specialist nodes), LangChain, Azure OpenAI, Azure AI Search (RAG), Azure Video Indexer |
| Backend | FastAPI, SQLModel + Alembic, SQLite (dev) / PostgreSQL (prod), async throughout |
| Frontend | Next.js 15 (App Router), TypeScript, Tailwind CSS v4, shadcn/ui (Base UI), TanStack Query, Framer Motion, Recharts |

---

## Project Structure

```
compliance-qa-pipeline/
├── backend/
│   └── src/
│       ├── api/            FastAPI app, routers (/api/v1/audits, /api/v1/reports), CORS, error envelope
│       ├── graph/           The LangGraph pipeline: nodes, supervisor, observability
│       ├── jobs/            Background job runner that drives a graph run to completion
│       ├── db/              SQLModel models, session, migration runner
│       ├── repositories/    Data-access layer (AuditRepository, ReportRepository)
│       ├── schemas/         Pydantic request/response contracts
│       ├── services/        External integrations (YouTube download, Video Indexer, etc.)
│       └── core/            Config, logging, exceptions -- the only place env vars are read
├── frontend/
│   ├── app/                 Route groups: (marketing) landing page, (dashboard) app shell
│   ├── components/          ui/ (shadcn primitives), layout/, shared/
│   ├── features/            audits/, dashboard/, reports/, landing/, settings/ -- feature-scoped components
│   ├── hooks/                useAuditJobPolling, etc.
│   ├── lib/                  api.ts (real backend client), format.ts, report-export.ts
│   └── types/                api.ts -- TypeScript types mirroring the backend's Pydantic schemas
├── alembic/                  Database migrations
├── main.py                   CLI smoke-test entry point (runs the pipeline directly, no API/DB)
└── docs/                     Planning docs, audits, and per-phase implementation summaries (see below)
```

---

## Getting Started

### Prerequisites

- Python 3.12+ and [uv](https://docs.astral.sh/uv/)
- Node.js 18+ and npm
- Azure OpenAI, Azure AI Search, and Azure Video Indexer resources, if you want a full pipeline run to actually succeed (see [Environment Variables](#environment-variables) below — the app runs and the UI works without them, but an audit job will fail at the transcript/OCR stage)

### 1. Backend

```bash
cp .env.example .env      # fill in your Azure credentials
uv sync
uv run uvicorn backend.src.api.main:app --reload
```

- API: `http://localhost:8000`
- Interactive docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

The database defaults to a local SQLite file (`vidauditflow.db`) with migrations run automatically on startup in `local` environment — no setup required. Point `DATABASE_URL` at a Postgres DSN for production.

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env.local   # NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

- App: `http://localhost:3000`

The frontend calls the backend directly (no proxy) — make sure `NEXT_PUBLIC_API_URL` matches wherever the backend is actually running, and that its origin is in the backend's `CORS_ALLOWED_ORIGINS`.

---

## Environment Variables

Full reference with inline comments: [`.env.example`](.env.example).

| Variable | Required | Notes |
|---|---|---|
| `AZURE_OPENAI_API_KEY` / `_ENDPOINT` / `_CHAT_DEPLOYMENT` | Yes | Powers the Compliance and Summary agents |
| `AZURE_SEARCH_ENDPOINT` / `_API_KEY` / `_INDEX_NAME` | Yes | The RAG policy knowledge base |
| `AZURE_VI_LOCATION` / `_ACCOUNT_ID` / `_SUBSCRIPTION_ID` / `_RESOURCE_GROUP` | Yes | Video transcription/OCR via Azure Video Indexer |
| `DATABASE_URL` | No | Defaults to local SQLite; set to a Postgres DSN in production |
| `CORS_ALLOWED_ORIGINS` | No | Comma-separated origin allow-list; defaults to `http://localhost:3000` |
| `APPLICATIONINSIGHTS_CONNECTION_STRING`, `LANGCHAIN_*` | No | Observability/tracing; each feature degrades gracefully if unset |

---

## Development

A `Makefile` wraps the common commands (works out of the box on Linux/macOS, or on Windows via WSL/Git Bash with `make` installed; the raw commands to its right work everywhere, including plain PowerShell):

| `make` target | Equivalent |
|---|---|
| `make setup` | `uv sync --all-groups` && `cd frontend && npm install` |
| `make dev-backend` | `uv run uvicorn backend.src.api.main:app --reload` |
| `make dev-frontend` | `cd frontend && npm run dev` |
| `make test` | Backend (`uv run pytest`) + frontend (`cd frontend && npm test`) |
| `make coverage` | Both test suites, with coverage reports |
| `make lint` | `uv run ruff check .` + `cd frontend && npm run lint` |
| `make format` | `uv run ruff format .` + `cd frontend && npm run format` |
| `make build` | `cd frontend && npm run build` |
| `make migrate` | `uv run alembic upgrade head` |

Run `make help` for the full list. **CI** ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) runs on every push/PR: Ruff, backend tests with coverage, a backend import check, TypeScript, ESLint, frontend tests with coverage, and a production frontend build — all against dummy Azure credentials, no real service calls. See [`QUALITY_REPORT.md`](QUALITY_REPORT.md) for what the test suite covers and what it deliberately doesn't.

---

## Documentation

This project was built in phases, each with a written brief and a summary of what shipped. Everything beyond this README lives in [`docs/`](docs/) (see [`docs/README.md`](docs/README.md) for the full index) — planning docs describe the target architecture, phase summaries describe what was actually implemented and verified, and [`REPOSITORY_AUDIT.md`](REPOSITORY_AUDIT.md) documents the pre-public-release cleanup.

**Implementation, in order:**

| Phase | Summary | Scope |
|---|---|---|
| 2 | [`PHASE_2_SUMMARY.md`](docs/phases/PHASE_2_SUMMARY.md) | Backend foundation: config, logging, async, error handling |
| 3 | [`PHASE_3_SUMMARY.md`](docs/phases/PHASE_3_SUMMARY.md) | Supervisor-based, 7-node LangGraph pipeline |
| 4 | [`PHASE_4_SUMMARY.md`](docs/phases/PHASE_4_SUMMARY.md) | Persistence (SQLModel/Alembic) + background job execution |
| 4.5 | [`PHASE_4_5_AUDIT.md`](docs/audits/PHASE_4_5_AUDIT.md) | Full engineering audit and rectification |
| 5 | [`PHASE_5_SUMMARY.md`](docs/phases/PHASE_5_SUMMARY.md) | Frontend foundation (Next.js, mocked data) |
| 6 | [`PHASE_6_SUMMARY.md`](docs/phases/PHASE_6_SUMMARY.md) | Real backend integration, typography/visual polish |
| 7 | [`PHASE_7_SUMMARY.md`](docs/phases/PHASE_7_SUMMARY.md) | Premium report experience (evidence timeline, violation cards, export) |
| 8 | [`PHASE_8_SUMMARY.md`](docs/phases/PHASE_8_SUMMARY.md) | AI Copilot for compliance reports |

---

## Current Status

The full stack runs end-to-end: creating an audit, polling its live status, viewing the resulting report, and chatting with an AI Copilot grounded in that report (`POST /api/v1/reports/{id}/chat`) all work against the real backend (no mocks). Without real Azure credentials configured, a submitted audit will still be created and tracked correctly, but the pipeline itself will fail at the transcript/OCR stage — the app is designed to degrade gracefully in that case (a report is still generated, explaining what failed, rather than the job silently disappearing).
