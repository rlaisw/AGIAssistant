---
description: "Task list template for feature implementation"
---

# Tasks: Time-Grouped Chat History

**Input**: Design documents from `specs/014-chat-history-groups/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/chat-history.md, quickstart.md

**Tests**: INCLUDED — user requirement (tests-first + error handling) and Constitution II; every pure module has failing vitest before implementation (data-model.md test matrix).

**Organization**: Tasks grouped by user story; pure logic precedes DOM/UI so each story is independently testable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: parallelizable (different files, no dependencies)
- **[Story]**: user story (US1/US2/US3)
- Root = `ai-chat-landing/` unless prefixed

---

## Phase 1: Setup

- [x] T001 Create `ai-chat-landing/lib/history/types.ts` per data-model.md: `ConversationRecord` (`difyId: string`, `title: string`, `lastActivityAt: number | null` — nullable per R3), `BucketId` (`today | yesterday | previous-7-days | last-month | few-months-ago`), `BucketedConversations`, `HistoryErrorCode` (`history_unavailable | messages_unavailable`), `HistoryError extends Error`

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: pure modules + tests first; all four tracks are independent files — run fully in parallel. `pnpm test` must be green before US1.

- [x] T002 [P] Write FAILING vitest for `bucketOf` in `ai-chat-landing/lib/history/buckets.test.ts`: one record per bucket at a frozen `now`; local-midnight boundary cases (00:01 vs 23:59 same day; exact −1d/−8d/−38d midnights per data-model.md boundary table); `null`/NaN timestamp → floor bucket (FR-001/002/007, edge)
- [x] T003 [P] Implement `bucketOf(lastActivityAt: number | null, now: Date): BucketId` in `ai-chat-landing/lib/history/buckets.ts` to pass T002 (stdlib date math only, zero deps)
- [x] T004 [P] Write FAILING vitest for `groupConversations` in `ai-chat-landing/lib/history/buckets.test.ts`: empty buckets omitted (FR-003); fixed section order (today→few-months-ago); within-bucket most-recent-first with nulls last (FR-004); dedupe by `difyId` keeps the fresher record (merge rule); never mutates input, never throws (data-model invariants)
- [x] T005 [P] Implement `groupConversations(records, now?): BucketedConversations` in `ai-chat-landing/lib/history/buckets.ts` to pass T004
- [x] T006 [P] Write FAILING vitest for `titleFor` in `ai-chat-landing/lib/history/titles.test.ts`: Dify name passthrough; empty/missing name → first-question fallback capped ≤ 60 chars; never "Untitled"; empty-everything → defined placeholder (FR-012)
- [x] T007 [P] Implement `titleFor(difyName, firstQuestion?)` in `ai-chat-landing/lib/history/titles.ts` to pass T006
- [x] T008 [P] Write FAILING vitest for `createHistoryState` in `ai-chat-landing/lib/history/state.test.ts` with an injected `fetchPage` stub: idle→loading→ready; load failure → `HistoryError("history_unavailable")` + error state; Load more while loadingMore ignored; `hasMore=false` → exhausted, no further fetches (FR-006/008/013)
- [x] T009 [P] Implement `createHistoryState(fetchPage)` in `ai-chat-landing/lib/history/state.ts` to pass T008 (records, loadMore, retry, status; no raw exceptions cross the boundary — R6)
- [x] T010 [P] Write FAILING vitest for Dify mappers in `ai-chat-landing/lib/history/mappers.test.ts`: conversation page `{data:[{id,name,created_at,updated_at}], has_more, last_id}` → `{conversations:[{difyId,title,lastActivityAt(ms)}], hasMore, nextCursor}` with `updated_at ?? created_at` and null-when-absent; messages record → paired user/assistant `Message[]` with sequential ids, `metadata.retriever_resources` → deduped sources (contracts §1/§2, R3)
- [x] T011 [P] Implement `mapConversationPage` + `mapMessagesPage` in `ai-chat-landing/lib/history/mappers.ts` to pass T010

**Checkpoint**: `pnpm test` green with zero UI/backend changes; US1 can begin.

---

## Phase 3: User Story 1 — Grouped sidebar from backend history (Priority: P1) 🎯 MVP

**Goal**: Open the app → history loads from the backend and renders under Today / Yesterday / Previous 7 days / Last month / Few months ago.

**Independent Test**: quickstart S1 + S5 error half — reload with several past conversations; only non-empty headings, most-recent-first.

### Implementation for User Story 1

- [x] T012 [US1] Create `ai-chat-landing/app/api/conversations/route.ts` (GET): proxy Dify `GET /conversations` with `user: "ai-chat-ui-user"`, `cursor` → `last_id`, `limit` (default 20, max 100); respond `{conversations, hasMore, nextCursor}` via `mapConversationPage`; errors `502`/`503` per contracts §1; never echo key/user
- [x] T013 [US1] Create `ai-chat-landing/components/chat-history.tsx`: render `BucketedConversations` with bucket labels (Today/Yesterday/Previous 7 days/Last month/Few months ago), loading skeleton, honest `history_unavailable` notice with retry (FR-003/008/011), and per-conversation click callback
- [x] T014 [US1] Wire fetch-on-open in `ai-chat-landing/app/page.tsx`: on mount call `GET /api/conversations`, feed `createHistoryState`, render `chat-history.tsx` in the sidebar; DELETE the hardcoded `sidebarGroups` array and canned `group` fields (Constitution V — delete, don't dead-code); keep "New chat" above the groups (FR-009)
- [x] T015 [US1] Verify: `pnpm test` + typecheck + lint green; quickstart S1 pass (real backend groups, empty headings absent, ordering correct)

**Checkpoint**: MVP — backend-backed grouped history visible on open.

---

## Phase 4: User Story 2 — Resume a past conversation (Priority: P2)

**Goal**: Click any conversation → its history loads in the chat pane; follow-ups continue it.

**Independent Test**: quickstart S2 — resume an old conversation, send a message, reply arrives in-session.

### Implementation for User Story 2

- [x] T016 [US2] Create `ai-chat-landing/app/api/conversations/[id]/messages/route.ts` (GET): proxy Dify `GET /conversations/{id}/messages` (limit 100, cursor passthrough), map via `mapMessagesPage` to the app `Message[]` shape; `404` unknown id, `502` upstream failure → client `HistoryError("messages_unavailable")` (contracts §2)
- [x] T017 [US2] Wire resume-on-click in `ai-chat-landing/app/page.tsx`: clicking a sidebar conversation fetches its messages, sets them as the active chat with `difyId` (so the existing chat route continues that conversation — zero changes to `/api/chat`), and shows a per-action inline error on fetch failure (sidebar untouched — R6 degradation rule)
- [x] T018 [US2] Implement draft promotion (FR-014, R7) in `ai-chat-landing/app/page.tsx`: "New chat" stays a session-only draft; when the first message's `done` stream event returns `conversationId`, promote the draft to a `ConversationRecord` under Today (it never reaches history before that; reload does not resurrect empty drafts)
- [x] T019 [US2] Verify: quickstart S2 + S3 pass; messages-unavailable case shows inline error without blanking the sidebar

**Checkpoint**: resume + draft lifecycle done; reload persistence complete.

---

## Phase 5: User Story 3 — Immediate re-grouping + Load more (Priority: P3)

**Goal**: Activity moves conversations to Today instantly; long histories reachable via Load more.

**Independent Test**: quickstart S4 + S2 step 2 — send in an old conversation → it jumps to Today without reload; Load more appends and disappears at exhaustion.

### Implementation for User Story 3

- [x] T020 [US3] Wire activity re-grouping in `ai-chat-landing/app/page.tsx`: on send/resume update that record's `lastActivityAt` to `Date.now()` in the session store so the next `groupConversations` render puts it under Today immediately (FR-006)
- [x] T021 [US3] Add the "Load more" control to `ai-chat-landing/components/chat-history.tsx`: visible only while `hasMore` (calls `state.loadMore()` with `nextCursor`), busy state during fetch, absent at exhaustion — never silently hiding pages (FR-013)
- [x] T022 [US3] Verify: quickstart S4 pass (appends pages, control disappears at end); S2 step 2 re-grouping pass

**Checkpoint**: all stories complete.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [x] T023 [P] Full validation: `pnpm test`, `pnpm typecheck`, `pnpm lint` in `ai-chat-landing/` (never `pnpm build` while `pnpm dev` runs — AGENTS.md)
- [x] T024 [P] Execute quickstart.md S1–S7 against the running stack, including the S5 error-handling scenario (stop `docker-nginx-1` → honest notice; restart → recovers) and the S7 PDF-export regression (spec 013 untouched)
- [x] T025 [P] Add the one-line feature note to `ai-chat-landing/README.md` (sidebar history grouping + resume + Load more); no other docs
- [x] T026 Constitution gate: confirm no MCP schema / sidecar change (Chat UI + two same-origin routes only), full pytest suite unaffected (no Python touched — spot-check `uv run --extra dev pytest tests -q --co` clean)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: immediate — types gate everything
- **Phase 2 (Foundational)**: after Phase 1; **blocks all stories** (pure seams + tests)
- **Phase 3 (US1)**: after Phase 2; establishes the sidebar + list route
- **Phase 4 (US2)**: after Phase 3 (click callbacks exist); messages route + wiring
- **Phase 5 (US3)**: after Phase 4 (activity updates build on resume wiring)
- **Phase 6 (Polish)**: after all stories

### Within Each User Story

- Tests failing first (Phase 2 pairs T002→T003, T004→T005, T006→T007, T008→T009, T010→T011)
- Pure modules → API route → component → page wiring → verification
- Never weaken a test to pass it — fix the code (Constitution II)

### Parallel Opportunities

- Phase 2: all four module tracks [P] — independent files, run together
- T023–T025 in Phase 6 all [P]
- T012 (list route) can start as soon as T011 lands, in parallel with T013 (component)

---

## Parallel Example: Phase 2

```bash
# Four independent test→impl tracks:
Track A: T002 (bucketOf test)      → T003 (bucketOf impl)
Track B: T004 (group test)         → T005 (group impl)        # same file as Track A — run after T003
Track C: T006 (titles test)        → T007 (titles impl)
Track D: T008 (state test)         → T009 (state impl)
Track E: T010 (mappers test)       → T011 (mappers impl)
```
(Note: Tracks A+B share `buckets.ts` — sequential within the track pair, but independent of C/D/E.)

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 + Phase 2 (types, pure modules, tests green)
2. Phase 3 (US1: list route + component + wiring)
3. **STOP and VALIDATE**: quickstart S1 — grouped history visible on reload
4. Demo-ready: the sidebar shows real, grouped, reload-safe history

### Incremental Delivery

1. Foundation → US1 (grouped sidebar) → US2 (resume + drafts) → US3 (regroup + Load more) → Polish (full battery + docs)
2. Each story is independently verifiable via its quickstart section; nothing breaks the previous story.

---

## Notes

- Tests are mandatory (user requirement + Constitution II); every implementation task in Phase 2 has its failing test first.
- All fetches go through the injected `fetchPage` seam — tests never touch the network or Dify.
- The `/api/chat` route is NOT modified — resume reuses `difyId` on the existing POST (Constitution I).
- Verify Dify field names against the live API during T012/T016 (contracts §4 assumptions); if `updated_at` is absent in this Dify version, R3's `created_at` fallback applies without design change.
- Commit after each task or logical group; `pnpm typecheck && pnpm lint` before each commit inside `ai-chat-landing/`.
