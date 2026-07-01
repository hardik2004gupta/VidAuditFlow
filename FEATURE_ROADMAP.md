# FEATURE_ROADMAP.md
## VidAuditFlow — Feature Prioritization

Complexity is rated Low / Medium / High relative to this project's scale (not relative to enterprise software). Effort is in Claude-Code-session-equivalents (see `IMPLEMENTATION_PHASES.md`).

---

## Must Have

Foundation without which the product does not function or cannot be honestly called "production-aware."

### 1. Async, non-blocking audit execution
- **Purpose:** Fix the event-loop-blocking defect (audit C1) so the API can serve more than one request at a time.
- **Complexity:** Medium — requires converting `VideoIndexerService` to async HTTP and switching to `ainvoke`.
- **Estimated effort:** 1 session.
- **Business value:** Without this, the product cannot demo two audits back-to-back without one hanging the other — a portfolio-killing bug if triggered live.

### 2. Authentication (Supabase Auth)
- **Purpose:** Gate AI-triggering endpoints behind real accounts; enable per-user history.
- **Complexity:** Medium.
- **Estimated effort:** 1–2 sessions.
- **Business value:** Turns an open API anyone can spam into an actual product with users; required before persistence means anything.

### 3. Persistence layer (SQLModel + SQLite/Postgres)
- **Purpose:** Store `users`, `audit_jobs`, `reports` so results outlive one HTTP request.
- **Complexity:** Medium.
- **Estimated effort:** 2 sessions.
- **Business value:** Enables history, re-visiting a report, and everything downstream (chat, export) that needs a report to still exist later.

### 4. Background job execution + status polling
- **Purpose:** Return immediately from "start an audit" and let the client poll/stream progress instead of holding an HTTP connection open for minutes.
- **Complexity:** Medium.
- **Estimated effort:** 1–2 sessions.
- **Business value:** This is the difference between "feels broken" and "feels like a real async product" given Azure Video Indexer's multi-minute processing time.

### 5. Paste-URL landing page + audit kickoff flow
- **Purpose:** The core, single most important user interaction in the entire product.
- **Complexity:** Low–Medium.
- **Estimated effort:** 1 session.
- **Business value:** This is the first thing a reviewer sees — it has to look intentional and confident.

### 6. Live audit progress tracker (stage-by-stage UI)
- **Purpose:** Visualize the supervisor/agent pipeline running in real time (Downloading → Transcribing → OCR → Retrieving Policies → Analyzing → Summarizing).
- **Complexity:** Medium.
- **Estimated effort:** 2 sessions.
- **Business value:** This single screen is the clearest demonstration of "this person built a real multi-agent pipeline," which is the entire point of a portfolio piece.

### 7. Interactive compliance report view
- **Purpose:** Render violations, severity, and a summary in a clean, scannable UI instead of raw JSON.
- **Complexity:** Medium.
- **Estimated effort:** 2 sessions.
- **Business value:** This is "the product" from the user's point of view — everything else supports this screen.

### 8. Supervisor + specialist-agent LangGraph redesign
- **Purpose:** Replace the 2-function graph with a legible supervisor + 5-node graph (Transcript, OCR, Retrieval, Compliance, Summary agents).
- **Complexity:** Medium–High.
- **Estimated effort:** 3 sessions.
- **Business value:** This is the single biggest AI-engineering credibility signal in the whole project — see `AI_PIPELINE_VISION.md`.

### 9. Structured-output validation on LLM responses
- **Purpose:** Replace raw `json.loads()` with Pydantic-validated structured output (audit finding M5).
- **Complexity:** Low–Medium.
- **Estimated effort:** 1 session.
- **Business value:** Prevents a malformed LLM response from silently producing a broken report — directly protects the "polished" perception.

### 10. `.env` hygiene + secrets discipline
- **Purpose:** Close the un-ignored `.env` gap (audit C2) before any real credentials exist.
- **Complexity:** Low.
- **Estimated effort:** <1 session (bundle into Phase 1).
- **Business value:** A leaked Azure key is an instant credibility (and cost) disaster — this is the cheapest possible fix with the highest downside avoidance.

### 11. Test suite + CI
- **Purpose:** Real `pytest` coverage (unit + integration) running in GitHub Actions on every push.
- **Complexity:** Medium.
- **Estimated effort:** 2 sessions.
- **Business value:** "Has tests and CI" is a baseline expectation for anything called production-aware; its absence is the loudest red flag in the current audit.

---

## Should Have

Meaningfully improves the product but the MVP is coherent without them on day one.

### 12. AI chat panel scoped to a report
- **Purpose:** Let a user ask follow-up questions ("why was this flagged?", "what rule does this violate?") grounded in that specific report's retrieved policy chunks.
- **Complexity:** Medium.
- **Estimated effort:** 2 sessions.
- **Business value:** Strong differentiator vs. a static report — demonstrates RAG reused as a conversational surface, not just a one-shot classifier.

