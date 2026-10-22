# Implementation Plan: Sidebar Full-Text Search (Case-Insensitive)

**Branch**: `018-sidebar-search` | **Date**: 2026-10-22 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/018-sidebar-search/spec.md`

## Summary

Wire the inert sidebar search input to a case-insensitive client-side
filter: titles of every backend history row, plus the loaded message text
of rows whose conversation is open (or was opened this session). The
matcher lives in a pure module (`lib/history/search.ts`, vitest-covered);
filtering happens in `page.tsx` via a memo before `ChatHistory`, which
stays untouched.

## Technical Context

- **Language/Version**: TypeScript (Next.js 16.4, React 19.3)
- **Primary Dependencies**: none added — pure client-side filter
- **Storage**: N/A (session-local query state)
- **Testing**: `pnpm typecheck && pnpm lint && pnpm test` — new vitest
  suite for `lib/history/search.ts` (8 cases, see contracts); CDP
  acceptance for the rendered flow (Chrome :9240, `pnpm dev` :3000)
- **Target Platform**: web, sidebar-visible viewports (≥768px, where the
  sidebar exists)
- **Project Type**: web frontend (Next.js App Router)
- **Performance Goals**: filter of a 100-row list settles <1s after input
  (SC-001); debounce ≈200 ms
- **Constraints**: no backend/API changes; no new dependencies; spec
  014/015 sidebar behaviors preserved (FR-010)
- **Scale/Scope**: 1 new pure module + 1 page.tsx integration + tests

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Contract Preservation**: PASS — no API/tool/response changes.
- **II. Tests-First**: PASS — the non-trivial logic (the matcher) lands
  with its vitest suite written alongside; CDP acceptance for the
  rendered flow (SC-002/SC-003).
- **III. Minimal Dependencies**: PASS — zero new dependencies (stdlib
  string ops only).
- **IV. Honest Answers**: PASS — FR-009's no-unclaimed-coverage boundary
  is a stated requirement, and T-case 5 pins the title-only fallback as
  an explicit expected behavior.
- **V. Spec-Driven Replacement**: PASS — replaces the dead input stub with
  a working control; `ChatHistory` untouched.

No violations; Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/018-sidebar-search/
├── plan.md              # This file
├── research.md          # Phase 0 decisions
├── data-model.md        # Filter signature + states
├── contracts/
│   └── search-filter.md # Match rules, states, test matrix, error handling
├── quickstart.md        # Validation guide
├── checklists/
│   └── requirements.md  # (from /speckit.specify)
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
ai-chat-landing/
├── lib/history/
│   ├── search.ts            # NEW — pure matcher: filterHistory(records, getContent, query)
│   └── search.test.ts       # NEW — 8 vitest cases (contract T1–T8)
├── app/
│   └── page.tsx             # query state + debounce + memoized filter
│                            # before ChatHistory; × clear + Escape; empty state
└── components/
    └── chat-history.tsx     # UNTOUCHED (FR-010 regression guard)
```

**Structure Decision**: the matcher is pure logic in `lib/history/` (house
convention: vitest for pure logic); `page.tsx` owns state and passes
filtered records down.

## Design

- **Match semantics**: case-insensitive substring (`toLowerCase().includes()`)
  on titles for every row; content match only for rows whose `difyId` has
  loaded messages in `conversations` (open / previously-opened; active
  once upserted). Literal substring — no regex, no injection surface.
- **Corpus**: titles of all `historyRecords` + message text for rows with
  loaded messages (see `data-model.md`; the corpus boundary is the
  double-clarified one — demo drafts are never in the sidebar).
- **States** (error handling, user-requested):
  - `loading`/`error` → existing skeleton/error UI takes precedence; the
    search-empty state MUST NOT render
  - `ready` + empty/whitespace query → full grouped list
  - `ready` + query + matches → filtered grouped list (empty buckets
    collapse, via existing `groupConversations`)
  - `ready` + query + zero matches → "No conversations match ‹query›"
  - × control and Escape reset the query (× visible only when non-empty)

## Verification

1. `pnpm typecheck && pnpm lint && pnpm test` — all green incl. the 8 new
   vitest cases (contract T1–T8).
2. CDP rendered checks (contract rows C1–C6): typing filters live,
   "BAR"/"bar" identical, content-match via a live throwaway reply, empty
   state on nonsense query, × and Escape restore, delete/Load more/open
   while searching stay green (FR-010 subset).
