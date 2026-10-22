# Tasks: Sidebar Full-Text Search (Case-Insensitive)

**Input**: Design documents from `/specs/018-sidebar-search/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/search-filter.md

**Tests**: Vitest is REQUIRED for the pure matcher (user-requested; Constitution II — `lib/history/search.test.ts` T1–T8 written FIRST, must fail until the matcher lands). CDP acceptance C1–C6 for the rendered flow.

**Organization**: US1 (P1, title search) then US2 (P2, loaded-content search); the matcher + query state are shared and land in Foundational.

## Phase 1: Setup (Shared Infrastructure)

- [x] T001 Create spec artifacts per implementation plan (spec, plan, research, data-model, contracts/search-filter.md, quickstart, checklist)

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The pure matcher and its failing test suite — both user stories depend on them.

- [x] T002 [P] Write the vitest suite `ai-chat-landing/lib/history/search.test.ts` with T1–T8 verbatim from `contracts/search-filter.md` *(written first; failed on missing module — TDD red confirmed)*
- [x] T003 Implement the pure matcher in `ai-chat-landing/lib/history/search.ts` *(TDD green: 8/8 pass — trim+lowercase literal substring, no regex)*

## Phase 3: User Story 1 - Find a conversation by its title (Priority: P1) 🎯 MVP

**Goal**: Typing in the sidebar search filters conversation rows case-insensitively by title; empty buckets collapse; explicit empty state; ×/Escape restore the full list.

**Independent Test**: CDP C1/C2/C4/C5 + vitest T1–T3/T8 green.

### Implementation for User Story 1

- [x] T004 [US1] In `ai-chat-landing/app/page.tsx`: add `query` state (controlled by the existing sidebar search `Input` at ~line 603) plus a 200 ms debounced mirror, and pass `filterHistory(historyRecords, getContentStub, debouncedQuery)` to `ChatHistory` (stub returns `undefined` until T008)
- [x] T005 [US1] In `ai-chat-landing/app/page.tsx`: add the × clear control (`aria-label="Clear search"`, rendered only when query is non-empty) and Escape-key clearing on the search input
- [x] T006 [US1] In `ai-chat-landing/app/page.tsx`: render "No conversations match ‹query›" ONLY when `history.status === "ready"` && debounced query is non-empty && filtered rows are empty — loading skeleton and error states keep precedence (research R5)
- [x] T007 [US1] Verify US1: `pnpm test` (T1–T3/T8 green) + CDP C1 (typing filters live: 20→2 rows), C2 ("BAR"/"bar" identical), C4 (nonsense query → empty state, not skeleton/error), C5 (× and Escape restore full list) — all green

## Phase 4: User Story 2 - Find a loaded conversation by its message content (Priority: P2)

**Goal**: The same query also matches loaded message text of open/previously-opened conversations; unopened rows match on title only.

**Independent Test**: CDP C3 + vitest T4/T5 green.

### Implementation for User Story 2

- [x] T008 [US2] In `ai-chat-landing/app/page.tsx`: memoize the content map `difyId → concatenated message texts` from `conversations` where `difyId` is set, and pass it as `getContent` into `filterHistory` (replaces the T004 stub)
- [x] T009 [US2] Verify US2: `pnpm test` (T4/T5 green) + CDP C3 (deterministic: 60+ char marker message places the probe past the 60-char title cutoff — probe found the row via content match, 1 row) and C6 (delete while searching 1→0, empty state after last match deleted, Load more green; two intermediate script bugs fixed: textContent fusing → innerText+clone-strip, and marker-gone probe fooled by the empty state echoing the query — the feature itself was correct both times)

## Phase 5: Polish & Cross-Cutting Concerns

- [x] T010 Run `pnpm typecheck && pnpm lint && pnpm test` in `ai-chat-landing/` — all green *(tsc clean, eslint clean, **79/79** vitest)*
- [x] T011 Boundary check: diff limited to `ai-chat-landing/app/page.tsx` + new `lib/history/search.ts` + `search.test.ts` — no backend/API edits, no new dependencies (SC-005)
- [x] T012 Commit spec artifacts + diff together *(committed and pushed)*

## Phase 6: Convergence

- [x] T013 Verify US1/AC4 (open a filtered row) *(verified 2026-10-22: search → click filtered row → header shows the full title, messages load — CDP green)* (US1/AC4, contracts/search-filter.md C6)

## Dependencies & Execution Order

- T001 → all; T002 → T003 (TDD: failing suite first) → T004
- T004 → T005 → T006 (same file — sequential), then T007
- T008 after T004 (extends the same page.tsx wiring) → T009
- T009 → T010 → T011 → T012

### Parallel Opportunities

- T002 is independent (new test file) — [P]
- T003 (search.ts) can proceed while T002's cases are being finalized, but the suite must gate it
- T007 and T009's CDP runs are sequential (one browser, one throwaway lifecycle)

### Parallel Example: Foundational

```text
Task: "Write the vitest suite lib/history/search.test.ts with T1–T8 (fails until matcher lands)"
Task: "Implement the pure matcher in lib/history/search.ts"
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. T001 → T002 (failing tests) → T003 (matcher passes) → T004–T006 (page wiring) → T007 verify
2. **STOP and VALIDATE**: title search works end-to-end (MVP)

### Incremental Delivery

1. MVP: title search (US1) ships value alone
2. Add US2 (content map) → verify → ship the full feature
3. Polish: gates, boundary, commit
