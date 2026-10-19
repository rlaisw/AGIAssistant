# Tasks: PPT-Master MCP Tools

**Input**: Design documents from `/specs/009-ppt-master-mcp-tools/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/ppt-tools.md, quickstart.md

**Tests**: Included — user directive in the plan ("create test cases and add error handling") plus Constitution II (tests-first). Test tasks precede implementation tasks in every phase and must FAIL before the implementation lands.

**Organization**: Tasks grouped by user story. Executable order is dependency-driven: US2 (tool surface) → US3 (delivery route) → US1 (chatflow journey) → US4 (honest-failure behaviors). US1 and US2 are both P1 in the spec; US2 is built first because US1's journey drives US2's tools.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1–US4 per spec.md
- Exact file paths in every task

---

## Phase 1: Setup (Shared Infrastructure)

- [x] T001 Add `[ppt]` config section to `src/agentic_rag_mcp/config.py`: `scripts_root` (default `/opt/ppt-master/skills/ppt-master`), `projects_root` (default `/opt/ppt-master/projects`), `exports_url_base` (default `http://localhost:28080/exports`), `max_pages` (default `5`), `script_timeout_s` (default `120`), `retention_days` (default `0` = keep forever) — per research.md R8; extend the config loader and its existing unit tests

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T002 [P] Write failing unit tests in `tests/unit/test_ppt_bridge.py`: error envelope shape for all 8 codes (`code`+`message`+`hint`, non-empty message — matrix T23), subprocess non-zero exit → `PPT_SCRIPT_FAILED` with verbatim truncated stderr ≤2000 chars (T24), timeout → `PPT_SCRIPT_TIMEOUT` (T16), unwritable projects root → `PPT_WORKSPACE_ERROR` (T03)
- [x] T003 [P] Create `src/agentic_rag_mcp/ppt/errors.py`: `PptError` hierarchy (`InvalidProject`, `InvalidInput`, `MissingIcon`, `ScriptTimeout`, `ScriptFailure`, `CheckFailed`, `ExportBlocked`, `WorkspaceError`) mapping to the shared envelope `{"error": {"code", "message", "hint"}}` exactly per `contracts/ppt-tools.md` (R6)
- [x] T004 Create `src/agentic_rag_mcp/ppt/bridge.py` (with `__init__.py`): subprocess runner — command assembly from `[ppt]` config paths, `script_timeout_s` enforcement, stdout/stderr capture, exit-code/stderr → `PptError` mapping (R1/R6); no Dify or MCP imports (pure bridge)

**Checkpoint**: Foundation ready — runner and error envelope are unit-green.

---

## Phase 3: User Story 2 — Granular Tools for the Agent (Priority: P1)

**Goal**: Five additive MCP tools (`ppt_project_init`, `ppt_icon_sync`, `ppt_write_page`, `ppt_check`, `ppt_export`) callable directly, with the full error contract.

**Independent Test**: Direct MCP calls init → icon sync → write page → check → export produce a passing one-page deck with zero manual steps (quickstart.md §2 battery).

### Tests for User Story 2 (write FIRST, must fail)

- [x] T005 [P] [US2] Write failing contract tests in `tests/contract/test_ppt_contract.py`: all five tool schemas per `contracts/ppt-tools.md`; envelope on every error code (T06, T15, T19, T23); `tools/list` grows 16 → 21 with existing entries schema-identical (T22 — Constitution I)
- [x] T006 [P] [US2] Write failing integration tests in `tests/integration/test_ppt_pipeline.py` with fixtures `tests/fixtures/ppt/passing.svg` + `tests/fixtures/ppt/failing.svg` (known text overflow): init creates workspace with id `<slug>_<YYYYMMDD>_<rand4>` (T01), icon missing report (T05), valid write persists `<NN>_<name>.svg` (T07), check parses passing/failing (T13/T14), export produces a real `.pptx` with native text frames via python-pptx (T17), export refused on failing pages (T18), revision re-export yields new artifact with old link alive (T20), concurrent inits disjoint (T21)

### Implementation for User Story 2

