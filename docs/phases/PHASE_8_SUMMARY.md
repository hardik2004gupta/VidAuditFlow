# Phase 8 Summary — AI Copilot for Compliance Reports

**Scope:** one new backend endpoint and one new frontend feature (a chat panel on the report page). No authentication, no persistence, no streaming, no RAG changes, no LangGraph changes, no database changes — a single stateless request/response chat grounded entirely in the report already being viewed.

---

## 1. Files Changed

**Backend — new:**
- [`backend/src/services/report_chat.py`](backend/src/services/report_chat.py) — the entire Copilot: system prompt, report-context serializer, request/response schemas, and `generate_chat_reply()`.

**Backend — modified:**
- [`backend/src/api/routers/reports.py`](backend/src/api/routers/reports.py) — added `POST /api/v1/reports/{id}/chat`.
- [`backend/src/core/exceptions.py`](backend/src/core/exceptions.py) — added `ChatError(VidAuditFlowError)`; no new exception handler needed, it's caught by the existing generic `VidAuditFlowError` → `502` handler in `api/main.py`.

**Frontend — new:**
- `frontend/features/reports/components/copilot/` — `copilot-launcher.tsx`, `copilot-panel.tsx`, `chat-message.tsx`, `chat-input.tsx`, `suggested-prompt.tsx`, `typing-indicator.tsx`, `markdown-renderer.tsx`.
- `frontend/hooks/use-report-chat.ts` — conversation state, send/retry/clear.
- `frontend/hooks/use-media-query.ts` — small reusable breakpoint hook, used to switch the panel between desktop-sidebar and mobile-bottom-sheet chrome.

**Frontend — modified:**
- `frontend/types/api.ts` — `ChatTurn`, `ChatMessageRequest`, `ChatMessageResponse`.
- `frontend/lib/api.ts` — `sendReportChatMessage()`.
- `frontend/app/(dashboard)/reports/[id]/page.tsx` — one import + one line (`<CopilotLauncher reportId={report.id} />`) added at the end of the existing JSX; nothing else in the file changed.

No other files were touched. No database migration, no changes to `graph/`, no changes to any other route.

---

## 2. Architecture

```
Frontend                                Backend
--------                                -------
CopilotLauncher (FAB)
  └─ CopilotPanel
       ├─ useReportChat(reportId)  ──►  POST /api/v1/reports/{id}/chat
       │    (conversation state,        (api/routers/reports.py)
       │     TanStack useMutation)           │
       ├─ ChatMessage (+ Markdown)            ▼
       ├─ ChatInput                    ReportRepository.get(id)  ──► 404 if missing
       └─ TypingIndicator                     │
                                               ▼
                                     services/report_chat.py
                                       ├─ build_report_context(report)
                                       ├─ REPORT_CHAT_SYSTEM_PROMPT
                                       └─ get_chat_llm(temperature=0.2).ainvoke([...])
                                               │  (graph/llm_clients.py -- the SAME
                                               │   cached AzureChatOpenAI client the
                                               │   pipeline's own nodes use)
                                               ▼
                                     { reply: str }
```

**Statelessness, by design:** the backend never stores a conversation. Every request carries `message` (the new turn) plus `conversation` (every prior turn, oldest first) from the client; `services/report_chat.py` replays that history as alternating `HumanMessage`/`AIMessage` objects ahead of the new `HumanMessage`, all under one `SystemMessage` that embeds the full report context. Refreshing the report page starts a new conversation — there is nothing server-side to reset.

**Grounding, not retrieval:** "answer using only the report" is enforced by *what's in the prompt*, not a new retrieval step. `build_report_context()` serializes the report's `final_report` narrative, every `compliance_results` entry (category/severity/timestamp/confidence/evidence/policy_reference/recommendation), every retrieved `sources` chunk, and `warnings` into one text block that becomes the system message. The Compliance/Retrieval agents already did the real RAG work when the report was generated; this phase only re-presents that already-grounded data conversationally.

