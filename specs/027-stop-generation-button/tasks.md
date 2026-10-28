---
description: "Task list for Stop Generation Button (feature 027)"
---

# Tasks: Stop Generation Button

**Input**: Design documents from `/specs/027-stop-generation-button/`

**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/stop-generation.md ✓, quickstart.md ✓

**Tests**: Requested at plan time ("create test cases and add error handling") and mandated by Constitution II — test tasks included, unit suite written failing-first.

**Organization**: Grouped by user story (US1 P1 → US2 P2 → US3 P3) for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: User story the task belongs to
- Exact file paths in every description

## Path Conventions

Web-app layout: all feature code in `ai-chat-landing/` (Next.js 16 App Router); battery scenario in `src/agentic_rag_mcp/deploy/`. No sidecar/MCP changes (research R9).

---

## Phase 1: Setup

**Purpose**: Verify the one live-stack assumption before any wiring

- [x] T001 Verify live that Dify 1.18 stream events for the deployed "AGI Assistant" app carry `task_id` (one-off capture through `ai-chat-landing/app/api/chat/route.ts` logging or a direct curl against the Dify streaming API); record the observed event type(s) and shape as an addendum note in `specs/027-stop-generation-button/research.md` (R2 verification gate)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The pure stop state machine (tested) and the task_id transport — everything else builds on these

**⚠️ CRITICAL**: No user story work begins until this phase is complete

- [x] T002 [P] Write the failing-first vitest suite `ai-chat-landing/lib/stop/state.test.ts` covering quickstart cases A1–A7 exactly: composerMode visibility (incl. FR-010 viewed-conversation rule), double-stop no-op latch (FR-009), completion race resolution, empty-stop `remove-empty-turn`, mid-stream `finalize-stopped` (text+reasoning kept, streaming:false, stopped:true), session-only caption derivation, and `shouldCallBackendStop` (false for demo mode and missing taskId). Signatures per `specs/027-stop-generation-button/contracts/stop-generation.md` §3. Suite MUST fail (module absent) before T003
- [x] T003 Implement `ai-chat-landing/lib/stop/state.ts` (composerMode, decideStopAction, finalizeOnStop, shouldCallBackendStop) until `state.test.ts` is green — no page.tsx changes yet
- [x] T004 [P] Add the additive `task` stream event to `ai-chat-landing/app/api/chat/route.ts`: capture first-seen `event.task_id`, emit `{ "type": "task", "taskId": "..." }` exactly once; all existing event emissions byte-identical (Constitution I; unknown-event tolerance is the compat rule). Depends on T001's recorded shape

**Checkpoint**: State machine green in vitest; task id reaches the browser. User story wiring can begin.

---

## Phase 3: User Story 1 — Stop an in-progress answer (Priority: P1) 🎯 MVP

**Goal**: Send button morphs to Stop during generation; activating it halts the backend generation, aborts the local stream, keeps the partial answer, and returns the composer to ready in < 1 s (FR-001/002/003/004/006, SC-001).

**Independent Test**: Ask a long question, click Stop mid-stream — partial text remains, composer ready, follow-up answerable; battery scenario proves no further content is generated (SC-005).

### Tests for User Story 1

- [x] T005 [P] [US1] Author `ai-chat-landing/scripts/stop-button-check.mjs` (CDP, patterned on `ai-chat-landing/scripts/wide-layout.mjs`, Chrome on `--remote-debugging-port=9240`) covering quickstart B1 (morph during generation; typing enabled, sending disabled) and B2 (stop mid-stream: composer ready < 1 s, partial text kept, no growth after stop)
- [x] T006 [P] [US1] Add the `stop-generation` battery scenario to `src/agentic_rag_mcp/deploy/battery.py` (registry pattern of `chat-ui-liveness`): stop a live generation, wait a fixed interval ≥ 5 s, re-fetch the conversation messages, assert the stopped answer text has not grown (SC-005/FR-006 verified backend halt)

### Implementation for User Story 1