- [x] T007 [US2] Implement `ppt_project_init` in `src/agentic_rag_mcp/ppt/bridge.py` + `@mcp.tool` registration in `src/agentic_rag_mcp/server.py`: name validation (1–64 chars, url-safe — T02), unique project id per data-model.md, workspace path + `max_pages` returned
- [x] T008 [US2] Implement `ppt_icon_sync`: batch `icon_sync.py` invocation, per-icon missing list with library search hint in `hint` (T05), `PPT_INVALID_PROJECT` on unknown id (T06)
- [x] T009 [US2] Implement `ppt_write_page`: page bound `1..max_pages` (T09), name sanitization + path-traversal rejection (T12), SVG sanitization — well-formed XML, root viewBox match, forbidden constructs (`<script>`, event attributes, `<foreignObject>`, `<style>`, `class`, external references), 256 KB cap (T08/T10/T11)
- [x] T010 [US2] Implement `ppt_check`: `svg_quality_checker.py --json` invocation parsed to `{passing, blocking_errors, warnings, details}` with verbatim fixable issue text (T13/T14), timeout mapping (T16)
- [x] T011 [US2] Implement `ppt_export`: refuse with `PPT_EXPORT_BLOCKED` + blocking summary unless all pages pass (T18); `svg_to_pptx.py` invocation; artifact + absolute URL per contracts (T19)
- [x] T012 [US2] Update `dify/docker/mcp-server/Dockerfile`: bake ppt-master runtime deps (per `ppt-master/requirements.txt`: python-pptx, PyMuPDF, Pillow, PyYAML, edge-tts, flask, lxml, requests, beautifulsoup4) into the sidecar image

**Checkpoint**: The five tools pass the contract + integration batteries; sidecar image builds.

---

## Phase 4: User Story 3 — Download Delivery (Priority: P2)

**Goal**: Generated `.pptx` files are downloadable via a link in the chat answer.

**Independent Test**: `GET /exports/<project>/<file>.pptx` returns the file; old links keep resolving (quickstart.md S2).

### Tests for User Story 3 (write FIRST, must fail)

- [x] T013 [P] [US3] Write failing contract tests in `tests/contract/test_ppt_contract.py` for the exports route: 200 with pptx content-type on valid file, honest 404 on missing, 400 on traversal (T25)

### Implementation for User Story 3

- [x] T014 [US3] Implement the static `/exports/<project_id>/<filename>` route in `dify/docker/mcp-server/server.py`, rooted at `projects_root`, traversal-safe, content-type `application/vnd.openxmlformats-officedocument.presentationml.presentation` (research.md R2)
- [x] T015 [US3] Confirm retention default `retention_days=0` keeps exports on disk (no GC in v1) and the re-export flow leaves prior artifacts resolvable (quickstart.md S2)

**Checkpoint**: A deck generated via direct MCP tool calls is downloadable through its returned URL.

---

## Phase 5: User Story 1 — Prompt-to-Deck Generation (Priority: P1) 🎯 completes the MVP

**Goal**: A user types "help to generate a powerpoint, introduce Dify software" and receives a clickable download link to a native editable deck.

**Independent Test**: quickstart.md S1 — full prompt in the Chat UI produces a working link; file opens in PowerPoint as editable text.

### Implementation for User Story 1

- [x] T016 [P] [US1] Create `dify/ppt-master-rulebook.md`: distilled quick-generate instructions (research.md R4) — tool-call protocol (init → icons → write per page → check → fix loop → export), SVG contract subset (1280×720 viewBox, grouped `data-pptx-bounds` zones, positioned line-break tspans, forbidden constructs), ≤5 pages per run, deck language follows prompt language, paste/research input modes
- [x] T017 [US1] Update `dify/Chatflow Basic (AgenticRAG Agent).yml` to v2: add the intent-classifier router (deck requests → PPT-Master, everything else → existing AgenticRAG agent unchanged — FR-014) and the PPT-Master agent node (Function Calling, max_iterations ≥ 30, tools = five `ppt_*` + existing web research tools, instructions = rulebook snapshot)
- [x] T018 [US1] Deploy-side wiring per `specs/009-ppt-master-mcp-tools/quickstart.md` §1–§4: rebuild sidecar with the ppt-master mount, refresh Dify's MCP tool cache, import chatflow v2, then run scenario S1 end-to-end

**Checkpoint**: MVP complete — prompt-to-download works in one conversational turn.

---

## Phase 6: User Story 4 — Honest Status and Failure (Priority: P3)

**Goal**: Progress is narrated; failures are honest; out-of-scope requests are declined truthfully.

**Independent Test**: quickstart.md S3–S6 — edge prompts produce honest answers, no fabricated links.

### Implementation for User Story 4

- [x] T019 [US4] Extend `dify/ppt-master-rulebook.md` with the failure protocol: narrate progress between tool calls, report the failing page + reason after repair attempts without delivering a broken file (FR/SC-004), decline unsupported requests (animated video) with what is possible instead, report partial state with a resume-or-smaller-deck offer when the iteration budget runs out, refuse cross-conversation edits with a regeneration offer (edge cases in spec.md)
- [x] T020 [US4] Re-import the updated chatflow and validate scenarios S3–S6 from `specs/009-ppt-master-mcp-tools/quickstart.md` (old-conversation edit, 10-page bound, file attachment, export-blocked probe)

