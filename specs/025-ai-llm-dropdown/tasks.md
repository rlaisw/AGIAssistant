---
description: "Task list for feature implementation"
---

# Tasks: "AI LLM" Model Drop-Down Menu

**Input**: Design documents from `/specs/025-ai-llm-dropdown/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/model-selection.md, quickstart.md — all present.

**Tests**: Included — constitution Principle II (tests-first) and the plan request ("create test cases and add error handling"). Test tasks precede implementation in every story.

**Organization**: Phases by user story (P1 → P2 → P3), each independently testable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: parallelizable (different files, no dependency on incomplete tasks)
- **[Story]**: US1 = pick & chat, US2 = honest availability, US3 = persistence
- File paths are exact.

---

## Phase 1: Setup (Shared Infrastructure)

- [X] T001 [P] Create the no-think local model: write `dify/AGIAssistant/ollama/qwen3-8b-nothink.Modelfile` (`FROM qwen3:8b` + the think-off parameter — verify the exact parameter name with `ollama show --modelfile qwen3:8b` on the installed Ollama 0.40.11), then run `ollama create qwen3-8b-nothink -f <Modelfile>` on the host; verify with `ollama list` + a short test chat showing no reasoning block
- [X] T002 [P] Create the model catalog in `ai-chat-landing/lib/models/options.ts` — exactly two options: id `"cloud"` (displayName "DeepSeek", isDefault true, available always true) and id `"local"` (displayName "Qwen3 8B", hint "slower, runs on this host's CPU"); ids are the stable strings `"cloud" | "local"` (data-model.md ModelOption)

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: No live user-story work until this phase is complete — the chatflow must route before the UI can switch.

- [X] T003 Add start input variable `ai_model` (default `"cloud"`, allowed values `"cloud" | "local"`, absent input = cloud) to the start node in `dify/AGIAssistant/AGI_Assistant.yml` (contracts §2)
- [X] T004 Add the `model_router` IF/ELSE node in `dify/AGIAssistant/AGI_Assistant.yml`: condition `{{#start.ai_model#}} == "local"` → `intent_router_local`, else → `intent_router`; REPLACE the `start → intent_router` edge with `start → model_router` fan-out — delete the old edge, no dead edges (contracts §3; depends T003)
- [X] T005 Add the three local branch nodes in `dify/AGIAssistant/AGI_Assistant.yml` — `intent_router_local` (question-classifier), `agentic_strategy_local` (agent, full tool set), `ppt_master_local` (agent, full tool set) — exact copies of their cloud counterparts with model `qwen3-8b-nothink` (Ollama provider, thinking disabled per FR-009); add edges to the SHARED answer nodes: `agentic_strategy_local → answer`, `ppt_master_local → ppt_answer` (depends T004)
- [X] T006 [P] Register the Ollama model provider via the deploy CLI in `src/agentic_rag_mcp/deploy/`: base URL `http://172.17.0.1:11434` (docker bridge gateway) and model name `qwen3-8b-nothink` in config, console-API provider setup alongside the existing chatflow publish path; secrets redacted in output (research D2)
- [X] T007 [P] Forward `inputs.ai_model` in `ai-chat-landing/app/api/chat/route.ts`: pass the per-conversation selection to `/v1/chat-messages`; absent/invalid selection → omit the input entirely (contract: absent = cloud, battery requests stay byte-identical)
- [X] T008 Publish and smoke the routed graph: run `python -m agentic_rag_mcp.deploy chatflow` (project venv), then one live send with NO `ai_model` input — cloud path must answer exactly as before (depends T001–T007)

**Checkpoint**: chatflow routes on `ai_model`; absent input = today's behavior.

---

## Phase 3: User Story 1 - Pick the model and chat with it (Priority: P1) 🎯 MVP

**Goal**: single-select Cloud/Local in the UI; every subsequent reply runs on the selected model and carries a footer badge naming it.

**Independent Test**: SC-001 — switch to Local (≤2 interactions), reply badge reads "Qwen3 8B"; switch back; earlier messages unchanged.

### Tests for User Story 1 (write FIRST, must fail)

- [X] T009 [P] [US1] Vitest suite `ai-chat-landing/lib/models/selection.test.ts`: single-select invariant (selecting one leaves exactly one active), user switch applies from the next message, stored value outside `{"cloud","local"}` → treated as cloud, new conversation → cloud
- [X] T010 [P] [US1] Vitest suite `ai-chat-landing/lib/models/persistence.test.ts`: set/get round-trip for `agi-model:selection:<conversationId>`, absent key → cloud, unreadable storage (private mode) → cloud, never throws
- [X] T011 [P] [US1] Vitest suite `ai-chat-landing/lib/models/badge.test.ts`: map hit → that model, map miss → cloud (backfill rule), entries written once at stream completion and never mutated, mid-conversation switch leaves earlier entries untouched

### Implementation for User Story 1

- [X] T012 [P] [US1] Implement `ai-chat-landing/lib/models/selection.ts` — the selection state machine from data-model.md (new→cloud; select→switch; reset rules wired later in US2)
- [X] T013 [P] [US1] Implement `ai-chat-landing/lib/models/persistence.ts` — localStorage keys `agi-model:selection:<conversationId>` and `agi-model:badge:<conversationId>`, try/catch on all storage access
- [X] T014 [P] [US1] Implement `ai-chat-landing/lib/models/badge.ts` — messageId→model resolution with cloud backfill on absence
- [X] T015 [US1] Implement `ai-chat-landing/components/model-dropdown.tsx` — single-select menu over the catalog: exactly two entries, active marked, FR-006 hint beside Local, trigger label distinct from the sidebar's "Conversation options" (use the existing house menu primitives; no new deps)
- [X] T016 [US1] Wire the feature into `ai-chat-landing/app/page.tsx`: dropdown trigger near the composer, selection flows to the send path as `inputs.ai_model` (via T007), assistant message footer renders the badge from T014 — write the map entry at stream completion (depends T012–T015)

**Checkpoint**: SC-001 passes on a throwaway conversation (delete after).

---

## Phase 4: User Story 2 - Honest availability of the local model (Priority: P2)

**Goal**: Local that is down is visibly unavailable, unselectable, and the conversation keeps working on Cloud with a persistent inline note.

**Independent Test**: SC-002 — stop Ollama, dropdown marks Local unavailable ≤5 s; a send completes on Cloud with the inline reset note; error matrix rows 1–5 hold.

### Tests for User Story 2 (write FIRST, must fail)

- [X] T017 [P] [US2] Vitest suite `ai-chat-landing/lib/models/availability.test.ts`: probe success / timeout / malformed body / HTTP error → `available: false` (never guessed), ≤5 s budget honored via fake timers, cloud always `true`
- [X] T018 [P] [US2] Vitest suite for `ai-chat-landing/app/api/models/route.ts` handler with stubbed fetch: reachable + `qwen3-8b-nothink` present → true; reachable + model missing → false; connection refused → false; payload shape per contracts §1

### Implementation for User Story 2

- [X] T019 [P] [US2] Implement `ai-chat-landing/lib/models/availability.ts` — client probe of `GET /api/models`, fetched when the dropdown opens
- [X] T020 [P] [US2] Implement `ai-chat-landing/app/api/models/route.ts` — host-side probe of `127.0.0.1:11434/api/tags` with 2 s timeout + model-presence check; returns both options, cloud `available: true` always; Ollama address never in the payload
- [X] T021 [US2] Add the unavailable state to `ai-chat-landing/components/model-dropdown.tsx`: Local marked unavailable + short status text, unselectable (depends T019)
- [X] T022 [US2] Implement the FR-004 send-time fallback in `ai-chat-landing/app/page.tsx` + `ai-chat-landing/lib/models/selection.ts`: probe fails with Local selected → inline persistent system note in the chat stream, stored selection resets to cloud, message sends as cloud
- [X] T023 [US2] Implement the FR-007 mid-stream failure path in `ai-chat-landing/app/page.tsx`: local stream error → existing message error state + the same reset rule (one code path with T022)

**Checkpoint**: SC-002 passes live (kill/restart Ollama; no auto-resume after restart).

---

## Phase 5: User Story 3 - The choice sticks with the conversation (Priority: P3)

**Goal**: selection survives reload/resume; new chats start on Cloud; deleted conversations purge their storage.

**Independent Test**: SC-003 — select Local, reload, resume from sidebar → Local still active; delete the conversation → both storage keys gone.

- [X] T024 [US3] Hydrate the selection on conversation load in `ai-chat-landing/app/page.tsx` (resume path reads `agi-model:selection:<id>`; conversations with no entry stay cloud)
- [X] T025 [US3] Enforce defaults in `ai-chat-landing/app/page.tsx` + `ai-chat-landing/lib/models/persistence.ts`: brand-new chats and drafts (no conversation id yet) always start on cloud
- [X] T026 [US3] Purge `agi-model:selection:<id>` and `agi-model:badge:<id>` when a conversation is deleted — hook into the existing flow in `ai-chat-landing/lib/history/delete.ts` (FR-005 interplay)

**Checkpoint**: SC-003 passes live; delete leaves no keys.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T027 [P] Document the operational steps in `DEPLOY.md`: creating the no-think model, the Ollama provider registration, and the chatflow publish for this feature
- [X] T028 Run the full gates in `ai-chat-landing/`: `pnpm typecheck && pnpm lint && pnpm test` (all suites green, no spec-013–021 regressions) and `python -m agentic_rag_mcp.deploy verify` — 10/10, unchanged and cloud-only (SC-004)
- [X] T029 Execute the live validation scenarios in `specs/025-ai-llm-dropdown/quickstart.md` end-to-end (SC-001..SC-003, FR-009 no-reasoning check, mid-stream kill, storage-key purge) on a throwaway conversation, then delete it

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: no dependencies; T001/T002 parallel.
- **Phase 2 (Foundational)**: T003 → T004 → T005 (same file, sequential); T006/T007 parallel to the DSL chain; T008 after T001–T007. **BLOCKS all stories.**
- **Phase 3 (US1)**: after Phase 2. Tests T009–T011 first (parallel), then T012–T014 (parallel), then T015, T016.
- **Phase 4 (US2)**: after US1's dropdown (T015/T016); its test files T017/T018 can be written in parallel with late US1 work.
- **Phase 5 (US3)**: after US1 (needs persistence T013); independent of US2.
- **Phase 6 (Polish)**: after all desired stories.

### User Story Dependencies

- **US1 (P1)**: Foundational only — the MVP.
- **US2 (P2)**: US1's dropdown component; the one reset rule touches selection.ts (US1's module) — extend, don't duplicate.
- **US3 (P3)**: US1's persistence; the delete hook touches lib/history/delete.ts (spec-015 flow) — additive only.

### Parallel Opportunities

- T001 ∥ T002; T003–T005 chain ∥ T006 ∥ T007
- Per story: all `[P]` test files in parallel; all `[P]` lib modules in parallel
- US2 tests can start while US1 implementation finishes; US3 can proceed in parallel with US2 (different files)

---

## Parallel Example: User Story 1

```bash
# Write all US1 test suites together (they must fail):
Task: "Vitest suite selection.test.ts"
Task: "Vitest suite persistence.test.ts"
Task: "Vitest suite badge.test.ts"

# Then the three lib modules in parallel (different files):
Task: "selection.ts state machine"
Task: "persistence.ts storage"
Task: "badge.ts resolution + backfill"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 + Phase 2 (routed chatflow published, model ready)
2. Phase 3 (US1) complete → **STOP and VALIDATE**: SC-001 on a throwaway conversation
3. Demoable: the dropdown switches models with visible provenance

### Incremental Delivery

1. MVP → add US2 (availability honesty) → validate SC-002
2. Add US3 (persistence + purge) → validate SC-003
3. Polish gates + quickstart run → ship

### Parallel Team Strategy

- Dev A: US1 after Phase 2; Dev B: US2 test files during US1 impl; Dev C: US3 after US1's persistence lands.

---

## Notes

- Tests before implementation in every story (constitution Principle II) — verify they fail first.
- Commit after each task or logical group; battery (T028) must stay byte-identical in its requests — it sends no `ai_model` input.
- Never run `pnpm build` in `ai-chat-landing/` while `pnpm dev` is running.
- After code changes, refresh the codebase graph (`graphify update .`) per AGENTS.md.
- Live checks use throwaway conversations only — delete them afterwards.

---

## Phase 7: Convergence


Convergence pass (2026-10-26): assessed the shipped implementation against
spec.md, plan.md, and tasks.md. All 29 original tasks complete; the findings
below are the remaining traceable gaps.

- [X] T030 Smoke the local deck branch: send a deck-shaped query with `ai_model=local` directly to Dify and verify via SSE `node_started` events that `intent_router_local` routes to `ppt_master_local` (abort the request once the node starts — a full CPU deck run is out of scope) per FR-002/US1-AC2 (partial)
- [X] T031 Distinguish Dify-side send errors from local-model failures in the `send()` catch in `ai-chat-landing/app/page.tsx` — currently every error with a local selection resets to cloud; per research.md error-matrix row 8 a Dify-side rejection (e.g. stale published app) must surface as a normal send error and keep the local selection visible. Suggested: re-probe local availability in the catch — reset + local-failure text only when Local is actually down per FR-007/error-matrix row 8 (contradicts)
- [X] T032 Run the mobile-viewport sanity check from `specs/025-ai-llm-dropdown/quickstart.md` item 7: CDP at 390x844 — the AI LLM trigger opens and both entries are reachable in the overlay layout per US-edge-cases/quickstart (partial)
