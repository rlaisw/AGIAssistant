---
description: "Task list for feature implementation"
---

# Tasks: Apply Selected LLM to the Chatflow (Patch-on-Select)

**Input**: Design documents from `/specs/026-llm-patch-select/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/apply-model.md, quickstart.md — all present.

**Tests**: Included — constitution Principle II (tests-first). Python patch-fn tests and badge-variant tests precede implementation.

**Organization**: Phases by user story (P1 → P2 → P3), each independently testable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: parallelizable (different files, no dependency on incomplete tasks)
- **[Story]**: US1 = apply reconfigures, US2 = honest lifecycle, US3 = persists as app default
- File paths are exact.

---

## Phase 1: Setup (Shared Infrastructure)

- [X] T001 [P] Add `export_app()` to `src/agentic_rag_mcp/deploy/dify_console.py` — GET `/apps/{app_id}/export?include_secret=false` and return the YAML text (raises `ConsoleError` on failure)

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: The cycle must exist and be proven live before any UI work.

### Tests first (must fail before T003 exists)

- [X] T002 [P] Pytest suite `tests/unit/test_deploy_model_apply.py` for the patch function: (a) sets the model on exactly the three main node ids — `intent_router` (question-classifier `data.model`), `agentic_strategy` and `ppt_master` (`agent_parameters.model.value`) — provider `langgenius/openrouter/openrouter`, `completion_params: {}`, other nodes (e.g. the `*_local` branch) untouched; (b) idempotent FR-005 cleanup — removes all `*_kimi/_glm/_qwen38` nodes, their edges, the router's `kimi/glm/qwen38` cases, and the `cloud_model` start variable; a second run is a no-op; (c) unknown node shapes raise honestly

### Implementation

- [X] T003 Implement `src/agentic_rag_mcp/deploy/model_apply.py` — the cycle per contracts §4: export → write `dify/AGIAssistant/AGI_Assistant.yml` → patch (T002's rules) → `update_workflow_draft` → `publish`; `RunReport` entry per step; any failure aborts naming the failing step and leaves the published config untouched (FR-004)
- [X] T004 Extend `src/agentic_rag_mcp/deploy/__main__.py` with the `apply-model <id>` command: validates the id against the cloud catalog (`deepseek/deepseek-v4.1-flash`, `moonshotai/kimi-k3`, `z-ai/glm-5.3-flash`, `qwen/qwen3.8-flash`), `--dry-run` prints the 4-step plan, delegates to T003
- [X] T005 Prove the cycle live: run `pytest tests/unit/test_deploy_model_apply.py -q`, then `.venv/bin/python -m agentic_rag_mcp.deploy apply-model deepseek/deepseek-v4.1-flash` — verify the artifact shows Deepseek in the three main nodes, the extra branches and `cloud_model` are gone from the published app (this lands the FR-005 cleanup live)

**Checkpoint**: cycle works end-to-end; chatflow has a single cloud path again.

---

## Phase 3: User Story 1 - Choosing a model reconfigures the assistant (Priority: P1) 🎯 MVP

**Goal**: selecting a cloud model runs the cycle server-side; the next reply comes from it and is badged accordingly.

**Independent Test**: SC-001 — apply Kimi-k3 (≤90 s), send "Reply with exactly: PONG", badge names Kimi-k3.

### Tests for User Story 1 (write FIRST, must fail)

- [X] T006 [P] [US1] Update `ai-chat-landing/lib/models/badge.test.ts` for the fallback-variant badge values: `"<model-id>|fallback"` — `badgeModel` strips the suffix and returns the id; `badgeNote` detects it and returns the updated note "Local model unavailable — answered by the cloud model instead."; legacy `"cloud-fallback"` still badges as `deepseek/deepseek-v4.1-flash` with a note

### Implementation for User Story 1

- [X] T007 [US1] Implement the fallback-variant in `ai-chat-landing/lib/models/badge.ts` per T006 (make the tests green)
- [X] T008 [P] [US1] Create `ai-chat-landing/app/api/models/current/route.ts` — resolve the configured cloud model from the artifact's three main nodes (`dify/AGIAssistant/AGI_Assistant.yml`): locate the `intent_router` node id, take the next `model:` value within a bounded window; unreadable/missing → `deepseek/deepseek-v4.1-flash` (research D4; cacheless)
- [X] T009 [P] [US1] Create `ai-chat-landing/app/api/models/apply/route.ts` — POST `{model}`: 400 for ids outside the cloud catalog (read from `MODEL_OPTIONS`), 409 while a cycle is in flight, else spawn the `apply-model` cycle (T004), await with a 90 s budget, return `{applied, durationMs}` or `{error}` (contracts §1)
- [X] T010 [US1] Wire `ai-chat-landing/app/page.tsx`: on cloud select (≠ current configured, ≠ local) call T009; `applyingModel` state shows "Applying <displayName>…" with the existing spinner and disables send + Enter + the dropdown until completion (FR-003); on success set the selection (state + storage) to the applied id; on failure show an honest error and revert the visible selection (FR-004); on load fetch T008 and supersede stored cloud selections with the configured model (research D4); local-down fallback writes `"<serving-id>|fallback"` via T007 (research D6)
- [X] T011 [US1] Simplify `ai-chat-landing/app/api/chat/route.ts`: drop the `cloud_model` passthrough — local sends `{ai_model: "local"}`, cloud sends `{ai_model: "cloud"}` (no `cloud_model`; contracts §3)
- [X] T012 [US1] Live verify US1 per quickstart item 1: apply Kimi-k3, blocked send during apply, badge names Kimi-k3 after completion (SC-001)

**Checkpoint**: SC-001 passes on a throwaway conversation.

---

## Phase 4: User Story 2 - Honest reconfiguration lifecycle (Priority: P2)

**Goal**: applying indicator, blocked sends, failure honesty, no-op on same-model.

**Independent Test**: SC-002 — simulated failure shows an error, selection reverts, previous model still answers.

- [X] T013 [US2] Implement the same-model no-op in `ai-chat-landing/app/page.tsx`: selecting the already-configured model starts no cycle and shows no applying state (quickstart item 5)
- [X] T014 [US2] Live verify failure honesty per quickstart item 4: break the cycle mid-run (e.g. make the artifact path unwritable), confirm the apply route returns the failing step, the UI shows the error with the selection reverted, and the next message answers on the previous model; restore afterwards

**Checkpoint**: SC-002 passes; failure never leaves a half-applied app.

---

## Phase 5: User Story 3 - The choice persists as the app default (Priority: P3)

**Goal**: configured model is server truth on load; new chats default to it; badges keep per-message provenance.

**Independent Test**: reload with empty localStorage → dropdown shows the configured model; a brand-new chat answers on it.

- [X] T015 [US3] Live verify per quickstart items 3 and 6: reload with empty localStorage — the dropdown shows the applied model (US3); a new chat answers on it; Local selection and its fallback remain per-conversation and now badge the configured cloud model on fallback

**Checkpoint**: SC-003 (artifact shows the applied model) + US3 live behavior confirmed.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T016 [P] Document the cycle in `DEPLOY.md`: `apply-model` usage, the 4 steps, the artifact contract (FR-007), and failure semantics (previous config keeps serving)
- [X] T017 Run the full gates: `pytest tests/unit/test_deploy_model_apply.py -q`, `pnpm -C ai-chat-landing typecheck && pnpm -C ai-chat-landing lint && pnpm -C ai-chat-landing test`, and `.venv/bin/python -m agentic_rag_mcp.deploy verify` — 10/10 on the default configuration (SC-004)
- [X] T018 Run the remaining quickstart scenarios end-to-end (SC-001..SC-003, failure sim, no-op, local path, blocked sends), re-apply `deepseek/deepseek-v4.1-flash` to restore the default configuration, and delete all throwaway conversations

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: T001 standalone.
- **Phase 2 (Foundational)**: T002 → T003 → T004 → T005 (tests-first chain). **BLOCKS all stories.**
- **Phase 3 (US1)**: after Phase 2. T006 → T007; T008/T009 parallel after T005; T010 after T007–T009; T011 independent file; T012 last.
- **Phase 4 (US2)**: after US1 (T010's applying/revert paths); T013/T014 are live verifications of it.
- **Phase 5 (US3)**: after US1's current-model fetch (T010).
- **Phase 6 (Polish)**: after all desired stories.

### User Story Dependencies

- **US1 (P1)**: Foundational only — the MVP.
- **US2 (P2)**: US1's applying/failure UI paths.
- **US3 (P3)**: US1's current-model route and load behavior.

### Parallel Opportunities

- T001 ∥ T002; T006 ∥ T008 ∥ T009 (after T005); T010 and T011 are separate files but both touch send paths — run sequentially; US2/US3 checks can run back-to-back after T012.

---

## Parallel Example: User Story 1

```bash
# Test file + both new routes in parallel (different files):
Task: "badge.test.ts fallback variants"
Task: "app/api/models/current/route.ts"
Task: "app/api/models/apply/route.ts"
# Then the page wiring (single file, after the routes exist):
Task: "page.tsx applying state + current-model fetch + fallback variant"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 + Phase 2 (cycle proven live, FR-005 cleanup landed)
2. Phase 3 (US1) complete → **STOP and VALIDATE**: SC-001 on a throwaway conversation
3. Demoable: selecting a cloud model reconfigures the app and badges prove it

