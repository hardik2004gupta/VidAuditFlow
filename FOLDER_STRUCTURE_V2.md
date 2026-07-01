# FOLDER_STRUCTURE_V2.md
## VidAuditFlow — Target Repository Layout

This is the intended structure once the modernization is complete. It is a **monorepo** with two top-level deployables (`frontend/`, `backend/`) plus shared root-level docs/config. No workspace tool (Turborepo/Nx) is introduced — the two apps are independent deployables that happen to live in one git repo, deployed separately to Vercel and Render/Railway.

```
vidauditflow/
├── frontend/                          # Next.js 15 app — deployed to Vercel
│   ├── app/                           # App Router: routes = folders
│   │   ├── (marketing)/               # Public, unauthenticated routes
│   │   │   ├── page.tsx               # Landing page (paste-a-URL hero)
│   │   │   └── layout.tsx
│   │   ├── (auth)/                    # Sign in / sign up flows
│   │   │   ├── login/page.tsx
│   │   │   └── signup/page.tsx
│   │   ├── (dashboard)/               # Authenticated app shell
│   │   │   ├── layout.tsx             # Sidebar/topnav shell, session check
│   │   │   ├── dashboard/page.tsx     # List of past audits
│   │   │   ├── audits/
│   │   │   │   ├── new/page.tsx       # Paste-URL + kickoff form
│   │   │   │   └── [id]/
│   │   │   │       ├── page.tsx       # Live tracker OR finished report (same route, state-driven)
│   │   │   │       └── chat/page.tsx  # AI chat scoped to this report (or a panel within [id]/page.tsx)
│   │   │   └── settings/page.tsx
│   │   ├── api/                       # Next.js route handlers ONLY for BFF concerns
│   │   │   └── auth/callback/route.ts # Supabase auth callback
│   │   ├── layout.tsx                 # Root layout (fonts, theme provider)
│   │   └── globals.css                # Tailwind base + design tokens
│   ├── components/
│   │   ├── ui/                        # shadcn/ui primitives (generated, lightly customized)
│   │   ├── audit/                     # Domain components: StageTracker, ViolationCard, SeverityBadge
│   │   ├── charts/                    # Recharts wrappers: ComplianceScoreGauge, ViolationsBarChart
│   │   ├── chat/                      # ChatPanel, MessageBubble, ChatInput
│   │   └── layout/                    # Sidebar, Topbar, PageHeader, EmptyState
│   ├── lib/
│   │   ├── api-client.ts              # Typed fetch wrapper for the FastAPI backend
│   │   ├── supabase/                  # Supabase client (browser + server variants)
│   │   ├── types.ts                   # TypeScript types mirroring backend Pydantic schemas
│   │   └── utils.ts                   # cn() and small helpers (kept minimal, no grab-bag file)
│   ├── hooks/
│   │   ├── use-audit-status.ts        # Polling/SSE hook for a running job
│   │   └── use-auth.ts                # Session/user hook wrapping Supabase Auth
│   ├── public/                        # Static assets (logo, favicon, OG image)
│   ├── styles/                        # Tailwind config extensions if not colocated in globals.css
│   ├── middleware.ts                  # Route protection (redirect unauthenticated users)
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   └── package.json
│
├── backend/                            # FastAPI app — deployed to Render/Railway
│   ├── src/
│   │   ├── api/
│   │   │   ├── main.py                # FastAPI() app factory, middleware, router mounting
│   │   │   ├── deps.py                # Shared dependencies: get_db, get_current_user, get_settings
│   │   │   └── routers/
│   │   │       ├── audits.py          # POST /audits, GET /audits, GET /audits/{id}
│   │   │       ├── chat.py            # POST /audits/{id}/chat
│   │   │       ├── reports.py         # GET /reports/{id}/export
│   │   │       └── health.py          # GET /health
│   │   ├── core/
│   │   │   ├── config.py              # Pydantic Settings — single source of truth for env vars
│   │   │   ├── logging.py             # Structured logging setup
│   │   │   └── security.py            # Supabase JWT verification helpers
│   │   ├── db/
│   │   │   ├── session.py             # SQLModel engine/session factory (SQLite or Postgres via env)
│   │   │   └── models.py              # SQLModel table models: User, AuditJob, Report
│   │   ├── schemas/                   # Pydantic request/response + shared graph contracts
│   │   │   ├── audit.py               # AuditRequest, AuditJobRead, ComplianceIssue, ReportRead
│   │   │   └── chat.py                # ChatMessageRequest/Response
│   │   ├── graph/                     # LangGraph pipeline (see AI_PIPELINE_VISION.md)
│   │   │   ├── state.py               # Shared graph state (imports schemas/, no duplication)
│   │   │   ├── supervisor.py          # Supervisor node + routing logic
│   │   │   ├── nodes/
│   │   │   │   ├── transcript_agent.py
│   │   │   │   ├── ocr_agent.py
│   │   │   │   ├── retrieval_agent.py
│   │   │   │   ├── compliance_agent.py
│   │   │   │   └── summary_agent.py
│   │   │   └── workflow.py            # Graph assembly + compile() with checkpointer
│   │   ├── services/
│   │   │   ├── video_indexer.py       # Azure Video Indexer client (async, typed, retried)
│   │   │   ├── youtube.py             # yt-dlp wrapper with URL validation + size/duration guardrails
│   │   │   ├── vector_store.py        # Azure AI Search client wrapper
│   │   │   ├── storage.py             # Supabase Storage client (PDF upload)
│   │   │   └── pdf_export.py          # Report -> PDF rendering
│   │   └── jobs/
│   │       └── audit_runner.py        # Orchestrates a background audit job (calls graph, writes DB rows)
│   ├── scripts/
│   │   └── index_documents.py         # Existing offline PDF -> Azure AI Search ingestion (kept as-is, relocated if needed)
│   ├── data/                          # Existing regulatory PDFs used for RAG ingestion
│   ├── tests/
│   │   ├── unit/                      # Node-level and service-level tests with mocked Azure clients
│   │   ├── integration/               # FastAPI TestClient tests against real routes, test DB
│   │   └── eval/                      # Small golden-set RAG/LLM judgment eval
│   ├── alembic/                       # DB migrations (if adopted — see DATABASE_PLAN.md)
│   ├── pyproject.toml
│   ├── uv.lock
│   └── Dockerfile                     # Actually populated this time — single-stage, uv-based
│
├── docs/                               # All *.md planning/audit docs (this file's siblings)
│   ├── PROJECT_AUDIT.md
│   ├── MODERNIZATION_PLAN.md
│   └── ... (the rest of the modernization doc set)
│
├── .github/
│   └── workflows/
│       ├── backend-ci.yml             # lint + pytest on backend/ changes
│       └── frontend-ci.yml            # lint + typecheck + build on frontend/ changes
│
├── .env.example                        # Committed, blank placeholders only
├── .gitignore                          # Now correctly excludes .env, .venv, node_modules, .next
└── README.md                           # Real setup/run/deploy instructions
```

