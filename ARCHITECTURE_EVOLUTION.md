# ARCHITECTURE_EVOLUTION.md
## VidAuditFlow — Architecture Progression

This document shows the system's architecture at four points in time: **today**, and after **Phase 2**, **Phase 3**, and the **Final** target state. Each stage is additive — nothing from an earlier stage is thrown away, only extended. Detailed session-by-session sequencing lives in `IMPLEMENTATION_PHASES.md`; this document is the "shape of the system" view.

---

## Stage 0 — Current Architecture (as audited)

Single process, no persistence, no UI, no auth. See `PROJECT_AUDIT.md` for full findings.

```mermaid
flowchart TD
    CLI["main.py (CLI)"] --> GRAPH
    API["FastAPI /audit\n(async def, but blocks)"] --> GRAPH

    subgraph GRAPH["LangGraph — 2 nodes, linear"]
        IDX["indexer node"] --> AUD["auditor node"]
    end

    IDX --> YT[("YouTube\nvia yt-dlp")]
    IDX --> VI[("Azure Video Indexer")]
    AUD --> AOAI[("Azure OpenAI\nChat + Embeddings")]
    AUD --> SEARCH[("Azure AI Search")]

    style GRAPH fill:#1a1a1a,color:#fff
```

**Characteristics:** synchronous end-to-end, no database, no accounts, in-memory state only, single hardcoded video path, no UI.

---

## Stage 1 — Phase 2: Foundation Hardening (async + schema + auth skeleton)

Goal: make the *existing* shape safe and typed before adding new capability. No new user-facing features yet — this stage is invisible to an end user but removes every Critical defect from the audit.

```mermaid
flowchart TD
    CLIENT["Client (curl / Swagger)\nno UI yet"] --> AUTHMW

    subgraph API["FastAPI (fully async)"]
        AUTHMW["Auth dependency\n(verifies Supabase JWT)"] --> ROUTE["/audit route\n(async, await graph.ainvoke)"]
    end

    ROUTE --> GRAPH

    subgraph GRAPH["LangGraph — still 2 nodes, now async + typed"]
        IDX["indexer node\n(async httpx, per-session temp dir)"] --> AUD["auditor node\n(Pydantic-validated LLM output)"]
    end

    IDX --> YT[("YouTube")]
    IDX --> VI[("Azure Video Indexer")]
    AUD --> AOAI[("Azure OpenAI")]
    AUD --> SEARCH[("Azure AI Search")]

    subgraph SHARED["backend/src/schemas (new)"]
        SCHEMA["Single ComplianceIssue /\nAuditResult contract\nshared by API + graph"]
    end

    ROUTE -.imports.-> SCHEMA
    GRAPH -.imports.-> SCHEMA

    style API fill:#1a1a1a,color:#fff
    style GRAPH fill:#1a1a1a,color:#fff
```

**What changed:** async everywhere, per-request temp file isolation, one shared Pydantic schema module, an auth dependency wired but not yet backed by a real signup UI, `.env` hygiene fixed, timeouts/retries added to all outbound HTTP calls.

---

## Stage 2 — Phase 3: Data Layer + AI Pipeline v2

Goal: introduce persistence and upgrade the AI pipeline from "2 functions" to a legible supervisor + specialist-agent graph, still fully synchronous-free of external infrastructure (no queues, no k8s).

```mermaid
flowchart TD
    CLIENT["Frontend (early Next.js shell)"] -->|"POST /api/v1/audits"| API

    subgraph API["FastAPI"]
        AUTHMW["Auth dependency"] --> JOBROUTE["Jobs router\ncreates audit_job row"]
        JOBROUTE --> BG["BackgroundTasks\n(in-process, no external queue)"]
        STATUSROUTE["GET /api/v1/audits/{id}\n(poll for status)"]
    end

    BG --> SUPERVISOR

    subgraph SUPERVISOR_GRAPH["LangGraph — Supervisor + specialist nodes"]
        SUPERVISOR["Supervisor node\n(routes + aggregates)"]
        SUPERVISOR --> TRANSCRIPT["Transcript Agent"]
        SUPERVISOR --> OCR["OCR Agent"]
        TRANSCRIPT --> RETRIEVAL["Retrieval Agent"]
        OCR --> RETRIEVAL
        RETRIEVAL --> COMPLIANCE["Compliance Agent"]
        COMPLIANCE --> SUMMARY["Summary Agent"]
        SUMMARY --> SUPERVISOR
    end

    TRANSCRIPT --> VI[("Azure Video Indexer")]
    OCR --> VI
    RETRIEVAL --> SEARCH[("Azure AI Search")]
    COMPLIANCE --> AOAI[("Azure OpenAI Chat")]
    SUMMARY --> AOAI

    SUPERVISOR --> DB[("Postgres/SQLite\nvia SQLModel\nusers / audit_jobs / reports")]
    JOBROUTE --> DB
    STATUSROUTE --> DB

    style API fill:#1a1a1a,color:#fff
    style SUPERVISOR_GRAPH fill:#1a1a1a,color:#fff
```

