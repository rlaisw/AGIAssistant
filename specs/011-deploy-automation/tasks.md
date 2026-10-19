# Tasks: Deployment Automation — One-Command Stack Deploy & Verify

**Input**: Design documents from `/specs/011-deploy-automation/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/deploy-cli.md, quickstart.md

**Tests**: Included — user directive ("original tasks + add test cases and error handling") plus Constitution II. Test tasks precede implementation and must FAIL first. Matrix IDs (P01–P16) refer to `contracts/deploy-cli.md`.

**Organization**: user stories in priority order; US2 and US3 both depend on the console client but are otherwise independent.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1–US4 per spec.md
- Exact file paths in every task

---

## Phase 1: Setup (Shared Infrastructure)

- [x] T001 Create the package skeleton `src/agentic_rag_mcp/deploy/` with empty `__init__.py`, `__main__.py`, `config.py`, `docker_ops.py`, `dify_console.py`, `tool_sync.py`, `battery.py`, `report.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

### Tests first (must fail)

- [x] T002 [P] Write failing unit tests in `tests/unit/test_deploy_config.py` (P01–P02): config-file values, env overrides (`DIFY_CONSOLE_EMAIL`/`DIFY_CONSOLE_PASSWORD`/`DIFY_CONSOLE_URL`/`DIFY_API_KEY`), defaults (`console_url=http://localhost`, `sidecar_image=agentic-rag-mcp:latest`, `container=agentic-rag`, `db_container=docker-db_postgres-1`), and redaction masking every secret shape in formatted evidence
- [x] T003 [P] Write failing unit tests in `tests/unit/test_deploy_sync_payload.py` (P04–P05) with fixture `tests/fixtures/deploy/tools_list.json`: payload building produces the exact `{name, title, description, inputSchema}` list with count preserved; version gate selects `db-resync` for 1.17.x, `console-create` for registration, and an honest skipped-notice for unknown versions

### Implementation

- [x] T004 Implement `src/agentic_rag_mcp/deploy/config.py`: `[dify]`/`[deploy]` config resolution (env overrides file, defaults per contract), redaction helpers, and the exit-2 configuration-error path with one-line setup instructions
- [x] T005 Implement `src/agentic_rag_mcp/deploy/report.py`: Step/summary formatting with redaction applied to all evidence, failures-first summary output
- [x] T006 Implement `src/agentic_rag_mcp/deploy/__main__.py`: subcommand dispatch (`redeploy|chatflow|verify|all`, `--dry-run`, `--skip-chat`), exit codes (0 success · N failed scenarios · 2 config error), config echo (redacted) at start; dry-run prints the plan and touches nothing (P11)
- [x] T007 Contract-check the CLI in `tests/contract/test_deploy_cli.py` (P03, P11): missing console credentials → exit 2 before any mutation; `--dry-run` performs no docker/API side effects

**Checkpoint**: CLI skeleton green — config resolution, redaction, dispatch, exit semantics.

---

## Phase 3: User Story 1 — One-Command Stack Redeploy (Priority: P1) 🎯 MVP

**Goal**: `redeploy` builds + recreates the sidecar, ensures MCP registration, and re-syncs the tool cache with before/after counts.

**Independent Test**: run `redeploy` after a tool-count change; `tools/list` and Dify's cache match without any UI action (contract `redeploy` row).

### Tests for User Story 1 (write FIRST, must fail)

- [x] T008 [P] [US1] Write failing integration tests in `tests/integration/test_deploy_console.py` against a fake console HTTP server (stdlib `http.server`, conftest pattern) with fixture `tests/fixtures/deploy/`: login success → token captured (P06); login 401 → honest failure text; provider absent → create POST with documented name/URL (P07); provider present → no create, re-sync path selected (P08)

### Implementation for User Story 1

- [x] T009 [US1] Implement the console client login + provider operations in `src/agentic_rag_mcp/deploy/dify_console.py`: `POST /console/api/login`, `GET /workspaces/current/tool-provider/mcp` (provider list), `POST` create with the documented name/URL — never creating a duplicate when present
- [x] T010 [US1] Implement `src/agentic_rag_mcp/deploy/docker_ops.py`: image build from repo root, container recreate with the DEPLOY.md-documented mounts/networks/port/restart policy, bounded health-wait loop on `/healthz`, and Dify version detection from the api container (`DIFY_VERSION` env)
- [x] T011 [US1] Implement `src/agentic_rag_mcp/deploy/tool_sync.py`: fetch live `tools/list` from the sidecar MCP endpoint, build the cache payload, and apply the version-gated DB re-sync via `docker exec <db_container> psql` (the validated spec 009 workaround) with before/after counts; honest skipped-notice when the version gate or docker is unavailable
- [x] T012 [US1] Wire the `redeploy` subcommand in `src/agentic_rag_mcp/deploy/__main__.py` (steps per contract: build → recreate → health → register-or-sync) and validate live: dry-run, then a real run reporting before/after tool counts

**Checkpoint**: one command redeploys the stack and syncs tools, zero UI actions.

---

## Phase 4: User Story 2 — One-Command Dify Chatflow Update (Priority: P1)

**Goal**: `chatflow` updates the app in place (draft-update + publish) or imports it when absent.

**Independent Test**: run `chatflow` with a modified DSL; the published app answers with the new behavior and keeps its app id (contract `chatflow` row).

### Tests for User Story 2 (write FIRST, must fail)

