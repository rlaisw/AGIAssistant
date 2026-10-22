# Tasks: Landing Page Starts on "New Chat"

**Input**: Design documents from `/specs/020-landing-new-chat/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/landing-checks.md

**Tests**: No vitest additions (research R3 — no pure logic; the change is an initial-state constant). The acceptance instrument is the CDP check matrix T1–T6 from `contracts/landing-checks.md`.

**Organization**: Single user story (US1, P1).

## Phase 1: Setup (Shared Infrastructure)

- [x] T001 Create spec artifacts per implementation plan (spec, plan, research, data-model, contracts/landing-checks.md, quickstart, checklist)

## Phase 2: Foundational (Blocking Prerequisites)

None — no shared infrastructure; one file changed, one array deleted.

## Phase 3: User Story 1 - First load opens a fresh "New chat" draft (Priority: P1) 🎯 MVP

**Goal**: every fresh load (any viewport) opens on an empty "New chat" draft with the "How can I help you today?" empty state; demo fixtures removed.

**Independent Test**: CDP T1/T2/T4 green + fixture grep zero + fallback grep present.

### Implementation for User Story 1

- [x] T002 [P] [US1] Write `/tmp/kilo/cdp/landing-check.mjs` implementing T1/T2/T4 from `contracts/landing-checks.md` *(RED captured: header showed "Q3 roadmap draft", 1 fixture bubble, 0 suggestion cards — exactly the pre-change state)*
- [x] T003 [P] [US1] In `ai-chat-landing/app/page.tsx`: replaced the initialization — `conversations` = `[{ id: "c-0", title: "New chat", messages: [] }]`, `activeId` = `"c-0"`; deleted the `initialConversations` array (five demo threads, ~90 lines); `cannedReplies`/`demoStream` untouched
- [x] T004 [US1] Fixture grep (T3): zero occurrences of the fixture titles in `ai-chat-landing/app/`; fallback grep (T5): `cannedReplies`/`demoStream` present (4 references)
- [x] T005 [US1] Ran `/tmp/kilo/cdp/landing-check.mjs` — RED → GREEN: T1/T2 header "New chat" + empty state + 0 bubbles + 4 cards (1440 & 390), drawer closed on mobile, T4 first send creates the sidebar row, cleanup deleted

## Phase 4: Polish & Cross-Cutting Concerns

- [x] T006 Ran `pnpm typecheck && pnpm lint && pnpm test` in `ai-chat-landing/` — all green (tsc, eslint, 79/79)
- [x] T007 Regression scope (T6): wide-layout structural + drawer-check + search-check (basic) — all green. Required two honest adaptations to `scripts/wide-layout.mjs` (the landing change altered its precondition): (a) the chat column no longer exists at load (empty state) → added `openFirstConversation()` before measurements, with the spec-019 toggle step at mobile width; (b) opened conversations bring a ~15px scrollbar at shorter viewports → ratio checks (T1/T2/T4/T6) and the composer-equality check now allow ± one scrollbar width
- [x] T008 Boundary check: diff limited to `ai-chat-landing/app/page.tsx`, `ai-chat-landing/scripts/wide-layout.mjs` (+ `specs/020-landing-new-chat/`)
- [x] T009 Commit spec artifacts + diff together *(committed and pushed)*

## Dependencies & Execution Order

- T001 → all; T002 ∥ T003 (different files, independent) → T004 → T005 → T006, T007 → T008 → T009

### Parallel Opportunities

- T002 (write the check script) and T003 (the page edit) are independent files — [P]
- T006 and T007 are sequential (one browser for CDP re-runs)

### Parallel Example: User Story 1

```text
Task: "Write landing-check.mjs (T1/T2/T4) and capture the RED state"
Task: "Replace the initializer and delete initialConversations in page.tsx"
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. T001 → T002 (check script + RED capture) → T003 (edit) → T004 (greps) → T005 (green run)
2. Polish: gates, regression re-runs, boundary, commit

US1 is the entire feature; delivery = the initializer swap + fixture deletion, verified by the T1–T6 matrix.
