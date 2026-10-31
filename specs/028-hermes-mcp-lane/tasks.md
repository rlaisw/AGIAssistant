---
description: "Task list for Hermes Agent Lane (feature 028)"
---

# Tasks: Hermes Agent Lane — Windows File Tasks via Local Agent

**Input**: Design documents from `/specs/028-hermes-mcp-lane/`

**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/hermes-file-task.md ✓, quickstart.md ✓

**Tests**: Requested at plan time ("create test cases and add error handling") and mandated by Constitution II — unit suites failing-first; battery scenario + error matrix as live gates.

**Organization**: Grouped by user story (US1 P1 create-files, US2 P1 block-matrix, US3 P2 out-of-scope declines). Stories share the gate module, so the build is foundational-then-lanes.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story the task belongs to
- Exact file paths in every description

## Path Conventions

Sidecar Python at repo root: `src/agentic_rag_mcp/`, tests in `tests/unit/`, battery in `src/agentic_rag_mcp/deploy/battery.py`, DSL artifact `dify/AGIAssistant/AGI_Assistant.yml`.

---

## Phase 1: Setup

**Purpose**: Host-side Hermes API server + sidecar config — everything the lane depends on lives outside the repo tree.

- [x] T001 Configure the Hermes API server: write `~/.hermes/.env` with `API_SERVER_ENABLED=true`, `API_SERVER_KEY=<openssl rand -hex 32>`, `API_SERVER_HOST=172.17.0.1`, `API_SERVER_PORT=8642` (chmod 600), restart with `hermes gateway restart -y --detach`, and verify with `curl -H "Authorization: Bearer <key>" http://172.17.0.1:8642/v1/models` listing `hermes-agent` (research R1/R3)
- [x] T002 Verify the Windows target: `mkdir -p /mnt/c/temp` and confirm WSL write access (`touch /mnt/c/temp/.wsl-write-test && rm /mnt/c/temp/.wsl-write-test`); record the result in `specs/028-hermes-mcp-lane/quickstart.md` §Prerequisites
- [x] T003 Add config fields to `src/agentic_rag_mcp/config.py`: `hermes.api_url` (default `http://172.17.0.1:8642`), `hermes.api_key` (default empty — read from config.toml `[hermes]`), `hermes.timeout_s` (default 300), `hermes.allowed_root` (default `/mnt/c/temp`), `hermes.audit_path` (default `~/.hermes-mcp/audit.jsonl`); mirror the `[hermes]` section into `~/.config/agentic-rag-mcp/config.toml` with the real key (never committed)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The pure gate + client + audit writer — every lane consumes these. Tests-first (Constitution II).

**⚠️ CRITICAL**: No lane work begins until this phase is green.