- [x] T013 [P] [US2] Extend `tests/integration/test_deploy_console.py` (P09–P10): app with the DSL's name exists → workflow draft-update endpoint called (no import); app absent → import endpoint called; publish route hit in both paths

### Implementation for User Story 2

- [x] T014 [US2] Implement chatflow operations in `src/agentic_rag_mcp/deploy/dify_console.py`: app lookup by DSL name, workflow draft update (`POST /console/api/apps/<id>/workflows/draft` with the DSL's workflow section), DSL import (`POST /console/api/apps/imports`), and publish — update in place, never deleting other apps
- [x] T015 [US2] Wire the `chatflow` subcommand in `src/agentic_rag_mcp/deploy/__main__.py` and validate live against the running Dify: existing app draft-updated + published (app id unchanged)

**Checkpoint**: chatflow changes ship without any browser action.

---

## Phase 5: User Story 3 — One-Command Verification Battery (Priority: P1)

**Goal**: `verify` runs every headless scenario with pass/fail evidence, self-cleanup, and honest exit codes.

**Independent Test**: run `verify` on the deployed stack; all scenarios pass with evidence; exit 0 (contract battery table).

### Tests for User Story 3 (write FIRST, must fail)

- [x] T016 [P] [US3] Write failing contract tests in `tests/contract/test_deploy_cli.py` (P12–P15): the battery registry contains exactly the seven scenario ids from `contracts/deploy-cli.md`; exit code equals failed-scenario count; teardown removes `verify_<ts>` projects including pre-existing orphans (reported, not silent); `chat-journey` skipped honestly without an API key (notice, not failure)

### Implementation for User Story 3

- [x] T017 [US3] Implement the battery core in `src/agentic_rag_mcp/deploy/battery.py`: the scenario registry (health, tools-surface, deck-roundtrip, completion-page, honest-errors, chat-ui-liveness, chat-journey), the MCP call helper, unique `verify_<timestamp>` project naming, teardown + orphan sweep, per-scenario evidence, exit-code aggregation
- [x] T018 [US3] Implement the `chat-journey` scenario in `src/agentic_rag_mcp/deploy/battery.py`: service-API streaming prompt (`POST /v1/chat-messages`, `response_mode: streaming`) → parse the SSE answer → extract the deck link → verify the page serves and the file downloads; honest timeout with partial evidence
- [x] T019 [US3] Wire the `verify` subcommand with `--skip-chat` in `src/agentic_rag_mcp/deploy/__main__.py` and validate live: full battery green including chat-journey, exit 0

**Checkpoint**: the stack verifies itself headlessly.

---

## Phase 6: User Story 4 — Honest, Quiet Automation (Priority: P2)

**Goal**: every command is non-interactive, redacted, and idempotent.

**Independent Test**: run `all` twice on a healthy stack — zero prompts, identical outcomes, no duplicate registrations/imports (FR-007/FR-008).

- [x] T020 [US4] Polish pass across `src/agentic_rag_mcp/deploy/`: config echo redaction on every code path, skipped-with-notice formatting for version-gated steps, idempotency verification (second run makes no duplicate registrations, imports, or cache churn), and the umbrella `all` subcommand wiring (redeploy → chatflow → verify, aborting before the battery on step failure)

---

## Phase 7: Polish & Cross-Cutting Concerns

- [x] T021 [P] Update `DEPLOY.md` (automation section: credential setup + the four commands), `README.md` (one-command deploy/verify mention), and add the `[dify]`/`[deploy]` keys to the documented config reference
- [x] T022 Run the full pytest suite (existing 294 + new deploy tests — P16) and the quickstart end-to-end: `verify --dry-run`, `verify`, `all` on the live stack, plus one idempotent re-run

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: no dependencies
- **Phase 2 (Foundational)**: blocks all stories — config/report/CLI skeleton
- **US1 (Phase 3)**: depends on Foundational; delivers the MVP
- **US2 (Phase 4)**: depends on T009 (console client login); chatflow ops build on it
- **US3 (Phase 5)**: depends on T006 (CLI) for wiring; scenarios are self-contained against the running stack
- **US4 (Phase 6)**: cross-cutting polish over all commands
- **Polish (Phase 7)**: after all stories

### Within Each User Story

- Tests written first and failing (Constitution II)
- Console client before command wiring; battery core before the chat-journey scenario

### Parallel Opportunities

- T002 ∥ T003 (separate unit test files)
- T008 ∥ T013 ∥ T016 (test files, different phases' starts)
- T010 ∥ T009 (docker ops vs console client)
- With multiple workers: US2 (T013–T015) and US3 (T016–T019) proceed in parallel after T009/T006

---

## Implementation Strategy

### MVP First (User Story 1)

1. Setup + Foundational
2. US1: `redeploy` end-to-end (build → recreate → register/sync)
3. **STOP and VALIDATE**: contract `redeploy` row on the live stack
4. The operator's core loop is already automated

### Incremental Delivery

Foundation → US1 (redeploy) → US2 (chatflow) → US3 (battery) → US4 (quiet/idempotent polish) → full suite + live quickstart. Nothing breaks the existing 294-test suite at any point (P16 guards continuously).

---

## Notes

- Matrix IDs P01–P16 map to `specs/011-deploy-automation/contracts/deploy-cli.md`
- Credentials never enter the repo or logs — the redaction helper is mandatory in every evidence string (SC-005)
- The DB re-sync path is version-gated and honestly skipped, never silently version-coupled (FR-010)
- The chatflow update is draft-update-in-place (app id and API key preserved); import only when absent (R2)
