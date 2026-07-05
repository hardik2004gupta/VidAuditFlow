# Phase 6 Summary — Polish & Backend Integration

**Scope:** replace the Phase 5 mock data layer with the real FastAPI backend, upgrade typography and visual polish toward a Vercel/Linear/Raycast-grade finish, and verify the whole thing end-to-end against a genuinely running backend. No redesign, no new pages, no authentication, no architecture changes — per this phase's explicit brief.

---

## 1. Files Changed

### Backend (minimal, additive only — no endpoint changes)
- [`backend/src/core/config.py`](backend/src/core/config.py) — added `cors_allowed_origins` setting (+ `cors_allowed_origins_list` property).
- [`backend/src/api/main.py`](backend/src/api/main.py) — added `CORSMiddleware`, exact allow-list (no wildcard), per `API_PLAN.md`'s CORS section.

### Frontend — new files
- [`frontend/lib/api.ts`](frontend/lib/api.ts) — the real API client (replaces `lib/mock/`).
- [`frontend/hooks/use-audit-job-polling.ts`](frontend/hooks/use-audit-job-polling.ts) — replaces `use-simulated-audit-progress.ts`.
- [`frontend/components/shared/error-state.tsx`](frontend/components/shared/error-state.tsx) — inline query-error treatment (EmptyState's error-path counterpart).
- `frontend/.env.local` / `.env.example` — `NEXT_PUBLIC_API_URL`.

### Frontend — rewired to the real client
- `features/dashboard/components/dashboard-metrics.tsx`, `recent-audits-card.tsx`, `recent-reports-card.tsx`
- `features/reports/components/reports-table.tsx`
- `app/(dashboard)/reports/[id]/page.tsx`
- `features/audits/components/new-audit-form.tsx` (rewritten: real `createAudit` mutation + `useAuditJobPolling`)
- `features/audits/components/stage-tracker.tsx` (new `error` stage state, retyped against `StageProgress`)

### Frontend — deleted
- `lib/mock/` (api.ts, audits.ts, reports.ts, index.ts)
- `hooks/use-simulated-audit-progress.ts`

### Frontend — typography & visual polish
- `app/globals.css` — base heading letter-spacing/line-height/weight rules, body line-height, shimmer-skeleton keyframes.
- `components/ui/skeleton.tsx` — shimmer sweep instead of a flat opacity pulse.
- `components/ui/card.tsx` — `CardTitle` bumped to semibold + tracking-tight (H3 scale).
- `components/ui/button.tsx` — added `tracking-tight` to button labels.
- `components/ui/table.tsx` — Stripe-style header row (uppercase, tracked-out, muted), taller row padding, explicit hover transition duration.
- `components/ui/dialog.tsx` — `rounded-xl`/`ring-1` → consistent `rounded-lg` + `border-border` + `shadow-lg`; `DialogTitle` bumped to semibold/tracking-tight; padding bumped to match card spacing.
- `components/ui/dropdown-menu.tsx`, `components/ui/select.tsx` — same border/radius normalization as dialogs.
- `components/layout/page-header.tsx` — H1 resized (26px → 30px) to sit inside UI_VISION.md's 28–32px band.

---

## 2. Backend Integration

**Endpoints wired** (exactly the four requested, no new/changed backend routes):

| Function (`lib/api.ts`) | Endpoint |
|---|---|
| `fetchAuditJobs()` | `GET /api/v1/audits` |
| `fetchAuditJob(id)` | `GET /api/v1/audits/{id}` |
| `createAudit(url)` | `POST /api/v1/audits` |
| `fetchReport(id)` | `GET /api/v1/reports/{id}` |
| `fetchReports()` | *(composed, see below)* |

**No list-reports endpoint exists** (`API_PLAN.md` only documents single-report fetch by id). `fetchReports()` is composed client-side: list audit jobs, keep the ones with a `report_id`, fetch each report with `Promise.allSettled` (one failed fetch doesn't blank the whole list), sort newest-first. This exact same function name/shape already existed in the Phase 5 mock layer, so no calling component needed to change.

**Error handling.** `apiFetch()` in `lib/api.ts` normalizes both of the backend's error shapes — its own `{"error": {"code", "message"}}` envelope and FastAPI's default `422` `{"detail": [...]}` — into a single `ApiError` (with `.status`/`.code`), plus a distinct network-failure case ("Is the backend running?"). Every list/card component now branches on `isError` and renders the new `ErrorState` component with a retry button; the report detail page (an async Server Component) catches a `404 ApiError` and calls `notFound()`, letting any other error fall through to the existing `(dashboard)/error.tsx` boundary from Phase 5.

**CORS.** The backend had no CORS middleware at all before this phase — the browser could not have called it. Added `CORSMiddleware` with an exact origin allow-list (`http://localhost:3000` by default, configurable via `CORS_ALLOWED_ORIGINS`), matching `API_PLAN.md`'s explicit "no wildcard, ever" rule.

**Audit Tracker polling.** `useAuditJobPolling(jobId)` wraps `useQuery` with `refetchInterval: (query) => isTerminal(status) ? false : 2000` — polling `GET /api/v1/audits/{id}` every 2 seconds until the job reaches `completed`, `completed_degraded`, `failed`, or `cancelled`, exactly as this phase specified. It maps the job's `current_stage` (a human-readable label, matching `PIPELINE_STAGES` verbatim) and `status` onto the same `StageTracker` component from Phase 5 — no UI was rebuilt, only its data source and a new fourth stage state (`"error"`, a red X icon) to honestly represent a failed stage instead of leaving it spinning forever.

**Real per-stage timing is not available while a job is in flight** — `GET /api/v1/audits/{id}` reports only the current stage label, not a start/end timestamp per stage (that detail only exists in the finished Report's `processing_metadata`). `elapsedSeconds` is `null` for every stage during live polling; the Report Viewer's separate `StageTimeline` component still shows full, real per-stage durations once a report exists, since that data does come from `processing_metadata`.

---

## 3. Typography Improvements

- **Font:** Geist Sans / Geist Mono were already wired via `next/font/google` in Phase 5 — nothing to swap. The actual "feels dated" problem was the *absence* of a systematized scale, not the font family.
- **Global base rules** (`globals.css`): `h1`/`h2`/`h3` now get `-0.02em` letter-spacing and a `1.15` line-height by default, instead of every call site repeating `tracking-tight leading-tight` ad hoc. Body line-height set to `1.6` (UI_VISION.md's "generous line-height" rule). Added `font-feature-settings: "cv11", "ss01"` for Geist's crisper contextual alternates.
- **Hierarchy fixes:** `CardTitle` and `DialogTitle` were `font-medium` (500) — bumped to `font-semibold` (600) with `tracking-tight`, matching UI_VISION.md's H3 spec ("16–17px / 600"). `PageHeader`'s H1 resized from 24→28px to 26→30px, landing inside the documented 28–32px band at both ends.
- **Tables:** header cells were the same size/weight/color as body text (no visual hierarchy at all between header and data). Now `text-xs font-medium tracking-wide uppercase text-muted-foreground` — the Stripe-Dashboard convention UI_VISION.md explicitly calls for — with taller cell padding (`py-3.5`) for a proper 48–52px row height instead of the previous ~40px.
- **Monospace/technical values:** `.font-technical` now also carries `-0.01em` tracking so IDs/timestamps read a touch tighter, matching Geist Mono's intended feel.
- **Buttons:** added `tracking-tight` to button label text for crisper CTAs.

---

## 4. UI Improvements

- **Loading states:** `Skeleton` switched from a flat `animate-pulse` opacity fade to a sweeping shimmer gradient (`@keyframes shimmer`, respecting the existing global `prefers-reduced-motion` override) — a more premium, Linear/Vercel-style loading signal.
- **Elevated surfaces normalized:** dialogs, dropdown menus, and selects previously mixed `rounded-xl` + `ring-1 ring-foreground/10` (left over from the shadcn default, inconsistent with UI_VISION.md's "consistent rounded-lg, no mixed radii" rule). All three now use `rounded-lg` + `border border-border`, with `shadow-lg`/`shadow-md` kept only on these genuinely elevated layers, per the spec's one sanctioned exception to "borders over shadows."
- **Tables:** Stripe-style header treatment (see above), explicit `duration-150` on row hover to match UI_VISION.md's documented micro-interaction timing, softened hover tint (`bg-muted/40`).
- **Audit Tracker failure state:** added a fourth, honest `"error"` stage state (red `XCircle`, red connecting line) instead of a failed pipeline leaving its last stage stuck mid-spin indefinitely.

---

## 5. Quality Verification

- `npm run build` (Turbopack) — compiles cleanly, all 7 routes generated, zero TypeScript/ESLint errors.
- `npx tsc --noEmit` — clean.
- **Live end-to-end integration test**, backend actually running (`uv run uvicorn backend.src.api.main:app --port 8000`), no mocking:
  1. `GET /api/v1/audits` on a fresh, empty SQLite DB → dashboard and reports list correctly render their empty states (real network round-trip, not a fixture).
  2. Submitted a real YouTube URL via the New Audit form → `POST /api/v1/audits` created a job (`202`) → `useAuditJobPolling` polled `GET /api/v1/audits/{id}` every 2s and animated through real stage transitions as the backend genuinely downloaded the video via `yt-dlp`.
  3. Since this environment has no real Azure credentials configured, the pipeline failed at transcript/OCR extraction as expected — and the Audit Tracker correctly rendered the new failed/error state with the exact backend `error_message` (a real `DefaultAzureCredential` failure), not a placeholder.
  4. Discovered live (not from a fixture) that the backend's graceful-degradation path (`summary_agent.py`) still generates a `Report` even for a `status: "failed"` job — `confidence_score`/`risk_level` come back `null` and `video_metadata` comes back `{}`. Verified the Report Viewer handles this real shape without crashing: `ComplianceScoreCard` is correctly omitted (already gated on non-null score/risk), `ViolationTable`/`SourcesPanel` render their empty states, and the `WarningsBanner` surfaces the degradation reason.
  5. Confirmed CORS headers (`access-control-allow-origin: http://localhost:3000`) present on a real cross-origin request from the browser preview.
- **Responsive + theme check:** dashboard, reports list, and report viewer re-verified at 1280×900 and 375×812, and in both dark and light mode, using this same live data (not fixtures) — table header/typography upgrades hold up at mobile width, light mode contrast is correct.

---

## 6. Known Limitations

- **No successful pipeline run was demonstrated.** This environment has no real Azure OpenAI / Video Indexer / AI Search credentials, so no audit can reach `completed`/`completed_degraded` with real violations, a real compliance score, or real sources. The `failed`-with-degraded-report path was verified live instead (Section 5), which exercises the same API contract, error handling, and null-field rendering a successful run would — but a reviewer wanting to see a fully populated, real (non-mock) report will need real Azure credentials in `.env`.
- **`video_metadata` can be an empty object at runtime** (`Dict[str, Any]` on the backend, not always populated) even though the frontend's `VideoMetadata` type declares `platform: string` as always present. In this failure path it renders as a blank line rather than "undefined" (React renders `undefined` as nothing), so there's no crash — but the type is technically optimistic versus what a very-early pipeline failure can produce. Not fixed in this phase to keep changes localized; worth a narrower `Partial<VideoMetadata>` type if this edge case matters later.
- **No per-stage elapsed time during live polling** (see Section 2) — only after a report exists. This is a real backend data-availability gap, not a frontend simplification that can be fixed client-side without a backend schema change (out of scope: "do not change backend endpoints").
- **`fetchReports()`'s N+1-shaped composition** (one list call + one report call per job with a report) is fine at demo scale but would benefit from a real `GET /api/v1/reports` list endpoint if the audit history grows large — noted as a backend enhancement, not implemented here since backend endpoints were explicitly frozen for this phase.
