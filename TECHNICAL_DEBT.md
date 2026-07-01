# TECHNICAL_DEBT.md
## VidAuditFlow — Prioritized Technical Debt Register

Source: every finding in `PROJECT_AUDIT.md`, re-organized by priority with a recommended fix and effort estimate. Effort is in Claude-Code-session-equivalents. Cross-references to `IMPLEMENTATION_PHASES.md` show where each item is actually resolved.

---

## Critical

### TD-1. Synchronous call blocks the async event loop (audit C1)
- **Why it matters:** the entire API can serve exactly one request at a time while any audit is running — a multi-minute window given Azure Video Indexer's processing time. This is the single defect most likely to visibly break a live demo.
- **Recommended solution:** convert `VideoIndexerService` to `httpx.AsyncClient`; call `compliance_graph.ainvoke()` instead of `.invoke()`.
- **Estimated effort:** 1 session. — **Resolved in:** Phase 1.

### TD-2. `.env` not excluded by `.gitignore` (audit C2)
- **Why it matters:** the first commit with real credentials filled in permanently leaks them into git history; this repo currently has zero commits, making this the cheapest possible moment to fix it.
- **Recommended solution:** add `.env` to `.gitignore`; replace the current blank `.env` with a committed `.env.example`.
- **Estimated effort:** <1 session. — **Resolved in:** Phase 0.

### TD-3. Hardcoded, shared temp filename causes cross-request race conditions (audit C3)
- **Why it matters:** concurrent audits (once TD-1 is fixed and concurrency is actually possible) will corrupt or cross-contaminate each other's video files.
- **Recommended solution:** derive temp paths from `video_id`/job id via `tempfile.mkdtemp()`.
- **Estimated effort:** bundled with TD-1. — **Resolved in:** Phase 1.

### TD-4. No authentication on any endpoint (audit C4)
- **Why it matters:** any caller can trigger billable Azure Video Indexer/OpenAI usage with no cost control, and there is no concept of "whose audit is this" without it.
- **Recommended solution:** Supabase Auth + JWT verification dependency on every business route.
- **Estimated effort:** 1–2 sessions. — **Resolved in:** Phase 8, enforced from Phase 9 onward.

### TD-5. Unbounded polling loop with no timeout (audit C5)
- **Why it matters:** a stuck Azure Video Indexer job hangs the request forever, and — combined with TD-1 before it's fixed — hangs the entire server.
- **Recommended solution:** bounded max-attempts + overall timeout in `wait_for_processing()`, wrapped in the shared retry policy.
- **Estimated effort:** bundled into the Transcript Agent rebuild. — **Resolved in:** Phase 10.

### TD-6. Zero automated tests (audit C6)
- **Why it matters:** every refactor in this entire modernization plan is a leap of faith without a test suite; this is the highest-leverage investment for de-risking everything that follows it.
- **Recommended solution:** `pytest` unit + integration suite, run in CI.
- **Estimated effort:** 2 sessions initial + ongoing additions per phase. — **Resolved in:** Phase 5 (foundation), extended through every subsequent phase.

### TD-7. Non-functional deployment targets — empty Dockerfile and Azure Functions scaffold (audit C7)
- **Why it matters:** neither of the project's two apparent deployment paths actually works; the project cannot be deployed today.
- **Recommended solution:** populate `backend/Dockerfile` for real; delete the unused `azure_functions/` scaffold entirely rather than leaving dead placeholders (Azure Functions is not part of the target stack — see `MODERNIZATION_PLAN.md`).
- **Estimated effort:** 1 session for Dockerfile; <1 session to delete the Functions scaffold. — **Resolved in:** Phase 12 (Dockerfile); Functions scaffold removal can happen as a trivial cleanup in the same phase.

---

## High