- [x] T007 [P] [US1] Create `ai-chat-landing/app/api/chat/stop/route.ts` per contracts §2: POST `{ taskId: string, non-empty, ≤ 128 chars }` → `200 { result: "ok" | "no-task" }` | `400 { error }` | `502 { error ≤ 200 chars }`; forward to the backend stop endpoint with the same end-user identifier the chat proxy sends (`ai-chat-ui-user`); DIFY_API_KEY stays server-side
- [x] T008 [US1] In `ai-chat-landing/app/page.tsx`: capture `taskId` from the new `task` stream event into the in-flight generation state (additive case in the reader switch; data-model §2)
- [x] T009 [US1] In `ai-chat-landing/app/page.tsx`: composer morph via `composerMode({ busy, viewingGeneratingConversation })` from `lib/stop` — Stop renders in place of Send (label + aria "Stop"), typing stays enabled, sending disabled (FR-001; the existing `busy` guard already blocks send)
- [x] T010 [US1] In `ai-chat-landing/app/page.tsx`: stop handler — latch `stopRequested` (FR-009), call `/api/chat/stop` only when `shouldCallBackendStop` (fire-and-forget with console.warn on failure — client aborts regardless), abort `abortRef`, and route the `AbortError && !timedOut` branch through `decideStopAction`/`finalizeOnStop` instead of the current silent `return` (research R3 supersedes record; watchdog `timedOut` path byte-identical)

**Checkpoint**: MVP complete — stop works end-to-end with backend halt; run T005 + T006 before proceeding.

---

## Phase 4: User Story 2 — Stopped turn stays honest and usable (Priority: P2)

**Goal**: The stopped turn carries a visible "Stopped" caption and never masquerades as complete; the conversation stays fully usable afterward (FR-007/008, SC-002).

**Independent Test**: After a stop: follow-up question answers normally; reload shows the partial text without the caption (session-only); delete/search/PDF export unchanged.

### Tests for User Story 2

- [x] T011 [P] [US2] Extend `ai-chat-landing/scripts/stop-button-check.mjs` with quickstart B3 (follow-up answer works with sources) and D5 (reload: partial text intact, NO caption, conversation resumes and answers) — depends on T005
- [x] T012 [US2] Run the conversation-feature regression sweep after a stop (quickstart §B3/D5 + existing suites): follow-up, history resume, delete, search, PDF export; evidence recorded in the commit message of this task

### Implementation for User Story 2

- [x] T013 [US2] In `ai-chat-landing/app/page.tsx`: add the session-only `stopped?: boolean` field to the in-memory Message view model (data-model §1 — never sent upstream, never persisted; conversation switching keeps it, reload drops it)
- [x] T014 [US2] In `ai-chat-landing/app/page.tsx`: render the "Stopped" caption under the partial text for `stopped` messages and suppress completion affordances after the stop point (no sources badge additions post-stop; error turns render distinctly from stopped turns — FR-007, checklist CHK012)

**Checkpoint**: Honest stopped state complete; US1 behavior unchanged.

---

## Phase 5: User Story 3 — Stop behaves sanely at the boundaries (Priority: P3)

**Goal**: Edge matrix wired: thinking-phase stop, double-click, completion race, demo mode, conversation switch (FR-009/010, spec Edge Cases).

**Independent Test**: Run the edge matrix — every case ends consistent, none stuck (quickstart §B4–B7, §D2/D6).

### Tests for User Story 3

- [x] T015 [P] [US3] Extend `ai-chat-landing/scripts/stop-button-check.mjs` with quickstart B4 (thinking-phase stop: no empty assistant bubble), B5 (double-click: single stop), B6 (conversation switch mid-generation: generation continues, Stop visible only in owning view), B7 (demo-mode stop) — depends on T011

### Implementation for User Story 3