### Incremental Delivery

1. MVP → add US2 (lifecycle honesty) → validate SC-002
2. Add US3 (server-truth persistence) → validate US3 + SC-003
3. Polish gates + quickstart run + reset to default → ship

---

## Notes

- Tests before implementation (constitution Principle II) — verify they fail first.
- The published app is untouched until the publish step — a failed cycle leaves the previous config serving (FR-004).
- The artifact (`dify/AGIAssistant/AGI_Assistant.yml`) is the cycle-maintained mirror (FR-007); git-versioned for recovery.
- Never run `pnpm build` in `ai-chat-landing/` while `pnpm dev` is running.
- Live checks use throwaway conversations only — delete them afterwards.

---

## Phase 7: Convergence


Convergence pass (2026-10-26): the FR-005 cleanup removed the extra branch
nodes but left their template references behind in the shared answer nodes.

- [X] T019 Extend the patch cleanup in `src/agentic_rag_mcp/deploy/model_apply.py` to also strip the `{{#<node>.text#}}` template references of removed nodes from the `answer` and `ppt_answer` nodes (currently `AGI_Assistant.yml:529,591` still reference `agentic_strategy_kimi/glm/qwen38` and `ppt_master_kimi/glm/qwen38` — dangling refs that Dify currently tolerates), add pytest coverage in `tests/unit/test_deploy_model_apply.py`, then re-apply `deepseek/deepseek-v4.1-flash` to clean the live app and verify the templates concat only existing nodes per FR-005 (partial)
- [X] T020 Live-verify the spec-026 fallback badge variant (research D6): stop Ollama, select Local, send a message, and confirm the reply badges the globally configured cloud model with the persistent fallback note (the `<model-id>|fallback` write path has unit coverage in `ai-chat-landing/lib/models/badge.test.ts` but was never observed live) per FR-004/research D6 (partial)