### TD-8. Six unused dependencies inflate the install/attack surface
- **Why it matters:** `streamlit`, `redis`, `sqlalchemy`, `psycopg2-binary`, `firecrawl-py`, `pandas` are declared but never imported — dead weight with no functional benefit, and each is a future CVE surface for no reason.
- **Recommended solution:** remove all six from `pyproject.toml`. Note: `sqlalchemy`/`psycopg2-binary` become *legitimately* needed once SQLModel/Postgres land (Phase 7) — re-add deliberately at that point rather than assuming the existing declarations were "already handling it" (they weren't wired to anything).
- **Estimated effort:** <1 session. — **Resolved in:** cleanup pass alongside Phase 4 (config) or Phase 7 (DB layer, where the real DB deps are re-added correctly).

### TD-9. Duplicated `ComplianceIssue` schema (audit M4)
- **Why it matters:** the graph's `TypedDict` and the API's `BaseModel` can drift silently — a field added to one won't propagate to the other, and nothing will catch it without a shared-schema test.
- **Recommended solution:** one Pydantic model in `schemas/audit.py`, imported by both layers.
- **Estimated effort:** 1 session. — **Resolved in:** Phase 2.

### TD-10. No structured-output validation on LLM responses (audit M5, M6)
- **Why it matters:** a malformed LLM response either silently produces a broken report or throws an unhandled `AttributeError` from the regex fence-stripping logic.
- **Recommended solution:** `with_structured_output()` against the Phase-2 schema, with one automatic re-prompt on validation failure.
- **Estimated effort:** 1 session. — **Resolved in:** Phase 3.

### TD-11. No outbound HTTP timeouts anywhere (audit M3)
- **Why it matters:** any hung TCP connection to Azure hangs the calling thread/request indefinitely.
- **Recommended solution:** explicit timeout on every `httpx`/`requests` call, defined once in `core/config.py`.
- **Estimated effort:** bundled with TD-1. — **Resolved in:** Phase 1.

### TD-12. No retry policy on any node (audit M7)
- **Why it matters:** a single transient 429/500 from Azure fails an entire multi-minute audit with no automatic recovery.
- **Recommended solution:** LangGraph `RetryPolicy` on every node making external calls.
- **Estimated effort:** 1 session. — **Resolved in:** Phase 11.

### TD-13. Soft SSRF via substring YouTube-URL check
- **Why it matters:** `"youtube.com" in video_url` can be satisfied by a crafted malicious URL, which is then handed to `yt-dlp` (which supports many extractors beyond YouTube).
- **Recommended solution:** real URL parsing + exact host allow-list at the Pydantic validation layer, before any business logic runs.
- **Estimated effort:** bundled with TD-10. — **Resolved in:** Phase 3.

### TD-14. Verbose internal error messages returned to API clients
- **Why it matters:** raw exception text (potentially including partial Azure SDK error payloads) is exposed to any caller.
- **Recommended solution:** standard error envelope (`{"error": {"code", "message"}}`); log full details internally with a request id, return only the safe message externally.
- **Estimated effort:** 1 session. — **Resolved in:** Phase 9 (introduced alongside the new jobs API), applied consistently thereafter.

---

## Medium

### TD-15. Hardcoded embedding deployment name drifts from ingestion config (audit M2)
- **Why it matters:** query-time and index-time embeddings could silently use two different models against the same vector index, corrupting similarity search with no visible error.
- **Recommended solution:** single `AZURE_OPENAI_EMBEDDING_DEPLOYMENT` setting read from `core/config.py` everywhere, no per-file fallback strings.
- **Estimated effort:** bundled with config centralization. — **Resolved in:** Phase 4.

### TD-16. Deprecated `langchain_community.vectorstores.AzureSearch` wrapper (audit M10)
- **Why it matters:** on a deprecation trajectory in the LangChain ecosystem; works today but is a slow-burning maintenance risk.
- **Recommended solution:** migrate to the actively maintained `langchain-azure-ai` integration (or native `azure-search-documents` calls) when touching the Retrieval Agent.
- **Estimated effort:** 1 session. — **Resolved in:** Phase 11 (natural to fold into the Retrieval Agent extraction).

### TD-17. Fixed `k=3` retrieval, no reranking, no relevance threshold, discarded citations (audit M11, M12)
- **Why it matters:** retrieval quality is unmeasured and citations — specifically tagged "for citation later" in the ingestion script's own comment — are computed and then thrown away, wasting the compliance product's most credible feature (naming the exact rule violated).
- **Recommended solution:** preserve `metadata.source` through Retrieval → Compliance → report; consider a minimum-relevance-score cutoff.
- **Estimated effort:** 1 session. — **Resolved in:** Phase 11.

### TD-18. No prompt-injection hardening on transcript/OCR content
- **Why it matters:** transcript/OCR text originates from attacker-influenceable video content and is interpolated verbatim into the compliance prompt.
- **Recommended solution:** explicit delimiters + a system instruction that content inside the transcript/OCR block is untrusted data, not instructions.
- **Estimated effort:** bundled with the Compliance Agent build. — **Resolved in:** Phase 11.

### TD-19. Unbounded prompt size for long transcripts
- **Why it matters:** a long video's full transcript concatenated into one embedding query and one LLM call risks context-window overflow and cost blowups with no truncation/summarization strategy.
- **Recommended solution:** token-budgeted truncation/claim-prioritization heuristic in the Retrieval Agent's query construction.
- **Estimated effort:** 1 session. — **Resolved in:** Phase 11.

### TD-20. Azure AD token churn in the polling loop
- **Why it matters:** fetching a fresh ARM + Video Indexer account token on every 30-second poll iteration is wasted load with no benefit.
- **Recommended solution:** cache tokens until near expiry.
- **Estimated effort:** <1 session. — **Resolved in:** Phase 10 (Transcript Agent rebuild).

### TD-21. `yt-dlp` format unconstrained, no size/duration cap (audit M8)
- **Why it matters:** a long/high-resolution video downloads the largest available stream with no guardrail, directly worsening the already-long Video Indexer processing time.
- **Recommended solution:** cap format selection and reject videos exceeding a configured max duration at validation time.
- **Estimated effort:** 1 session. — **Resolved in:** Phase 10.

### TD-22. Inconsistent auth model across Azure services
- **Why it matters:** Video Indexer uses `DefaultAzureCredential` while Azure OpenAI/Search use static API keys — inconsistent security posture for services that all support managed identity.
- **Recommended solution:** standardize on managed identity across all three where the deployment target supports it; acceptable to defer if Render/Railway managed-identity support is impractical, but document the decision explicitly rather than leaving it as an unexamined inconsistency.
- **Estimated effort:** 1 session (evaluation) + 1 session (migration, if pursued). — **Target:** evaluated during Phase 12 deployment planning; may be deferred to Future if platform constraints make it impractical.

---

## Low

### TD-23. Logging configuration called redundantly in three places (audit L1, L2)
- **Why it matters:** only the first `logging.basicConfig()` call actually takes effect; the rest are dead code, and five inconsistent logger names complicate log filtering.
- **Recommended solution:** single `core/logging.py` setup, consistent module-path-based logger names.
- **Estimated effort:** bundled with config centralization. — **Resolved in:** Phase 4.

### TD-24. Unused import and print-statement typo in `main.py` (audit L3, L4)
- **Why it matters:** minor code-cleanliness debt, no functional impact.
- **Recommended solution:** remove the unused `pprint` import; fix the "1.nput" typo.
- **Estimated effort:** trivial (<15 min). — **Resolved in:** any convenient cleanup pass, e.g., Phase 4.

### TD-25. Tutorial-style comments throughout core modules (audit L5)
- **Why it matters:** appropriate for a learning exercise, but reads as unprofessional in a portfolio-quality codebase.
- **Recommended solution:** pass over `main.py`, `server.py`, `telemetry.py` replacing narrative comments with concise, decision-oriented ones (or none) as those files are touched during the relevant phases — not a dedicated standalone phase.
- **Estimated effort:** incremental, folded into Phases 1–4 as those files are edited anyway.

### TD-26. `backend/scripts/explanation.txt` is a personal note, not documentation (audit L6)
- **Why it matters:** organizational miscategorization; not harmful, just noise.
- **Recommended solution:** delete it; fold anything worth keeping into the real `README.md`.
- **Estimated effort:** trivial. — **Resolved in:** Phase 20 (README pass).

### TD-27. No linter/formatter/pre-commit config (audit L7)
- **Why it matters:** `pyproject.toml` exists but only pins dependencies, not code-quality tooling.
- **Recommended solution:** add `ruff` (lint + format) config; wire into CI (Phase 6).
- **Estimated effort:** <1 session. — **Resolved in:** Phase 6.

### TD-28. No URL type validation on the request model (audit L8)
- **Why it matters:** `video_url: str` accepts any string; failure happens deep in business logic instead of at the API boundary.
- **Recommended solution:** covered by TD-13's fix (real URL validation) — no separate work needed.
- **Estimated effort:** $0 additional (already covered). — **Resolved in:** Phase 3.

### TD-29. Hardcoded `"platform": "youtube"` in extraction (audit L9)
- **Why it matters:** dead/redundant given the existing YouTube-only gate; harmless today, would need attention if other platforms are added (Future roadmap item).
- **Recommended solution:** leave as-is until multi-platform support (`FEATURE_ROADMAP.md` → Future) is actually built; not worth touching before then.
- **Estimated effort:** N/A until relevant.

### TD-30. No version/build identifier on `/health` (audit L10)
- **Why it matters:** complicates "which version is deployed" triage.
- **Recommended solution:** add `version` field to the health response, sourced from a `pyproject.toml` version or git SHA at build time.
- **Estimated effort:** trivial. — **Resolved in:** Phase 12 (deployment).

---

## Priority Summary Table

| Priority | Count | Total estimated effort |
|---|---|---|
| Critical | 7 | ~7–8 sessions |
| High | 7 | ~6–7 sessions |
| Medium | 8 | ~7–8 sessions |
| Low | 8 | ~1–2 sessions |

This matches (and is the detailed backing for) the effort distribution in `MODERNIZATION_PLAN.md`'s timeline — the Critical + High items alone justify the first ~9 phases of `IMPLEMENTATION_PHASES.md` before any new user-facing feature work begins.