### 13. PDF export
- **Purpose:** Let a user download a shareable compliance report.
- **Complexity:** Low–Medium.
- **Estimated effort:** 1 session.
- **Business value:** Makes the product feel "real" (something you'd actually hand to a legal/marketing team) rather than a web-only toy.

### 14. Charts and timeline visualization (Recharts)
- **Purpose:** A compliance-score gauge, a violations-by-severity bar chart, and a transcript timeline marking where in the video violations occur.
- **Complexity:** Medium.
- **Estimated effort:** 1–2 sessions.
- **Business value:** Visual data storytelling is a strong "senior engineer" and "product sense" signal for a portfolio reviewer.

### 15. Per-node retry policy + checkpointing in LangGraph
- **Purpose:** Close audit findings M7 (no retry policy) and the "no resumability" gap — a transient Azure 429 shouldn't fail an entire multi-minute audit.
- **Complexity:** Medium.
- **Estimated effort:** 1 session.
- **Business value:** Real reliability engineering, visible in the architecture doc even if rarely triggered live.

### 16. Citation-aware compliance report (surface the source PDF/clause)
- **Purpose:** Close audit finding M12 — retrieved chunk metadata (`source`) is currently discarded; surface "per the YouTube Ad Specs guide, section X" in the report.
- **Complexity:** Low–Medium.
- **Estimated effort:** 1 session.
- **Business value:** Turns "the AI said so" into "the AI said so, citing this specific rule" — a credibility multiplier for a compliance product specifically.

### 17. Rate limiting / per-user quota
- **Purpose:** Prevent runaway Azure spend from a public demo link.
- **Complexity:** Low.
- **Estimated effort:** 1 session.
- **Business value:** Protects the (small) budget this project runs on; also a "production awareness" signal.

### 18. Dark theme + full responsive polish pass
- **Purpose:** Match the Vercel/Linear/OpenAI-inspired visual bar described in `UI_VISION.md` across breakpoints.
- **Complexity:** Medium.
- **Estimated effort:** 2 sessions.
- **Business value:** Visual craft is scrutinized heavily in portfolio review; this is where "looks like a tutorial" vs. "looks like a startup" is decided.

---

## Nice to Have

Real value, deliberately sequenced after the above; skipping these does not compromise the core pitch.

### 19. Email notification when an audit completes
- **Purpose:** Let a user close the tab and get notified instead of waiting.
- **Complexity:** Low–Medium (Supabase + a transactional email provider).
- **Estimated effort:** 1 session.
- **Business value:** Nice UX touch; not core to the demo narrative.

### 20. Shareable public report links
- **Purpose:** Generate a read-only public URL for a report (e.g., to share with a brand team).
- **Complexity:** Medium (requires access-control design even for "public" links).
- **Estimated effort:** 1 session.
- **Business value:** Realistic SaaS feature, good portfolio talking point, not required for the core demo loop.

### 21. Audit history filtering/search
- **Purpose:** Search/filter past audits by status, date, severity.
- **Complexity:** Low.
- **Estimated effort:** 1 session.
- **Business value:** Useful once a user has more than ~5 audits; low urgency for a demo account.

### 22. Command palette (Cmd+K) navigation
- **Purpose:** Linear-style power-user navigation.
- **Complexity:** Low–Medium (shadcn/ui has a `Command` primitive).
- **Estimated effort:** 1 session.
- **Business value:** A small but recognizable "this person studies great products" signal for reviewers familiar with Linear/Vercel.

### 23. Multi-video batch audits
- **Purpose:** Submit several YouTube URLs at once.
- **Complexity:** Medium (queueing multiple background jobs, aggregate view).
- **Estimated effort:** 2 sessions.
- **Business value:** Realistic for an actual brand-compliance team's workflow; not needed to prove the concept.

---

## Future

Explicitly deferred — parked here specifically so they don't creep into the current scope (see `MODERNIZATION_PLAN.md` Non-Goals).

### 24. Additional platform support (TikTok, Instagram Reels, raw file upload)
- **Purpose:** Broaden ingestion beyond YouTube.
- **Complexity:** High (each platform has different extraction quirks; raw upload needs its own storage/virus-scan story).
- **Estimated effort:** 3+ sessions per platform.
- **Business value:** Real product expansion, but orthogonal to proving the core AI-pipeline/UX concept.

### 25. Org accounts, team roles, seat-based billing
- **Purpose:** Multi-user organizations with shared audit history and permissions.
- **Complexity:** High.
- **Estimated effort:** 4+ sessions.
- **Business value:** This is where the product would start looking like the "enterprise banking platform" this plan explicitly avoids — valuable someday, wrong for a portfolio-scale MVP.

### 26. Custom/fine-tuned compliance model
- **Purpose:** Replace general Azure OpenAI prompting with a model tuned specifically on compliance judgments.
- **Complexity:** Very High (requires a labeled dataset, training/eval infra).
- **Estimated effort:** Out of scope for session-based estimation.
- **Business value:** Real differentiator at scale; unjustifiable effort for a portfolio project's current data volume.

### 27. Self-serve billing (Stripe integration)
- **Purpose:** Monetize the product.
- **Complexity:** Medium–High.
- **Estimated effort:** 2–3 sessions.
- **Business value:** Only relevant if this becomes a real business rather than a portfolio artifact — deliberately deferred.

### 28. Webhook/API access for third-party integration
- **Purpose:** Let external systems (e.g., a brand's CMS) trigger audits programmatically.
- **Complexity:** Medium.
- **Estimated effort:** 1–2 sessions.
- **Business value:** Real B2B feature, not needed to demonstrate the core product.
