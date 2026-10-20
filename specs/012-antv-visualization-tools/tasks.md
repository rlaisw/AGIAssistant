# Tasks: AntV Visualization Tools on the Sidecar

**Input**: Design documents from `/specs/012-antv-visualization-tools/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/antv-tools.md, quickstart.md

**Tests**: Included — user directive ("original plan + create test cases + add error handling") plus Constitution II. Test tasks precede implementation and must FAIL first. Matrix IDs (A01–A18) refer to `contracts/antv-tools.md`.

**Organization**: user stories in priority order; US1 and US2 share the chart tool but ship independently (US2's bridge change builds on US1's tool). US3 is fully parallel.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1–US4 per spec.md
- Exact file paths in every task

---

## Phase 1: Setup (Shared Infrastructure)

- [x] T001 Create `src/agentic_rag_mcp/antv/` package skeleton (`__init__.py`, empty `errors.py`, `charts.py`, `infographic.py`) and `tests/fixtures/antv/` with a small valid chart payload (`chart_payload.json`) and infographic syntax (`infographic.txt`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

### Tests first (must fail)

- [x] T002 [P] Write failing unit tests in `tests/unit/test_antv_tools.py` (A02–A05, A08, A10–A11): unsupported chart_type → `ANTV_INVALID_TYPE` naming the supported set (including a geo type); empty/oversized/malformed data → `ANTV_INVALID_INPUT`; service `success=false` → `ANTV_SERVICE_ERROR` with verbatim message; timeout → `ANTV_SERVICE_TIMEOUT`; infographic empty/oversized syntax → `ANTV_INVALID_INPUT`; write_page inlining (fake fetch → `data:image/…` and no `https://` hrefs remain; fetch failure/oversize → `PPT_INVALID_INPUT` naming the href)
- [x] T003 [P] Write failing contract tests in `tests/contract/test_antv_contract.py` (A01, A07–A09, A11, A13–A14, A15): fake HTTP service per the conftest pattern — valid chart call returns `{chart_type, image_url, usage}`; infographic call returns a url whose route serves `text/html` containing the syntax + engine reference; route 404/400 semantics; `tools/list` grows 21 → 23 with existing entries unchanged; every error code → envelope shape with non-empty hint; existing ppt/completion/deploy suites re-run green

### Implementation

- [x] T004 Implement `src/agentic_rag_mcp/antv/errors.py`: `AntvError` hierarchy (`AntvInvalidType`, `AntvInvalidInput`, `AntvServiceError`, `AntvServiceTimeout`) mapping to the uniform `{"error": {code, message, hint}}` envelope with agent-actionable hints (R7)
- [x] T005 Add the `[antv]` config section to `src/agentic_rag_mcp/config.py`: `chart_service_url` (default `https://antv-studio.alipay.com/api/gpt-vis`), `chart_timeout_s` (30), `max_inline_image_bytes` (2097152), `infographic_max_syntax_bytes` (65536) — env-overridable per the existing pattern (R6)

**Checkpoint**: error taxonomy + config green — story work can begin.

---

## Phase 3: User Story 1 — Charts in Chat Answers (Priority: P1) 🎯 MVP

**Goal**: `antv_chart(chart_type, data, title)` returns a hosted image URL the agent embeds in markdown answers.

**Independent Test**: direct MCP call → `{chart_type, image_url, usage}`; the image URL serves unauthenticated (contract `antv_chart` row).

### Implementation for User Story 1

- [x] T006 [US1] Implement `src/agentic_rag_mcp/antv/charts.py`: the curated supported-type list (geo types excluded), input validation (data non-empty, serialized ≤ 64 KB, title ≤ 200 chars), POST to the configured rendering service with `chart_timeout_s`, response mapping (`success` → `{chart_type, image_url, usage}`; `success=false`/non-200 → verbatim `ANTV_SERVICE_ERROR`; timeout → `ANTV_SERVICE_TIMEOUT`) (R1–R2, A01–A05)
- [x] T007 [US1] Register `antv_chart` in `src/agentic_rag_mcp/server.py` with the chart-selection guidance distilled into the docstring (intent → type table per R5); PptError-style envelope handling reused for Antv errors
- [x] T008 [P] [US1] Write the live integration test in `tests/integration/test_antv_pipeline.py` (A06, network-gated skipif): one real chart call returns an image URL that serves with an image content-type

**Checkpoint**: charts work end-to-end from MCP.

---

## Phase 4: User Story 2 — Charts in PowerPoint Decks (Priority: P1)

**Goal**: deck pages embed charts; exported decks are self-contained (Clarification Option A).

**Independent Test**: write a page with a remote `<image href>` → the persisted SVG contains only `data:` URIs; export embeds the bytes (A10, A12).

### Implementation for User Story 2