**Client-driven, backend-agnostic:** `POST /api/v1/reports/{id}/chat` is the sole new surface. It reuses `ReportRepository.get()` (same 404 semantics as `GET /api/v1/reports/{id}`), the same cached `get_chat_llm()` factory the Summary Agent uses, and the same structured JSON logger (`get_logger(__name__)`) — no new infrastructure.

---

## 3. Prompt Design

`REPORT_CHAT_SYSTEM_PROMPT` (in `report_chat.py`) is deliberately a fixed, non-negotiable instruction set, separate from the per-request report context that follows it:

1. **Source-of-truth boundary** — "Your ONLY source of truth is the report data provided below." No outside knowledge about the video, the creator, or general compliance practice.
2. **Anti-fabrication, twice** — an explicit rule against inventing a violation/policy/citation, reinforced by the report context itself only ever containing what the pipeline actually produced (nothing is synthesized into the prompt).
3. **Graceful "I don't know"** — told explicitly to say the report doesn't cover something rather than guess.
4. **Conciseness** — "a short paragraph or a tight bullet list," with an explicit instruction not to restate the whole report unless asked.
5. **Light Markdown, not heavy** — bold/lists/short code spans only, so replies stay scannable inside a 360px panel instead of turning into walls of formatting.
6. **Scope disclaimer** — told to clarify it's an automated compliance check, not legal advice, if asked about liability.

The context block that follows (`build_report_context()`) is structured, labeled sections (Status/Risk/Score, Executive Summary, numbered Violations, Sources, Warnings) rather than a JSON dump — readable structure the model can cite back accurately (e.g. "violation #2") without needing tool calls to look anything up.

---

## 4. Components

| Component | Responsibility |
|---|---|
| `CopilotLauncher` | FAB trigger; picks desktop-aside vs. mobile-bottom-sheet chrome via `useMediaQuery`; owns the single `open` boolean both branches share |
| `CopilotPanel` | Header (title, clear, close), message list with auto-scroll, empty state + suggested prompts, error/retry banner, mounts `ChatInput` |
| `ChatMessage` | One turn -- user bubble (accent, plain text) or assistant bubble (card surface, `MarkdownRenderer`), hover-revealed Copy button |
| `ChatInput` | Auto-growing textarea, Enter-to-send / Shift+Enter-for-newline, send button |
| `SuggestedPrompt` | One clickable example-question pill |
| `TypingIndicator` | Three-dot "thinking" animation shown while the mutation is pending |
| `MarkdownRenderer` | Hand-rolled block/inline parser (paragraphs, bold, inline code, fenced code, bullet/numbered lists) |

**Why a hand-rolled Markdown renderer instead of `react-markdown`:** this codebase already has a precedent (`lib/markdown.ts`) of parsing the limited Markdown the Summary Agent produces by hand rather than pulling in a full CommonMark library. An LLM chat reply constrained by the system prompt to "light Markdown" doesn't need a general-purpose parser, and skipping the dependency (plus `remark`/`rehype`'s own transitive tree) keeps the report page's bundle smaller.

---

## 5. UX Details Implemented

