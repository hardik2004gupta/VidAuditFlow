# UI_VISION.md
## VidAuditFlow — Design System & Product UI Vision

Reference points: **Vercel** (typographic restraint, dark-first, generous whitespace), **Linear** (motion precision, keyboard-first affordances, subtle depth), **OpenAI** (calm, confident, content-forward layouts), **Perplexity** (source-citation UI patterns, streaming-answer feel), **Stripe Dashboard** (data-density done cleanly, excellent tables/charts).

The through-line across all five: **restraint**. Lots of whitespace, a tiny color palette used deliberately, motion that clarifies state changes rather than decorating them, and typography doing most of the hierarchy work instead of borders/shadows.

---

## Typography

- **Font:** A single variable sans-serif family for UI text — **Inter** or **Geist Sans** (Vercel's own font, free, pairs naturally with a Vercel-deployed Next.js app). One font family, no mixing.
- **Monospace accent:** **Geist Mono** or **JetBrains Mono** for video IDs, timestamps, session IDs, and code-like values (e.g., `vid_4f2c9a1b`) — mirrors Linear/Vercel's convention of using mono type as a "this is a system value" signal.
- **Scale** (Tailwind-friendly, mobile-first):

| Role | Size / Weight | Usage |
|---|---|---|
| Display | 40–56px / 700 | Landing page hero only |
| H1 | 28–32px / 600 | Page titles (Dashboard, Report) |
| H2 | 20–22px / 600 | Section headers (Violations, Summary) |
| H3 | 16–17px / 600 | Card titles |
| Body | 14–15px / 400 | Default text |
| Small | 12–13px / 400–500 | Metadata, timestamps, badges |
| Mono | 12–13px / 500 | IDs, technical values |

- **Line height:** generous — 1.5–1.6 for body copy, 1.1–1.2 for display/headers. Cramped line-height is the single fastest way to look like a tutorial project; avoid it everywhere.
- **Color of type:** never pure black/white. Use near-black (`#0A0A0A`) on light surfaces and off-white (`#EDEDED`/`#FAFAFA`) on dark surfaces, matching Vercel/Linear's practice of avoiding harsh full-contrast text.

---

## Spacing

- Base unit: **4px**, scaling in the standard Tailwind steps (4, 8, 12, 16, 24, 32, 48, 64).
- Card internal padding: 20–24px minimum — never let content touch a card edge.
- Section vertical rhythm: 48–64px between major dashboard sections; 24–32px between related sub-sections.
- Line-item density (tables, lists): 12–16px vertical padding per row — dense enough to feel like a real data product (Stripe-style), never so tight it feels cramped.
- **One consistent max content width** for dashboard pages (e.g., `max-w-6xl`, centered) — avoids the amateur look of content stretching edge-to-edge on wide monitors.

---

## Color Palette

Dark-first (default), with a light theme as a secondary supported mode (see Dark Theme section).

| Token | Dark value | Role |
|---|---|---|
| `background` | `#0A0A0A` | App background |
| `surface` | `#141414` | Cards, panels |
| `surface-elevated` | `#1C1C1C` | Modals, popovers, dropdowns |
| `border` | `#262626` | Hairline borders (1px, never heavier) |
| `foreground` | `#EDEDED` | Primary text |
| `muted-foreground` | `#8C8C8C` | Secondary text, metadata |
| `accent` (brand) | `#6366F1` (indigo) or `#3B82F6` (blue) — pick one, use sparingly | Primary CTAs, active nav state, links |
| `success` | `#22C55E` | PASS status, healthy state |
| `warning` | `#F59E0B` | WARNING severity |
| `critical` | `#EF4444` | CRITICAL severity, FAIL status |
| `info` | `#38BDF8` | Neutral informational badges |

**Rule:** the accent color appears in at most 2–3 places per screen (primary button, active nav item, links). Severity colors (`success`/`warning`/`critical`) are reserved *exclusively* for compliance status — never reused for generic UI decoration, so their meaning stays unambiguous (a Stripe Dashboard convention: color always means something specific).

---

## Component Style

Built on **shadcn/ui** primitives, customized via Tailwind tokens above — not restyled into something unrecognizable. Key conventions:

- **Border radius:** consistent `rounded-lg` (8px) for cards/inputs/buttons, `rounded-full` only for avatars/badges/pills. No mixed radii on the same screen.
- **Borders over shadows:** 1px hairline borders (`border-border`) are the primary way to separate surfaces on dark backgrounds; shadows are used sparingly and only for genuinely elevated layers (modals, dropdowns), matching Linear's flat-with-hairlines aesthetic rather than Material-style heavy shadows.
- **Buttons:** three variants only — `primary` (accent-filled, for the one main action per screen), `secondary` (bordered, neutral), `ghost` (text-only, for tertiary actions). Never more than one `primary` button visible at once.
- **Icons:** one icon set only (**lucide-react**, shadcn/ui's default) — 16–20px, stroke width 1.5–2, matched to text color, never mixed with a second icon library.

### Cards
- Used for: audit history items, violation entries, report summary tiles, chat message groups.
- Structure: subtle border, `surface` background, 20–24px padding, optional top-right meta (timestamp/status badge), title + supporting text, optional footer action row.
- Hover state (for clickable cards, e.g. audit history row): border brightens slightly (`border-border` → a lighter neutral) plus a 150ms background tint — no heavy lift/shadow-pop, matching Linear's understated hover language.

### Tables
- Stripe-Dashboard-style: no vertical grid lines, horizontal hairline row separators only, generous row height (48–56px), right-aligned numeric columns, left-aligned text columns, a sticky header row on scroll for longer lists (e.g., a long violations table).
- Row hover: subtle background tint, entire row clickable where it represents a drill-in (e.g., audit history → report).
- Status/severity always rendered as a colored `Badge`, never as plain colored text.

### Timeline
- Used on the report page to plot *where in the video* violations occur, mapped against video duration (mm:ss ruler).
- Visual language: a horizontal track (video duration), with severity-colored markers/pins placed proportionally; clicking a marker scrolls to/highlights the corresponding violation card. Inspired by video-editing timeline UIs and Linear's issue-timeline visualizations — thin track, small precise markers, no heavy chrome.

### Navigation
- **Sidebar** (desktop, ≥1024px): fixed left, ~240px wide, dark `surface` background, product logo/name at top, primary nav items (Dashboard, New Audit, Settings) with active-state left-border accent + subtle background tint (Linear's exact active-nav-item pattern).
- **Topbar**: within the main content area, holds page title, breadcrumb (if nested, e.g. Dashboard / Audit #123), and user menu (avatar → dropdown: profile, sign out).
- **Mobile** (<768px): sidebar collapses to a slide-over drawer triggered by a hamburger icon in a slim topbar; bottom nav is deliberately avoided (too app-like for a dashboard product).
- **Command palette (Should Have feature):** `Cmd/Ctrl+K` opens a Linear-style fuzzy command menu (jump to audit, start new audit, toggle theme).

### Loading States
- **No blank spinners for anything longer than ~1 second.** Every loading surface uses a **skeleton** matching the shape of the eventual content (shadcn/ui `Skeleton` primitive) — card skeletons for audit history, row skeletons for tables, chart-shaped skeleton blocks for Recharts panels.
- **The live audit tracker is the one place a genuine progress indicator belongs** (see below) — this is a multi-minute operation and deserves an explicit, honest stage-by-stage progress UI, not a generic spinner pretending it'll be fast.
- Button loading state: spinner replaces the button's icon slot, label stays ("Starting audit…"), button is disabled — never swap the whole button for a spinner (avoids layout jump).

### Live Audit Tracker (signature screen)
- Vertical stepper (Perplexity/Linear-style "steps completed" pattern) listing the pipeline stages in order: **Downloading video → Extracting transcript → Reading on-screen text (OCR) → Retrieving relevant policies → Running compliance analysis → Generating summary**.
- Each step has three states: pending (muted, outline icon), active (accent color, animated pulse/spinner), done (success-green check). Completed steps show elapsed time (e.g., "Downloaded in 12s") — small but meaningful "we're being transparent about what's happening" detail.
- Framer Motion: each step transitions pending→active→done with a smooth icon crossfade/scale (150–250ms), and the stepper's active-step highlight animates its position rather than snapping — this single animation sequence is one of the highest-leverage "feels crafted" moments in the whole app.

### Charts (Recharts)
- **Compliance score gauge/donut:** single-number summary (e.g., "2 Critical, 1 Warning" or a 0–100 "compliance score") using a radial chart with severity colors, centered large number, small label beneath — Stripe-Dashboard-style KPI tile.
- **Violations-by-severity bar chart:** horizontal bars, one per category, colored by severity, on a report with several violations.
- **Styling discipline:** grid lines at 10–15% opacity or omitted entirely, axis labels in `muted-foreground`, tooltips styled to match the `surface-elevated` card style (dark background, hairline border, small type) rather than Recharts' default white tooltip — this default-white-tooltip-on-dark-app mistake is one of the fastest ways a Recharts integration looks unpolished; must be explicitly themed.

### Glassmorphism — used sparingly, deliberately
- **Where it's appropriate:** the topbar/header when content scrolls beneath it (`backdrop-blur-md` + semi-transparent surface color), and modal/dialog overlays (`backdrop-blur-sm` on the scrim behind a dialog).
- **Where it's *not* appropriate:** cards, buttons, sidebars, tables — these stay solid/opaque. Overusing blur/transparency across the whole UI is the fastest way to look dated (2021-era "glassmorphism trend" rather than 2026 Vercel/Linear restraint). One or two blurred surfaces per screen, maximum.

---

## Animation Principles (Framer Motion)

- **Duration:** 150–250ms for micro-interactions (hover, button press, badge appearance), 300–400ms for layout-level transitions (page transitions, panel open/close). Nothing should feel slower than ~400ms — Linear's whole feel comes from *fast, precise* motion, not lingering, decorative motion.
- **Easing:** `ease-out` for things entering/appearing, `ease-in-out` for things moving between two states. Avoid bouncy/spring physics except for one signature moment (e.g., a checkmark "pop" when a violation-free report completes) — used exactly once so it stays special.
- **What gets animated:** page/panel entrances (fade + slight y-offset, 8–12px), the live-tracker stage transitions, chat message appearance (fade+slide in, streaming-token feel), toast notifications, and modal/dialog open/close. What does **not** get animated: table row hovers (instant/CSS-only), text content changes, anything on every single scroll tick (respect `prefers-reduced-motion` throughout).

---

## Dark Theme (default) + Light Theme (secondary)

- Dark is the primary, default, and most-polished theme — matches every reference product (Vercel, Linear, OpenAI, Perplexity, Stripe Dashboard's app view all default dark or offer a dark mode as first-class).
- Light theme is a straightforward token swap (invert background/surface/foreground roles, keep accent and severity colors identical for consistent meaning across themes) — implemented via Tailwind's `dark:` variant and a theme toggle in the user menu, but dark is what gets showcased in a portfolio README/demo GIF.
- Theme preference persisted (localStorage, respecting system preference on first load).

---

## Responsive Behavior

- **Breakpoints:** rely on Tailwind defaults (`sm`640 / `md`768 / `lg`1024 / `xl`1280).
- **Landing page:** fully responsive hero, stacks the paste-URL input and supporting copy vertically below `md`.
- **Dashboard shell:** sidebar → drawer below `lg`; topbar always present.
- **Report page:** the two-column layout (report content + chat panel) on desktop collapses to a single column below `lg`, with chat becoming a bottom sheet / separate tab (`Report` / `Chat` toggle) rather than a squeezed sidebar — never shrink the chat panel to the point of being unusable.
- **Tables:** below `md`, wide tables (e.g., violations table) either switch to a stacked-card layout per row or gain horizontal scroll with a visible scroll-shadow cue — never silently clip columns.
- **Touch targets:** minimum 40px tap height for any interactive element on mobile, even though this is primarily a desktop-dashboard product.

---

## Signature "Wow" Moments (deliberately designed, not incidental)

These are the specific moments a portfolio reviewer is most likely to remember — worth calling out explicitly so implementation time is protected for them:

1. **The live stage tracker** animating through six real pipeline stages in real time — the clearest visual proof of "this is a working multi-agent system," not a mockup.
2. **The report reveal** — when the final stage completes, the report content animates in (staggered card entrance, ~50ms delay between items) rather than just appearing.
3. **Chat streaming** — AI chat responses stream token-by-token (or simulate it) with a subtle blinking cursor, matching the Perplexity/ChatGPT-familiar feel users already associate with "real AI."
4. **The compliance score gauge** animating from 0 to its final value on report load, rather than rendering static.
