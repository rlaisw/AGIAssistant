---
description: "Task list for feature implementation"
---

# Tasks: Delete Conversation

**Input**: Design documents from `specs/015-conversation-delete/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/conversation-delete.md, quickstart.md

**Tests**: INCLUDED — user requirement (tests-first + error handling) and Constitution II; every pure module gets failing vitest before implementation (data-model.md test matrix).

**Organization**: Pure logic (delete machine, store seam) precedes route + UI so each story is independently testable. Root = `ai-chat-landing/` unless prefixed.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: parallelizable (different files, no dependencies)
- **[Story]**: user story (US1/US2)

---

## Phase 1: Setup

- [x] T001 Extend `HistoryErrorCode` in `ai-chat-landing/lib/history/types.ts` to add `"delete_failed"` (data-model.md Error entity; additive — existing codes unchanged)

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: pure modules + tests first; US1 cannot begin until green. The two tracks touch different files and can run in parallel.

- [x] T002 [P] Write FAILING vitest for the store `remove` seam in `ai-chat-landing/lib/history/state.test.ts`: drops the record by difyId; other records untouched; missing difyId is a no-op; removing the last record of a bucket makes the bucket heading vanish on regroup (014 FR-003 holds); store immutability invariants preserved
- [x] T003 [P] Implement `remove(difyId: string): void` in `ai-chat-landing/lib/history/state.ts` to pass T002 (success-only call site per FR-005 — the route wiring, not the store, enforces backend-first)
- [x] T004 [P] Write FAILING vitest for the delete machine in `ai-chat-landing/lib/history/delete.test.ts`: full transition table idle→menu→confirming→in-flight→ok (menu closed on success); double-confirm ignored while in-flight (FR-006); failure → menu + `HistoryError("delete_failed")`, row kept (FR-005); cancel → zero state change + zero `deleteRequest` calls (FR-002); injected `deleteRequest` resolves before row removal is signaled (ordering, FR-003)
- [x] T005 [P] Implement `createDeleteState(deleteRequest)` in `ai-chat-landing/lib/history/delete.ts` to pass T004 (status: idle | menu | confirming | in-flight | error; open/chooseDelete/confirm/cancel; error carries only `delete_failed` — contracts §2)

**Checkpoint**: `pnpm test` green; no UI/backend changes yet; US1 can begin.

---

## Phase 3: User Story 1 — Delete via "…" menu (Priority: P1) 🎯 MVP

**Goal**: Hover a conversation row → "…" → Delete → inline confirm → row gone (backend-real, survives reload).

**Independent Test**: quickstart S1 + S3 — create two throwaway chats, delete one, reload: still gone; Dify stopped → row stays with inline error.

### Implementation for User Story 1

- [x] T006 [US1] Create `ai-chat-landing/app/api/conversations/[id]/route.ts` (DELETE): proxy Dify `DELETE /conversations/{id}` with `user: "ai-chat-ui-user"`; validate id `^[A-Za-z0-9_-]+$` (400 otherwise); map upstream to `200 {"ok": true}` / `404 not found` / `502 Dify error (<status>)` / `503 key missing` per contracts §1; never echo key or user; idempotent-404 semantics
- [x] T007 [US1] Add the per-row "…" affordance + dropdown to `ai-chat-landing/components/chat-history.tsx`: icon appears on hover/focus (FR-001), focusable + Enter-to-open (FR-007), opens the existing DropdownMenu with a destructive Delete item only (v1, no Rename), rendered per-row from a `createDeleteState` instance; rows without a difyId (drafts) never render the "…" (FR-008)
- [x] T008 [US1] Implement the inline confirmation inside the dropdown in `ai-chat-landing/components/chat-history.tsx`: menu → "Delete this chat? This cannot be undone." + Delete/Cancel (FR-002); confirm disabled while in-flight (FR-006); on `delete_failed` show "Could not delete this chat — please try again." inline and keep the row (FR-005); on success call `history.remove(difyId)` + `syncHistory` then close (FR-003)
- [x] T009 [US1] Wire `deleteRequest` in `ai-chat-landing/app/page.tsx`: `DELETE /api/conversations/{id}` call passed down through ChatHistory props; non-2xx → `HistoryError("delete_failed")` with the route's error detail; on success the row removal already flows through `history.remove` + `syncHistory` (T008)
- [x] T010 [US1] Verify: `pnpm test` + typecheck + lint green; quickstart S1 pass (row gone instantly, bucket heading vanishes when emptied, reload keeps it gone); quickstart S3 error pass (Dify stopped → row stays + inline error, retry works)

**Checkpoint**: MVP — delete works end-to-end, backend-real, honestly failing.

---

## Phase 4: User Story 2 — Safe state transitions (Priority: P2)

**Goal**: Deleting the open conversation aborts the in-flight stream and falls back to a fresh draft; cancel is a complete no-op.

**Independent Test**: quickstart S2 + S4 — delete active conversation mid-stream → fresh draft, no stream residue; cancel → untouched.

### Implementation for User Story 2

- [x] T011 [US2] Extend the delete wiring in `ai-chat-landing/app/page.tsx`: when the deleted conversation is the active one (`active?.difyId === deletedId`), invoke the existing stream abort (`abortRef.current?.abort()`) BEFORE removal, then switch to a fresh draft via the existing `newChat()` flow (US2/AC1, mid-stream edge); extend the delete-machine test in `ai-chat-landing/lib/history/delete.test.ts` if any ordering assertion changes
- [x] T012 [US2] Verify quickstart S2 + S4: active-deletion mid-stream → pane is a clean empty draft, no stream writes land anywhere; cancel leaves the conversation openable; last-conversation deletion → sidebar empty state + "New chat" works

**Checkpoint**: all stories complete.

---

## Phase 5: Polish & Cross-Cutting Concerns

- [x] T013 [P] Full validation: `pnpm test`, `pnpm typecheck`, `pnpm lint` in `ai-chat-landing/` (never `pnpm build` while `pnpm dev` runs — AGENTS.md)
- [x] T014 [P] Execute quickstart.md S1–S7 against the running stack (S5 spec-014 regression: buckets/Load-more/resume/draft-promotion unaffected; S7 PDF-export regression)
- [x] T015 [P] Add the one-line feature note to `ai-chat-landing/README.md` (per-row "…" → Delete with inline confirm; backend-real)
- [x] T016 Constitution gate: additive-only (one route + UI affordance, MCP schemas untouched); full pytest suite unaffected (no Python touched — `uv run --extra dev pytest tests -q --co` clean)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: immediate — types gate the error code
- **Phase 2 (Foundational)**: after Phase 1; **blocks all stories** (delete machine + store seam are the base)
- **Phase 3 (US1)**: after Phase 2; route + row UI + wiring
- **Phase 4 (US2)**: after Phase 3 (active-deletion wiring builds on US1's deleteRequest path)
- **Phase 5 (Polish)**: after all stories

### Within Each User Story

- Tests failing first (Phase 2 pairs T002→T003, T004→T005)
- Pure modules → route → component → page wiring → verification
- Never weaken a test to pass it — fix the code (Constitution II)

### Parallel Opportunities

- Phase 2: Track A (store seam: T002→T003) and Track B (delete machine: T004→T005) fully parallel — different files
- Phase 5: T013–T015 all [P]

---

## Parallel Example: Phase 2

```bash
Track A: T002 (state.test.ts remove cases) → T003 (state.ts remove())
Track B: T004 (delete.test.ts machine)    → T005 (delete.ts)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 + Phase 2 (types, delete machine, store seam — tests green)
2. Phase 3 (route, row UI, wiring)
3. **STOP and VALIDATE**: quickstart S1/S3 — delete is backend-real and honestly failing
4. Demo-ready