- Empty state: centered icon, one-line explanation of what the Copilot can/can't do, four suggested prompts (Summarize report / Highest risk issues / Explain recommendations / Next steps) that send their mapped question on click.
- Typing indicator while a reply is pending (no streaming, per this phase's explicit scope — Part 5).
- Auto-scroll to the newest message/typing indicator via a bottom sentinel + `scrollIntoView`.
- Retry: on failure, the failed user message stays visible in the transcript (not silently dropped) with an inline error explanation and a Retry button that resends without duplicating the turn.
- Clear conversation: resets local state and any lingering error, back to the empty state.
- Copy: every message (user or assistant) has a hover-revealed Copy-to-clipboard action.
- Keyboard: Enter sends, Shift+Enter inserts a newline.
- Desktop: non-modal ~360px right sidebar (`fixed`, below the topbar) — the report stays fully interactive behind it, closed only via its own X or Escape.
- Mobile (<1024px): the existing `Sheet` primitive as a modal bottom sheet (`80vh`), matching `UI_VISION.md`'s own documented "chat becomes a bottom sheet" convention for this exact scenario.

---

## 6. Verification

- `uv run python -c "from backend.src.api.main import app; ..."` — clean import, confirmed `POST /api/v1/reports/{report_id}/chat` is registered.
- `npx tsc --noEmit` and `npm run build` — both clean, zero errors. `/reports/[id]` route: 147 kB → 154 kB (First Load JS 378 kB → 385 kB) for the entire chat feature.
- **Live verification against the real backend** (not mocked):
  - `POST /api/v1/reports/{unknown-id}/chat` → `404`, matching `GET`'s existing behavior.
  - `POST /api/v1/reports/{real-id}/chat` with no Azure credentials configured in this environment → `502 {"error":{"code":"upstream_error","message":"The AI Copilot couldn't generate a reply. Please try again."}}`, proving `ChatError` → the existing generic handler works exactly as intended with zero new exception-handling code.
  - In the browser: opened the panel, clicked a suggested prompt, watched the real request fail with that exact 502 message rendered in the panel's error banner, clicked Retry (confirmed no duplicate user bubble), clicked Clear (confirmed reset to empty state) — all against the live server.
  - Since no real Azure OpenAI credentials exist in this environment to produce a genuine successful reply, one `fetch` call was temporarily intercepted client-side (in the browser console, not in any source file) to return a realistic Markdown reply, confirming bold/bullet-list/inline-code all render correctly inside a real `ChatMessage` in the live DOM.
  - Confirmed in both dark and light mode, and at 375×812 (mobile bottom sheet renders correctly, backdrop dims the report page behind it).
  - Confirmed the report page's existing sections (Executive Summary, Violations, Evidence Timeline, Report Details, Sources) are pixel-for-pixel unchanged from Phase 7 — the only diff on that page is the one new `<CopilotLauncher>` line.

---

## 7. Limitations

- **No real successful reply has been demonstrated end-to-end** — this environment has no live Azure OpenAI credentials (same root cause noted in Phase 6/7's summaries), so the `502` failure path is what's been proven live; the success path was verified with a client-side-only mocked response instead. The code path (`llm.ainvoke` → `response.content`) is identical to the pipeline's own Summary Agent call, which is the strongest available evidence it will behave the same with real credentials.
- **Conversation resets on page refresh or a desktop↔mobile resize mid-session** — both are expected consequences of "no persistence, no memory" being explicit requirements this phase, not oversights. A resize mid-conversation specifically remounts the panel (desktop uses a different component branch than mobile), losing in-progress state; refreshing the browser tab does the same. Neither is likely in real usage (users don't resize mid-chat), but it's worth knowing.
- **No token/length guard on the report context.** For a report with an unusually large number of violations, `build_report_context()` could produce a very large system prompt. `_MAX_CONVERSATION_TURNS = 20` caps how much *conversation history* gets replayed, but there's no equivalent cap on violation count today.
- **No rate limiting** on the new endpoint (API_PLAN.md's rate-limiting section calls out chat as one of the two routes that should eventually be limited, alongside audit creation, but this phase's brief explicitly scoped out backend refactoring beyond the one endpoint).

---

## 8. Future Improvements

- Real SSE/streaming (explicitly out of scope this phase) once the UX case for token-by-token output outweighs the added complexity of a stateful stream endpoint.
- Optional conversation persistence (a `chat_messages` table) if cross-session history becomes a real user need — `API_PLAN.md` already earmarks this as a reasonable "Future," not a day-one requirement.
- A token/character cap or truncation strategy for `build_report_context()` on reports with very large violation counts.
- Surfacing which specific violation(s) a reply drew from (e.g. inline citation markers back to the Violation Cards/Evidence Timeline) rather than prose-only references.