- [x] T009 [US2] Extend `write_page` in `src/agentic_rag_mcp/ppt/bridge.py` with remote-image inlining: after sanitization, fetch every `<image href="https://…">` (capped by `max_inline_image_bytes`), re-embed as `data:` URIs; fetch failure or oversize → `PPT_INVALID_INPUT` naming the href, page not persisted (R4, self-containment)
- [x] T010 [US2] Extend `tests/integration/test_antv_pipeline.py` with the deck self-containment test (A12): a page with a remote chart image exports and the `.pptx` zip contains the image bytes in `ppt/media/` with no hotlink in the slide XML
- [x] T011 [US2] Add the "Charts in decks" section to `dify/ppt-master-rulebook.md` (when to chart, sizing within page zones, embedding via image reference — noting write-time inlining) and regenerate `dify/Chatflow Basic (AgenticRAG Agent + PPT-Master).yml` with both `antv_*` tools added to the PPT-Master and Agentic Strategy node tool lists (R5)

**Checkpoint**: decks with charts export self-contained; DSL ready to republish.

---

## Phase 5: User Story 3 — Infographics (Priority: P2)

**Goal**: `antv_infographic(description)` returns a sidecar URL that renders the infographic in a browser.

**Independent Test**: tool call → url; `GET /infographics/<id>/` serves HTML containing the stored syntax + the CDN engine reference (A07).

### Implementation for User Story 3

- [x] T012 [P] [US3] Implement `src/agentic_rag_mcp/antv/infographic.py`: syntax validation (non-empty, ≤ `infographic_max_syntax_bytes`), unique URL-safe id, store the syntax under the served directory, render the small HTML page (engine UMD from CDN + the stored syntax, in-page honest error surface for CDN unavailability), return `{url, usage}` (R3)
- [x] T013 [P] [US3] Add the `GET /infographics/{id}/` route to `dify/docker/mcp-server/server.py` (200 `text/html`; 404 unknown id; 400 malformed id — reuse the id-validation pattern)
- [x] T014 [US3] Register `antv_infographic` in `src/agentic_rag_mcp/server.py` with infographic-syntax guidance distilled in the docstring (R5)

**Checkpoint**: infographics work end-to-end.

---

## Phase 6: User Story 4 — Honest Degradation and Data Posture (Priority: P2)

**Goal**: honest refusals and transparent data handling, battery-proven.

**Independent Test**: quickstart S4/S5 (unsupported type refused; service-down honesty) + the FR-009 doc section exists.

- [x] T015 [US4] Add the battery scenarios to `src/agentic_rag_mcp/deploy/battery.py` (A16–A18): `antv-chart` (tool call → image URL serves), `antv-infographic` (route serves rendered HTML), `chart-in-deck` (exported deck contains chart bytes) — each with honest failure reporting and `antv_`-prefixed unique project names for cleanup
- [x] T016 [P] [US4] Add the data-posture section to `DEPLOY.md` (FR-009: default public rendering service, data egress, private GPT-Vis-SSR alternative via `[antv] chart_service_url`, geo exclusion) and the `/infographics/` route to `docs/NETWORK.md`

---

## Phase 7: Polish & Cross-Cutting Concerns

- [x] T017 Rebuild and redeploy the sidecar, run `…deploy chatflow` (republish with antv tools on both nodes), then the full validation: complete pytest suite green (existing + antv), `…deploy verify` battery green including the three new scenarios, and quickstart S1–S6 spot-checked in the Chat UI

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: no dependencies
- **Phase 2 (Foundational)**: errors + config + failing tests — blocks all stories
- **US1 (Phase 3)**: depends on Phase 2 — delivers the chart tool (MVP)
- **US2 (Phase 4)**: depends on T006 (chart tool) for the chart image flow; the bridge inlining (T009) is independent of US1's internals
- **US3 (Phase 5)**: fully independent of US1/US2 after Phase 2 — can run in parallel from the start
- **US4 (Phase 6)**: battery scenarios need US1–US3 tool bodies; docs task (T016) is parallel
- **Polish (Phase 7)**: after all stories

### Within Each User Story

- Tests written first and failing (Constitution II)
- Tool bodies before server registration; bridge change before its integration test

### Parallel Opportunities

- T002 ∥ T003 (separate test files)
- T004 ∥ T005 (errors vs config)
- T008 ∥ T012 ∥ T013 (live test, infographic module, route — different files)
- US3 (T012–T014) runs fully parallel to US1/US2 after Phase 2
- T016 parallel to any story work

---

## Implementation Strategy

### MVP First (User Story 1)

1. Setup + Foundational
2. US1: `antv_chart` end-to-end (MCP call → image URL serves)
3. **STOP and VALIDATE**: contract `antv_chart` row via direct MCP
4. Charts in chat answers work — deployable

### Incremental Delivery

Foundation → US1 (chart tool) → US2 (self-contained decks + DSL) → US3 (infographics, parallel) → US4 (battery + posture docs) → full redeploy + verify. Nothing breaks existing suites at any point (A15 guards continuously).

---

## Notes

- Matrix IDs A01–A18 map to `specs/012-antv-visualization-tools/contracts/antv-tools.md`
- The self-containment rule (Clarification 2026-10-20, Option A) is implemented at write time (T009) — deterministic regardless of ppt-master exporter internals
- The chart service is external by default — live integration tests and the chart battery scenarios require outbound internet and are network-gated honestly
- The infographic rendering is browser-side (CDN engine) — no server-side DOM, no puppeteer (Constitution III)
- DSL regeneration (T011) requires republishing via `…deploy chatflow` — noted in the Phase 7 validation