**Checkpoint**: All honest-failure behaviors verified.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [x] T021 [P] Update `DEPLOY.md` (sidecar rebuild + ppt-master mount + /exports), `docs/NETWORK.md` (exports route), and `README.md` (feature mention) for the new tools
- [x] T022 Run the full pytest suite (`pytest`) — existing 228 tests plus all new files green — and the complete quickstart.md validation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: no dependencies
- **Phase 2 (Foundational)**: depends on T001 — BLOCKS all user stories
- **Phase 3 (US2)**: depends on Phase 2 — the tool surface everything else drives
- **Phase 4 (US3)**: depends on T011 (export tool produces the URL the route serves)
- **Phase 5 (US1)**: depends on Phases 3–4 (tools + route exist before the journey is tested)
- **Phase 6 (US4)**: depends on Phase 5 (rulebook and chatflow exist to extend)
- **Phase 7 (Polish)**: after all stories

### User Story Dependencies

- **US2 (P1)**: after Foundational — no story dependencies
- **US3 (P2)**: needs US2's `ppt_export` URL contract only
- **US1 (P1)**: integrates US2 tools + US3 route + chatflow; independently testable via quickstart S1
- **US4 (P3)**: extends US1's rulebook; independently testable via quickstart S3–S6

### Within Each User Story

- Tests written first and failing (Constitution II)
- Bridge functions before `@mcp.tool` registrations
- Tool implementations (T007–T011) are separate tasks but share `bridge.py` — implement sequentially

### Parallel Opportunities

- T002 ∥ T003 (different files: test vs errors)
- T005 ∥ T006 (separate test files + fixtures)
- T013 ∥ T016 (contract test vs rulebook authoring)
- T021 ∥ any validation task touching different files
- With multiple workers: US3 (T013–T015) and US1's rulebook (T016) can proceed while US2 implementation finishes

---

## Implementation Strategy

### MVP First (through User Story 1)

1. Complete Phase 1 + Phase 2 (foundation)
2. Complete Phase 3 (US2 — the five tools)
3. Complete Phase 4 (US3 — the download route)
4. Complete Phase 5 (US1 — chatflow journey)
5. **STOP and VALIDATE**: quickstart S1 prompt→link→native deck
6. Deploy/demo ready

### Incremental Delivery

Each phase lands a verifiable increment: subprocess bridge → directly-callable tools → downloadable artifacts → the full chat journey → honest-failure polish. Nothing breaks existing behavior at any point (Constitution I verified continuously by T005/T22).

---

## Notes

- Test tasks reference the matrix IDs (T01–T25) defined in `specs/009-ppt-master-mcp-tools/contracts/ppt-tools.md`
- ppt-master itself is a mounted external clone — never edit its scripts; the bridge wraps them (research.md R1)
- Commit after each task or logical group; the `.env.local` rule (never commit secrets) still applies

---

## Phase 8: Convergence

- [x] T023 Import and publish chatflow v2 (dify/Chatflow Basic (AgenticRAG Agent + PPT-Master).yml) in the Dify UI, refresh the MCP tool cache (Tools → MCP → server → Update), and run quickstart scenario S1 ("help to generate a powerpoint, introduce Dify software") to verify the prompt-to-download journey end-to-end per FR-009, FR-014, SC-001, SC-005, US1/AC1 (partial)
- [x] T024 Validate honest-failure scenarios S3–S6 from specs/009-ppt-master-mcp-tools/quickstart.md against the published chatflow (cross-conversation edit refusal, 10-page bound offer, file-attachment alternative, export-blocked probe) per US4/AC1–2 (partial)
- [x] T025 During S1 validation, confirm researched decks carry a sources footnote; if generated decks lack citations, strengthen dify/ppt-master-rulebook.md's provenance instruction and re-run S1 per FR-013 (partial)
- [x] T026 Document the [ppt] config surface in DEPLOY.md Step 9: the optional `python` interpreter field (host-side ppt-master venv vs container default) and the derived projects-root behavior (projects always at <ppt-master>/projects, matching [ppt] defaults) per plan R8 (partial)
- [x] T027 Add the PPT-Master feature mention to README.md: five ppt_* MCP tools (16 → 21), chatflow v2 router, /exports download route, pointer to DEPLOY.md Step 9 per T021 (partial)