- [x] T004 [P] Write the failing-first gate suite `tests/unit/test_hermes_gate.py` from quickstart §A: A1 normalization matrix (`C:\temp\x`, `c:/TEMP/x`, `/mnt/c/temp/x`, `~`, relative, `C:\temp\..\..\Windows`, mixed/trailing separators, case-insensitive drives), A2 containment (in-root ok; `D:\`, `/`, `C:\Windows`, traversal → blocked naming the active root), A3 op-set allowlist (create-dir/write-file/read-file/list-dir pass; delete/rename/move/bulk blocked with the v1 scope named — inside the root too), A4 no-location ask-back (no location assumed), A5 root override (arg narrows; config default when absent). Suite MUST fail (module absent)
- [x] T005 [P] Write the failing-first audit suite `tests/unit/test_hermes_audit.py` from quickstart §A6: one JSONL entry per attempt; executed entries carry `outcome`, blocked carry `reason`; entries never rewritten or pruned; file created on first write. Suite MUST fail
- [x] T006 Implement `src/agentic_rag_mcp/hermes_gate.py` until T004 is green: pure functions — `normalize_path(token)` (drive map `C:\…`→`/mnt/c/…`, `~`/`$HOME` expansion, relative anchoring, separator/case normalization, `..` resolution), `extract_paths(task)` , `gate_task(task, allowed_root)` → SafetyVerdict per data-model §3 (decision/operation/reason/normalized_path), op-set allowlist per contracts §2.4, no-location ask-back per FR-014
- [x] T007 Implement `src/agentic_rag_mcp/hermes_audit.py` until T005 is green: append-only JSONL writer per data-model §4 (ts, decision, reason, operation, normalized_path, allowed_root, outcome); atomic append; never prunes
- [x] T008 [P] Implement `src/agentic_rag_mcp/hermes_client.py`: thin stateless client — `POST {api_url}/v1/responses`, Bearer key, body `{input, instructions: <containment prompt>, store: false, model: "hermes-agent"}`, `httpx` timeout `hermes.timeout_s` (research R1/R4); map non-200/timeout/connection failures to honest error envelopes (never fabricate); expose no session state
- [x] T009 Wire the MCP tool `hermes_file_task(task, allowed_root?)` in `src/agentic_rag_mcp/server.py` per contracts §1–§4: gate → audit entry → (blocked: honest envelope with reason + active root; ok: Hermes call, relay result, audit `executed` with outcome; error: honest envelope + recovery hint, audit `blocked` with `error:<reason>`). Docstring = the DSL-synced tool_description (per the established pipeline)

**Checkpoint**: `pytest tests/unit/test_hermes_gate.py tests/unit/test_hermes_audit.py` green; the tool is callable directly against the sidecar.

---

## Phase 3: User Story 1 — Create files on the Windows disk from chat (Priority: P1) 🎯 MVP

**Goal**: A prompt like "create hello_test in C:\temp and write hello.txt with 'Hello World'" produces the real artifact, verifiable in Windows Explorer, answer names the Windows-style path (SC-001).

**Independent Test**: quickstart §B1/§B5 via the battery — file exists with content, < 60 s, audit shows `executed`.

### Tests for User Story 1

- [x] T010 [P] [US1] Add the `hermes-file-task` battery scenario to `src/agentic_rag_mcp/deploy/battery.py` (B1 create in a timestamped test root under the configured allowed root; B5 assert < 60 s; assert file content; assert audit `executed` entry; honest envelope shape) and register it in the scenario list after `chat-journey`

### Implementation for User Story 1

- [x] T011 [US1] Add the `hermes_file_task` tool to the DSL artifact `dify/AGIAssistant/AGI_Assistant.yml`: MCP tool entry (provider `agentic-rag`, tool_name `hermes_file_task`) with the tool_description synced from the server docstring (established pattern — all copies updated)
- [x] T012 [US1] Add the third intent class to `intent_router` in `dify/AGIAssistant/AGI_Assistant.yml` ("file task / Hermes" with examples: create/list/write on my computer, in C:\temp, on my Windows disk) and add the **Hermes Agent** node (function-calling strategy, existing cloud model, tools = `[hermes_file_task]`) wired router→hermes→answer merge per contracts §5; instructions state the lane scope + honest-relay rule
- [x] T013 [US1] Republish via `.venv/bin/python -m agentic_rag_mcp.deploy chatflow`, hot-patch the running sidecar (`docker cp` the new `hermes_gate.py`/`hermes_client.py`/`hermes_audit.py`/`server.py`/`config.py` + restart container), and run T010 live: file appears in `C:\temp`, answer names `C:\temp\…` (FR-008)

**Checkpoint**: MVP — chat creates real files on the Windows disk, end-to-end.

---

## Phase 4: User Story 2 — Out-of-bounds prompts blocked, never executed (Priority: P1)

**Goal**: The block matrix (other drives, system dirs, traversal, smuggled instructions) is refused with a reason; nothing changes on disk; audit records every block (SC-002/SC-005).

**Independent Test**: quickstart §B2–B4 via the battery + unit A2/A3 already green.

### Tests for User Story 2

- [x] T014 [P] [US2] Extend the battery scenario in `src/agentic_rag_mcp/deploy/battery.py` with B2 (live "delete everything in C:\Windows" → blocked envelope, nothing changed, audit `blocked`) and B3 (delete-in-root → declined with v1 scope, file still present) and B4 (audit cross-check: exactly the expected entries in order — SC-005)

### Implementation for User Story 2

- [x] T015 [US2] Harden the Hermes Agent node instructions in `dify/AGIAssistant/AGI_Assistant.yml`: relay the tool's verdict verbatim (blocked reasons, ask-backs); never claim direct disk access; never re-attempt a blocked operation with rephrased paths (anti-smuggling, FR-009); republish via `deploy chatflow`
- [x] T016 [US2] Run the extended battery live (D1 variant: stop the Hermes gateway, send B1 → honest error envelope + recovery hint per FR-010; restart gateway) and record the D-matrix outcomes in `specs/028-hermes-mcp-lane/quickstart.md` §D

**Checkpoint**: The security story is complete and evidence-backed.

---

## Phase 5: User Story 3 — Windows program execution is out of scope (Priority: P2)

**Goal**: notepad/PowerShell/GUI prompts get a clear decline naming the file-only scope; no Windows process is ever started (FR-009, SC via §C regression).

**Independent Test**: quickstart §D4-style probes + C1–C3 regression battery green.

### Tests for User Story 3

- [x] T017 [P] [US3] Add decline-probe cases to the battery scenario in `src/agentic_rag_mcp/deploy/battery.py` ("open notepad", "run a PowerShell command that lists processes") → expect a decline naming the v1 file-only scope; assert no new process evidence (audit shows blocked/unsupported verdicts only)

### Implementation for User Story 3

- [x] T018 [US3] Extend the Hermes Agent node instructions in `dify/AGIAssistant/AGI_Assistant.yml` with the explicit file-only scope rule and decline template; republish via `deploy chatflow`; run the full battery (12 scenarios — C3: chat-journey, antv-chart, stop-generation unchanged, SC-004)

**Checkpoint**: All three stories functional; battery 12/12.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [x] T019 [P] Docs sync: root `AGENTS.md` feature-surface line + `README.md` (new lane), `DEPLOY.md` (Hermes API server prerequisites row + troubleshooting: Hermes down, key rejected, 172.17.0.1 unreachable), deploy skill mirrors
- [x] T020 Full green sweep: `pytest tests/unit -q` (gate/audit suites + existing 218+), `pnpm typecheck && pnpm lint && pnpm test` in `ai-chat-landing/` (untouched — must stay green), full battery live; update `specs/028-hermes-mcp-lane/quickstart.md` with the recorded D-matrix results
- [x] T021 [P] Commit: source + DSL + battery + spec artifacts; leave the audit log and `~/.hermes/.env` out (user data, never committed); note the pending sidecar image rebuild in the commit message (docker cp hot-patch caveat)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1**: immediate; T003 blocks Phase 2 (config fields)
- **Phase 2**: blocks ALL lane work (gate/client/audit/tool are the shared foundation); T006/T007 after T004/T005 (tests fail first); T008 parallel; T009 last in phase
- **Phases 3–5**: sequential recommended (each republishes the DSL — avoid concurrent YAML edits); within a phase, battery-test tasks [P] run alongside DSL work
- **Phase 6**: last

### User Story Dependencies

- US1 (P1): after Phase 2 — no story deps. **MVP = Phases 1–3.**
- US2 (P1): builds on US1's battery scenario + node (T014 extends T010's scenario; T015 hardens T012's instructions)
- US3 (P2): builds on US1/US2's node + battery (T017 extends the same scenario)

### Within Each User Story

- Battery-test task before the DSL edit (assert the current gap), DSL + republish + hot-patch, live run, then next story.

### Parallel Opportunities

- Phase 2: T004 ∥ T005 ∥ T008 (different files)
- Phase 3: T010 (battery file) ∥ T011/T012 (DSL — single file, sequential pair)
- Phase 4: T014 ∥ T015 prep; Phase 5: T017 ∥ T018 prep
- Phase 6: T019 ∥ T020 prep

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Phase 1 (host setup + config) → 2. Phase 2 (gate green, tool live on sidecar) → 3. Phase 3 (DSL lane + battery B1) → 4. **STOP and VALIDATE**: file in `C:\temp` + audit entry — chat-driven Windows file creation works.

### Incremental Delivery

1. MVP (US1) → 2. US2 security battery → 3. US3 scope declines → 4. Polish/docs/commit. Each story keeps the previous green (battery re-run per phase).

---

## Notes

- [P] = different files, no dependencies on incomplete tasks
- The DSL (T011/T012/T015/T018) is a single YAML file — never two DSL tasks in flight together
- Sidecar changes reach the running container via `docker cp` (AGENTS.md); the image rebuild stays pending — note it in the commit
- The Hermes key lives in `~/.hermes/.env` and `~/.config/agentic-rag-mcp/config.toml` only — never in the DSL, answers, or repo
- Battery scenario must not depend on spec-026 model state — the lane works for any configured model
- Commit after each phase or logical group

---

## Phase 7: Convergence

- [x] T022 Persist the Hermes audit log outside the container's ephemeral layer per FR-012 (partial): point `hermes.audit_path` in `src/agentic_rag_mcp/config.py` (and `~/.config/agentic-rag-mcp/config.toml`) at a volume-backed path (the mounted `/root/.config/agentic-rag-mcp/` tree or a new `~/.hermes-mcp` bind in the sidecar's compose volume set), update the audit-read path in `src/agentic_rag_mcp/deploy/battery.py` scenario B4, hot-patch + restart the sidecar, and live-verify one pre-existing audit entry survives a container restart (the pending image rebuild must not destroy the trail)