**What changed:** `users`/`audit_jobs`/`reports` tables exist (SQLite locally); the 2-node graph becomes a supervisor with 5 specialist nodes (transcript + OCR now explicit and independently retryable, retrieval is its own node instead of 3 inline lines, summary is separated from compliance judgment); job creation returns immediately and the client polls status — no more request blocking on multi-minute Video Indexer processing.

---

## Stage 3 — Final Architecture (target)

Goal: the full product — real frontend, real auth, real storage, real exports, real observability.

```mermaid
flowchart TD
    subgraph VERCEL["Vercel — Next.js 15 Frontend"]
        LANDING["Landing / paste-URL page"]
        LIVE["Live audit tracker\n(stage-by-stage, polling/SSE)"]
        REPORT["Interactive report\n(violations, charts, timeline)"]
        CHAT["AI chat panel\n(scoped to report)"]
        EXPORT["PDF export"]
    end

    subgraph SUPA_AUTH["Supabase Auth"]
        JWT["JWT issuance"]
    end

    LANDING --> JWT
    JWT -->|"Bearer token"| BACKEND

    subgraph RENDER["Render/Railway — FastAPI Backend"]
        AUTHDEP["Auth dependency\n(verifies Supabase JWT)"]
        AUDITROUTER["/api/v1/audits\nCRUD + status"]
        CHATROUTER["/api/v1/chat\n(RAG over one report)"]
        EXPORTROUTER["/api/v1/reports/{id}/export"]
        AUTHDEP --> AUDITROUTER
        AUTHDEP --> CHATROUTER
        AUTHDEP --> EXPORTROUTER
    end

    LIVE -->|poll/SSE| AUDITROUTER
    REPORT --> AUDITROUTER
    CHAT --> CHATROUTER
    EXPORT --> EXPORTROUTER

    AUDITROUTER --> BG["In-process BackgroundTasks"]
    BG --> SUPERVISOR

    subgraph GRAPH["LangGraph — Supervisor + 5 agents\n(checkpointed, retryable per node)"]
        SUPERVISOR["Supervisor"]
        SUPERVISOR --> TRANSCRIPT["Transcript Agent"]
        SUPERVISOR --> OCR["OCR Agent"]
        TRANSCRIPT --> RETRIEVAL["Retrieval Agent"]
        OCR --> RETRIEVAL
        RETRIEVAL --> COMPLIANCE["Compliance Agent"]
        COMPLIANCE --> SUMMARY["Summary Agent"]
    end

    TRANSCRIPT --> VI[("Azure Video Indexer")]
    OCR --> VI
    RETRIEVAL --> SEARCH[("Azure AI Search")]
    COMPLIANCE --> AOAI[("Azure OpenAI Chat")]
    SUMMARY --> AOAI
    CHATROUTER --> AOAI
    CHATROUTER --> SEARCH

    SUPERVISOR --> PG[("Supabase Postgres\n(prod) / SQLite (dev)\nvia SQLModel")]
    AUDITROUTER --> PG
    CHATROUTER --> PG

    EXPORTROUTER --> STORAGE[("Supabase Storage\nexported PDFs")]

    BACKEND -.traces.-> LANGSMITH[("LangSmith")]
    BACKEND -.metrics/logs.-> MONITOR[("Azure Monitor")]

    style VERCEL fill:#0a0a0a,color:#fff
    style RENDER fill:#1a1a1a,color:#fff
    style GRAPH fill:#1a1a1a,color:#fff
```

**What changed from Stage 2:** full frontend experience, chat is its own RAG surface scoped to a completed report (reuses the Retrieval Agent's pattern, not a new pipeline), exports write to Supabase Storage instead of being generated on-the-fly only, and both LangSmith and Azure Monitor are load-bearing observability (not optional env-var-only integrations).

---

## What deliberately never appears in any stage

To keep this evolution honest about its own constraints:

- No Kubernetes / container orchestration at any stage.
- No message broker (Kafka/RabbitMQ/SQS) at any stage — `BackgroundTasks` inside the single FastAPI process is sufficient at this scale, since audits are seconds-to-minutes, not hours, and volume is portfolio-demo scale, not production-enterprise scale.
- No microservice split — "backend" is one deployable FastAPI app in every stage.
- No self-hosted vector DB or self-hosted LLM — Azure AI Search and Azure OpenAI remain external managed services throughout.
