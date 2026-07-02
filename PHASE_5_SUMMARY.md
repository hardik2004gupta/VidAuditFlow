# Phase 5 Summary — Frontend Foundation

**Scope:** build the complete VidAuditFlow frontend as a standalone Next.js 15 application, fully mocked, with no authentication, no backend integration, and no real network calls. This phase is architecture and UI only; every data source is a typed, artificially-delayed mock that mirrors the shape of the real backend responses so a later integration phase only has to swap `lib/mock/` for a real `lib/api-client.ts`.

---

## 1. Tech Stack

| Concern | Choice |
|---|---|
| Framework | Next.js 15.5 (App Router, Turbopack, React 19) |
| Language | TypeScript (strict) |
| Styling | Tailwind CSS v4 (CSS-first config, no `tailwind.config.ts`) |
| Components | shadcn/ui, "base-nova" style — built on **Base UI** (`@base-ui/react`), not Radix |
| Animation | Framer Motion |
| Server state | TanStack Query v5 |
| Forms | react-hook-form + Zod (`@hookform/resolvers`) |
| Icons | Lucide React |
| Theming | next-themes (`class` strategy, dark-first) |
| Charts | Recharts (compliance-score radial gauge) |
| Dates | date-fns |

A non-obvious but important fact for future work: **this shadcn/ui installation is Base UI, not Radix.** Polymorphism uses a `render` prop (`<Button render={<Link href="..." />}>`), not `asChild`, and Base UI's `Button` primitive defaults `nativeButton={true}` — rendering it as a `<Link>`/`<a>` without overriding that produces a console warning and drops button a11y semantics (`role`/`tabindex`). This was fixed once, centrally, in [`components/ui/button.tsx`](frontend/components/ui/button.tsx): the wrapper now defaults `nativeButton` to `false` whenever a `render` prop is present, so every call site across the app gets correct semantics for free instead of needing `nativeButton={false}` repeated at ~10 call sites.

---

## 2. Folder Structure

```
frontend/
├── app/
│   ├── (marketing)/            route group: public landing page, own header/footer
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── (dashboard)/            route group: authenticated-feel app shell
│   │   ├── layout.tsx          wraps children in DashboardShell (sidebar + topbar)
│   │   ├── loading.tsx         skeleton boundary
│   │   ├── error.tsx           error boundary
│   │   ├── dashboard/page.tsx
│   │   ├── audits/new/page.tsx
│   │   ├── reports/page.tsx
│   │   ├── reports/[id]/page.tsx
│   │   └── settings/page.tsx
│   ├── layout.tsx               root layout: fonts, AppProviders, metadata
│   ├── globals.css              design tokens, Tailwind v4 theme
│   └── not-found.tsx
├── components/
│   ├── ui/                      shadcn primitives (Base UI-backed)
│   ├── layout/                  sidebar, topbar, page-header, nav, logo, theme-toggle, user-menu
│   └── shared/                  cross-feature: StatusChip, MetricCard, EmptyState, LoadingCard, SectionHeader
├── features/
│   ├── audits/components/       SeverityBadge, RiskBadge, FinalStatusBadge, AuditStatusChip,
│   │                            ComplianceScoreCard, ViolationTable, EvidenceCard, StageTimeline,
│   │                            StageTracker, NewAuditForm
│   ├── dashboard/components/    DashboardMetrics, RecentAuditsCard, RecentReportsCard,
│   │                            SystemStatusCard, QuickActionsCard
│   ├── reports/components/      ReportsTable, ExecutiveSummaryCard, SourcesPanel, WarningsBanner
│   ├── landing/components/      SiteHeader, HeroSection, FeaturesSection, ArchitectureSection,
│   │                            TechStackSection, CtaSection, SiteFooter
│   └── settings/components/     AppearanceSettingsCard
├── hooks/
│   └── use-simulated-audit-progress.ts
├── lib/
│   ├── mock/                    api.ts, audits.ts, reports.ts, index.ts
│   ├── constants.ts             status/severity → label + className maps, NAV_ITEMS
│   ├── format.ts                relative/absolute time, durations, short ids
│   ├── markdown.ts              minimal `## Heading` section extractor for final_report
│   └── utils.ts                 `cn()`
├── providers/                   ThemeProvider, QueryProvider, AppProviders (composition root)
└── types/
    └── api.ts                   TypeScript types mirroring the backend's Pydantic schemas exactly