---

## Folder Responsibility Reference

### Frontend

| Folder | Responsibility |
|---|---|
| `app/(marketing)/` | Public pages reachable without login — the landing page is the entire sales pitch, must load fast and look premium immediately. |
| `app/(auth)/` | Supabase-Auth-backed login/signup screens, isolated from the dashboard layout. |
| `app/(dashboard)/` | Everything behind a session check: audit history, new-audit form, live tracker/report, settings. Route groups keep the URL clean (no `/dashboard/dashboard`). |
| `app/api/` | Only for concerns Next.js itself must own (auth callback redirect handling) — **not** a general API layer; all business logic calls go straight to the FastAPI backend via `lib/api-client.ts`. |
| `components/ui/` | shadcn/ui-generated primitives (Button, Card, Dialog, Table, Skeleton). Customized via Tailwind config, not forked/rewritten. |
| `components/audit/` | Domain-specific composed components (stage tracker, violation card, severity badge) — the vocabulary of this specific product. |
| `components/charts/` | Thin Recharts wrappers pre-configured with the product's color palette/typography so raw chart config never leaks into page components. |
| `components/chat/` | The AI chat panel's UI pieces, kept separate so the chat feature can be iterated on without touching report-rendering code. |
| `lib/api-client.ts` | The single place that knows the backend's base URL and attaches the Supabase JWT to every request — no component calls `fetch()` directly. |
| `lib/types.ts` | Hand-mirrored (or generated via `openapi-typescript` from the FastAPI OpenAPI schema) TypeScript types matching backend Pydantic models — keeps the frontend/backend contract explicit. |
| `hooks/` | Reusable stateful logic (polling a job's status, reading the current session) extracted out of page components. |
| `middleware.ts` | Redirects unauthenticated users away from `(dashboard)` routes at the edge, before a page even renders. |

### Backend

| Folder | Responsibility |
|---|---|
| `api/main.py` | Application factory: creates the `FastAPI()` instance, registers middleware (CORS, request-id), mounts routers. Nothing else lives here. |
| `api/deps.py` | Every `Depends(...)`-injected dependency (DB session, current user, settings) in one place, so routers stay declarative. |
| `api/routers/` | One file per resource, thin — routers call into `jobs/`/`graph/`/`services/`, they don't contain business logic themselves. |
| `core/config.py` | The **only** place `os.getenv` is called, via a Pydantic `BaseSettings` class — closes the audit finding about scattered, inconsistent env-var defaults. |
| `core/logging.py` | One structured-logging setup, replacing the audit's three competing `logging.basicConfig()` calls. |
| `core/security.py` | Supabase JWT verification — small, isolated, unit-testable in isolation from the rest of the app. |
| `db/models.py` | SQLModel table definitions — the single source of truth for `User`, `AuditJob`, `Report`, doubling as Pydantic schemas where convenient. |
| `db/session.py` | Engine/session creation, driven by `core/config.py`'s `DATABASE_URL` (SQLite path locally, Supabase Postgres URL in prod) — no connection logic duplicated elsewhere. |
| `schemas/` | Pydantic request/response contracts shared between the API layer and the LangGraph state — closes the audit's "`ComplianceIssue` defined twice" finding permanently. |
| `graph/` | The LangGraph pipeline itself — supervisor, five node modules, and the compiled workflow. See `AI_PIPELINE_VISION.md` for node-level detail. |
| `services/` | Thin, typed wrappers around every external system (Azure Video Indexer, yt-dlp, Azure AI Search, Supabase Storage, PDF rendering) — routers and graph nodes depend on these interfaces, never on raw SDK calls inline. |
| `jobs/audit_runner.py` | The glue between "an HTTP request created a job" and "the graph actually runs" — owns background-task submission, status updates, and error capture into the `audit_jobs` row. |
| `tests/unit` | Fast, mocked-dependency tests for individual nodes/services. |
| `tests/integration` | `TestClient`-driven tests hitting real routes against a throwaway SQLite test DB. |
| `tests/eval` | A small fixed set of (transcript, expected verdict) pairs to catch RAG/prompt regressions — not exhaustive, just a tripwire. |
| `scripts/` | Operator-run, one-off scripts (the existing PDF ingestion script) — never imported by the app itself. |
| `alembic/` | Schema migrations once the schema needs to evolve past its initial three tables (see `DATABASE_PLAN.md` for whether this is adopted immediately or deferred). |

### Root

| Folder/file | Responsibility |
|---|---|
| `docs/` | All planning and audit markdown — kept out of `frontend/`/`backend/` so neither app's tooling (Next.js, uv) ever has to think about it. |
| `.github/workflows/` | Two independent CI pipelines so a frontend-only change doesn't trigger a backend test run and vice versa. |
| `.env.example` | Documents every required variable with a blank value — replaces today's dual-purpose `.env` (see `TECHNICAL_DEBT.md` C2). |
| `README.md` | Real setup instructions: prerequisites, env vars, `uv run` / `npm run dev` commands, deploy steps. |