### Incremental Delivery

1. Foundation → US1 (delete via menu) → US2 (active-deletion + stream abort) → Polish (regressions + docs)
2. Each story independently verifiable via its quickstart section.

---

## Notes

- Tests are mandatory (user requirement + Constitution II); failing tests precede every implementation.
- The `deleteRequest` is injected end-to-end — tests never touch the network or Dify.
- `/api/chat` and spec-014 routes are NOT modified; the delete route is a new sibling file (`[id]/route.ts` next to `[id]/messages/route.ts`).
- The abort machinery (`abortRef`) and `newChat()` are reused verbatim — no new stream/draft code.
- Verify against live Dify 1.17 during T006 (contracts §4); a 404-after-delete is idempotent success, not an error.
- Commit after each task or logical group; `pnpm typecheck && pnpm lint` before each commit inside `ai-chat-landing/`.

---

## Phase 6: Convergence

- [x] T017 Update `specs/015-conversation-delete/contracts/conversation-delete.md` §2 seam signature from `confirm()` to `confirm(difyId)` (two occurrences) to match `ai-chat-landing/lib/history/delete.ts` per contracts §2 (partial)

---

## Phase 7: Convergence

- [x] T018 Align the delete machine's terminal-state naming across artifacts: add `"done"` to the status union in `specs/015-conversation-delete/contracts/conversation-delete.md` §2 and relabel data-model.md's diagram terminal from "closed" to "done" to match `ai-chat-landing/lib/history/delete.ts` per contracts §2 (partial)
- [x] T019 Live-verify the active-conversation deletion path (quickstart S2): open a chat, send a message, delete that conversation mid-stream via the "…" menu, and confirm the pane falls back to a clean draft with no stream residue — or, if deferred, annotate T012 with the pending user step per spec US2/AC1 (partial)