```

Organization is strictly feature-first: `features/<domain>/components/` for anything specific to audits, reports, dashboard, landing, or settings; `components/shared/` only for components with no domain knowledge; `components/ui/` only for the shadcn primitives themselves. Nothing lives in one giant `components/` dump.

---

## 3. Component Hierarchy (high-level)

```
RootLayout (app/layout.tsx)
└── AppProviders (Theme → Query → Tooltip → Toaster)
    ├── (marketing)/layout.tsx
    │   └── SiteHeader / <page content> / SiteFooter
    │       └── page.tsx → HeroSection, FeaturesSection, ArchitectureSection,
    │                       TechStackSection, CtaSection
    └── (dashboard)/layout.tsx
        └── DashboardShell (Sidebar + Topbar)
            ├── dashboard/page.tsx
            │   └── PageHeader, DashboardMetrics, RecentAuditsCard, RecentReportsCard,
            │       SystemStatusCard, QuickActionsCard
            ├── audits/new/page.tsx
            │   └── NewAuditForm (react-hook-form + zod)
            │       └── StageTracker (useSimulatedAuditProgress) → CheckCircle2/LoaderCircle/CircleDashed
            ├── reports/page.tsx
            │   └── ReportsTable (TanStack Query → fetchReports)
            └── reports/[id]/page.tsx  (async server component → fetchReport)
                ├── WarningsBanner
                ├── ExecutiveSummaryCard (parses final_report markdown)
                ├── ViolationTable → Dialog → EvidenceCard
                ├── StageTimeline (processing_metadata)
                ├── SourcesPanel
                ├── ComplianceScoreCard (Recharts RadialBarChart + Framer Motion count-up)
                └── Video Details card
```

---

## 4. Design Decisions

- **Dark-first, hairline borders over shadows.** `app/globals.css` maps UI_VISION.md's exact hex tokens onto shadcn's structural token names (`background`, `card`, `popover`, `primary`, `border`, etc.) and layers four *additional* domain tokens (`success` / `warning` / `critical` / `info`, each with a `-foreground` pair) reserved exclusively for compliance severity/status — never reused for generic UI decoration. The default `card.tsx` (`rounded-xl` + `ring-1 ring-foreground/10`) was edited to `rounded-lg` + `border border-border` to match the spec's "borders over shadows" rule.
- **One brand accent, used sparingly.** `primary` (`#6366F1` indigo) is reserved for CTAs, active nav state, and links. shadcn's own `accent` token is kept as a *separate*, subtler hover/highlight tint (`#efeff8` light / `#1c1c2b` dark) — the two are semantically distinct and never collapsed into one.
- **Radial gauge as a signature moment.** `ComplianceScoreCard` combines Recharts' own arc-sweep animation with a Framer Motion-driven count-up of the number overlay (0 → final score, ~1.1s, `easeOut`), gated behind `useReducedMotion()` so it renders instantly for users who've opted out of motion.
- **Live Audit Tracker as the other signature moment.** `StageTracker` renders the seven real pipeline stages (from `types/api.ts`'s `PIPELINE_STAGES`, copied verbatim from the backend's `_STAGE_LABELS`) as a vertical stepper with three icon states (pending/active/done), each transition Framer-Motion-crossfaded, plus a per-step elapsed-time readout once done.
- **No fabricated auth UI.** `UserMenu` shows a static "Demo Workspace / No account connected" label and a single link to Settings — deliberately no "Sign out" action, since implying a real session would misrepresent what this phase built.
- **Evidence surfaced without a page navigation.** Clicking a `ViolationTable` row opens a `Dialog` containing `EvidenceCard` in place, rather than routing to a separate page — keeps the reviewer in context while checking every finding.

---

## 5. Mock Architecture

Every "API" function in [`lib/mock/api.ts`](frontend/lib/mock/api.ts) — `fetchAuditJobs`, `fetchAuditJob`, `fetchReport`, `fetchReports` — has the same async signature and shape a real `fetch`-based client will have, including an artificial `delay()` so loading states are actually exercised. `types/api.ts` mirrors the backend's Pydantic schemas field-for-field (`AuditJobRead`, `ReportRead`, `ComplianceIssue`, `RetrievedRule`, `StageTrace`), so when real backend integration lands, only the data source in `lib/mock/` needs replacing with `lib/api-client.ts` — no component, hook, or React Query key should need to change.