- [x] T016 [US3] In `ai-chat-landing/app/page.tsx`: thinking-phase stop — `decideStopAction` returns `remove-empty-turn`, the assistant placeholder is removed (no empty bubble, no caption; the user's question stays)
- [x] T017 [US3] In `ai-chat-landing/app/page.tsx`: double-click guard + completion-race wiring — second activation no-ops on the latch (A2); `done` arriving after the latch resolves to one consistent outcome, never stuck-streaming (A3)
- [x] T018 [US3] In `ai-chat-landing/app/page.tsx`: demo-mode stop — `demoStream` interval cleared on stop, message finalized with caption, `busy` cleared, no backend call (`shouldCallBackendStop` false; research R6)
- [x] T019 [US3] In `ai-chat-landing/app/page.tsx`: conversation-switch semantics — switching never aborts the in-flight generation; the morph shows Stop only while viewing the generating conversation (FR-010, single-flight per research R5)

**Checkpoint**: All stories independently functional; full matrix passes.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [x] T020 [P] Run the error-handling matrix from quickstart §D and record results inline in `specs/027-stop-generation-button/quickstart.md` §D: D1 block `/api/chat/stop` → client still stops < 1 s + console.warn; D2 `no-task` race = success; D3 stop-route 502 → clean client stop; D4 watchdog-timeout UX unchanged (regression); D6 stop-at-`done` race consistent
- [x] T021 [P] Docs sync: add the stop feature to the AGENTS.md (`/kilocode/AGIAssistant/AGENTS.md`) and `ai-chat-landing/AGENTS.md` + `ai-chat-landing/README.md` feature-surface lines, and a DEPLOY.md troubleshooting row for stop-route failures (pattern of the image-proxy fix)
- [x] T022 Full green sweep: `pnpm test && pnpm typecheck && pnpm lint` in `ai-chat-landing/`, `pytest tests/unit/` at repo root (battery scenario compiles/registers), `node scripts/stop-button-check.mjs` exit 0; note — `specs/027-stop-generation-button/checklists/error-handling.md` markers are reviewer-owned and must NOT be toggled by implementation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1** → no dependencies. **Phase 2** → depends on T001 (T004 only); T002/T003 independent of T001. **User stories** → depend on Phase 2 complete. **Polish** → after all desired stories.

### User Story Dependencies

- **US1 (P1)**: after Phase 2 — no other story needed. **MVP = Phase 1+2+3.**
- **US2 (P2)**: after US1 (finalize path exists); independently testable via its own checks.
- **US3 (P3)**: after US1 (stop handler exists); its edge cases extend US1/US2 wiring in the same file.

### Within-Story Ordering

- T008 → T009 → T010 sequential (same file: `page.tsx`); T005/T006/T007 parallel (different files).
- T013 → T014 sequential (`page.tsx`); T011 parallel once T005 lands.
- T016 → T017 → T018 → T019 sequential (`page.tsx`); T015 parallel once T011 lands.

### Parallel Opportunities

- Phase 2: T002 ∥ T004 (then T003 after T002).
- US1: T005 ∥ T006 ∥ T007 while T008–T010 proceed on `page.tsx`.
- US2: T011 ∥ (T013 → T014).
- US3: T015 ∥ (T016 → T017 → T018 → T019).
- Polish: T020 ∥ T021, then T022.

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Phase 1 (T001) → 2. Phase 2 (T002–T004) → 3. Phase 3 (US1) → 4. **STOP and VALIDATE**: run T005 CDP + T006 battery + `pnpm test` — the stop works end-to-end with verified backend halt.

### Incremental Delivery

Add US2 (honesty + usability), then US3 (edges), then Polish (error matrix + docs + full sweep). Each story leaves the previous behavior unchanged.

---

## Notes

- [P] = different files, no dependencies on incomplete tasks
- Unit suite (T002) is written FIRST and fails before T003 — Constitution II
- The silent `AbortError → return` path in `page.tsx` is deliberately superseded by T010 (Constitution V record in plan.md)
- Commit after each task or logical group; `pnpm typecheck && pnpm lint` before every commit inside `ai-chat-landing/`
- Do not mark the reviewer-owned `checklists/error-handling.md` items during implementation
- Battery scenario T006 must not require a model dropdown or spec-026 state — stop works for any serving model

---

## Phase 7: Convergence

- [x] T023 Sync the stop-state contracts and data model with the implemented interface: add the dated additive `hasReasoning` input and the "remove only when text AND reasoning are both empty" rule to `specs/027-stop-generation-button/contracts/stop-generation.md` §3 (`decideStopAction`/`finalizeOnStop`), and add `conversationId` to the `task` event row in `specs/027-stop-generation-button/data-model.md` §3 per contracts §1 (partial)
- [x] T024 Run the B7 demo-mode stop check once against a key-less dev server (no `DIFY_API_KEY` in `ai-chat-landing/.env.local`, port 3001 or a second instance): canned stream stops with caption, composer ready, no backend call — record the result in `specs/027-stop-generation-button/quickstart.md` §B (per US1 / quickstart §B7 / research R6) (partial)
- [x] T025 Run the D4 watchdog-timeout regression once (stall the upstream ~120 s with no events, e.g. point `DIFY_API_BASE_URL` at a dribbling endpoint): existing error UX unchanged, no stop-latch interference — record the result in `specs/027-stop-generation-button/quickstart.md` §D (per FR-005 / quickstart §D4 / research R3) (partial)
- [x] T026 Verify US3/AC3 live once: send a deck-generating question, stop mid-answer, assert the already-emitted deck export link in the partial text remains clickable and downloads — record the result in `specs/027-stop-generation-button/quickstart.md` §B (per US3/AC3) (partial)