Fixtures cover every real backend state: `lib/mock/audits.ts` has one `AuditJob` per `AuditJobStatus` (`queued`, `running`, `completed`, `completed_degraded`, `failed`, `cancelled`), and `lib/mock/reports.ts` has three `Report`s — a clear FAIL (two CRITICAL + two WARNING violations), a clear PASS (zero violations), and a degraded PASS (OCR stage failed, one warning surfaced via `WarningsBanner`).

The one exception to "static mock, real fetch shape" is the **Live Audit Tracker**: since it's UI_VISION.md's signature "wow moment," it needs to visibly progress, not just describe a finished state. `hooks/use-simulated-audit-progress.ts` drives it with a client-side `setTimeout` per stage — standing in for polling `GET /api/v1/audits/{id}` until real integration lands — and `NewAuditForm` resolves the simulated run to an existing mock report at the end.

---

## 6. Accessibility Decisions

- Every icon-only control (`ThemeToggle`, table row "view evidence" button, mobile sidebar trigger) has an explicit `aria-label`.
- Form errors use `role="alert"` and are wired to the input via `aria-describedby` + `aria-invalid` (`NewAuditForm`).
- `SidebarMobile`'s `SheetTitle` is present but `sr-only` — screen readers get a label without a redundant visible heading.
- All interactive elements rely on the existing shadcn/Base UI focus-visible ring (`focus-visible:ring-3 focus-visible:ring-ring/50`); no custom component suppresses it.
- `prefers-reduced-motion` is respected globally (`globals.css` forces near-zero animation/transition durations) and individually in the two Framer Motion-heavy components (`ComplianceScoreCard`, `StageTracker` icon crossfades check `useReducedMotion()`/rely on the same global rule).
- Color is never the only signal: every severity/status indicator pairs color with a text label (`SeverityBadge`, `RiskBadge`, `FinalStatusBadge`, `StatusChip`), never a bare colored dot.

---

## 7. Performance Considerations

- Turbopack for both `dev` and `build`.
- Client components are scoped narrowly: report pages and the reports list fetch via an async server component / TanStack Query respectively, but static marketing sections (`FeaturesSection`, `TechStackSection`, `ArchitectureSection`) are plain server components with zero client JS.
- `next/link` + Next's built-in route prefetching for all in-app navigation; no manual route-level code-splitting was needed beyond what App Router already does per route segment.
- Recharts and Framer Motion are only pulled into the routes that use them (report viewer, new-audit flow), not the global bundle.

---

## 8. Verification

- `npm run build` (Turbopack) — compiles cleanly, generates all 9 routes, zero TypeScript errors, zero ESLint errors:

  ```
  Route (app)                         Size  First Load JS
  ┌ ○ /                            61.9 kB         255 kB
  ├ ○ /_not-found                      0 B         193 kB
  ├ ○ /audits/new                   151 kB         382 kB
  ├ ○ /dashboard                   14.3 kB         245 kB
  ├ ○ /reports                     13.6 kB         245 kB
  ├ ƒ /reports/[id]                 143 kB         374 kB
  └ ○ /settings                    1.18 kB         232 kB
  ```
- `npx tsc --noEmit` — no errors.
- Manual verification in-browser (desktop 1280×900, mobile 375×812, light + dark) covering: landing page, dashboard (metrics, recent audits/reports, system status, quick actions), New Audit form validation + submission + live StageTracker animation + completion state, Reports list, Report Viewer (score gauge count-up, violations table → evidence dialog, processing timeline, sources, warnings banner), Settings appearance switcher.
- One real bug found and fixed during verification: Base UI's `Button` needed `nativeButton={false}` whenever polymorphed via `render` into a `Link` — fixed centrally in `components/ui/button.tsx` (see Section 1) rather than at each call site.

---

## 9. What Was Deliberately Not Built

Per this phase's explicit scope: no authentication, no Supabase, no real backend calls, no AI chat, no PDF export, no analytics, no notifications, no streaming/WebSockets, no client-side caching beyond TanStack Query's defaults, no optimistic updates. The Settings page has one real control (appearance/theme) and an `EmptyState` noting that account/workspace/notification settings arrive once authentication exists.
