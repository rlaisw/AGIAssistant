# Tasks: PPT Completion Experience — Preview & Edit

**Input**: Design documents from `/specs/010-ppt-preview-edit/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/completion-page.md, quickstart.md

**Tests**: Included — plan directive ("create test cases and add error handling") plus Constitution II. Test tasks precede implementation and must FAIL first. Matrix IDs (D01–D18) refer to `contracts/completion-page.md`.

**Organization**: User stories in priority order; US4's pure-helper tasks are independent of the server work and can proceed in parallel with US1–US3.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1–US4 per spec.md
- Exact file paths in every task

---

## Phase 1: Setup (Shared Infrastructure)

- [x] T001 Add `vitest` as a dev dependency in `ai-chat-landing/package.json` with a `test` script and `ai-chat-landing/vitest.config.ts` (node environment, include `lib/**/*.test.ts`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T002 [P] Write failing unit tests in `tests/unit/test_ppt_completion.py`: snapshot logic (ordered slide copies into `<project>/previews/<stem>/`, write-once behavior, degraded marker `.degraded`), and completion-page HTML must contain the download href, slide count, and degraded states (matrix D02/D05/D06 shapes)
- [x] T003 Create `src/agentic_rag_mcp/ppt/completion.py`: `snapshot_previews(cfg, project_id, stem)` — invoke the pipeline's finalize step, copy the per-slide self-contained renderings into `previews/<stem>/` (numeric order, write-once), on failure write the `.degraded` marker and never raise (R1/R4); `render_completion_page(cfg, project_id, stem)` — HTML with slide previews or honest unavailable states, download control (frozen `/exports/` URL), edit-path pointer; `resolve_slide(project_id, stem, filename)` — traversal-safe slide path resolution

**Checkpoint**: snapshot + rendering logic unit-green.

---

## Phase 3: User Story 1 — One-Link Completion Experience (Priority: P1) 🎯 MVP

**Goal**: every export gets an immutable completion page at `GET /decks/<project>/<stem>/` with a download control; `ppt_export` returns the additive `page_url`.

**Independent Test**: quickstart S1 + S4 — export via MCP, open `page_url` (slides + download + edit path), unknown stem gives an honest 404.

### Tests for User Story 1 (write FIRST, must fail)

- [x] T004 [P] [US1] Write failing contract tests in `tests/contract/test_ppt_completion_contract.py` (fake scripts): `/decks/<p>/<stem>/` returns 200 HTML containing download href + edit pointer; slide asset 200 with `image/svg+xml`; honest 404 for unknown project/stem; 400/404 for traversal (`..%2F`, absolute paths); malformed ids rejected; `ppt_export` result has byte-identical `file`+`url` plus `page_url`; missing-project error envelope unchanged (D01, D07–D12)
- [x] T005 [P] [US1] Write failing integration tests in `tests/integration/test_ppt_completion_pipeline.py` (real toolchain, fixtures `tests/fixtures/ppt/passing.svg` + a two-page variant): export → snapshot exists with ordered slides; re-export → second stem, first artifact's files byte-stable (FR-007); `page_url` resolves 200; direct `/exports/` URL unchanged (D01–D03, D17)

### Implementation for User Story 1

- [x] T006 [US1] Extend `export_pptx` in `src/agentic_rag_mcp/ppt/bridge.py`: after a successful export, call `snapshot_previews` inside its own failure boundary (failure → degraded marker, export still succeeds — D04) and add the additive `page_url` field to the result (`file`/`url` byte-identical)
- [x] T007 [US1] Wire routes in `dify/docker/mcp-server/server.py`: `GET /decks/{project_id}/{stem}/` → `render_completion_page` as HTMLResponse, and `GET /decks/{project_id}/{stem}/slides/{filename}` → slide SVG FileResponse (content-type `image/svg+xml`), both reusing the projects-root validation from `src/agentic_rag_mcp/ppt/http_exports.py`

**Checkpoint**: export → page_url → completion page with download works end-to-end.

---

## Phase 4: User Story 2 — Faithful In-Browser Preview (Priority: P1)

**Goal**: previews are faithful, readable, responsive, and degrade honestly.

**Independent Test**: quickstart S2 (mobile width readable) + D04/D05 battery (degraded mode honest, download intact).

### Implementation for User Story 2

- [x] T008 [US2] Add responsive styling to the completion page in `src/agentic_rag_mcp/ppt/completion.py`: viewport meta, fluid slide width with max bound, spaced vertical layout, neutral theme tokens (works in dark and light browser settings)
- [x] T009 [US2] Extend `tests/contract/test_ppt_completion_contract.py` for degraded artifacts (D05): a `.degraded` marker renders per-slide "preview unavailable" states while the download control remains; partial snapshots (some slides present) render the missing ones as unavailable — never blank
- [x] T010 [US2] Extend `tests/integration/test_ppt_completion_pipeline.py` with a forced finalize failure (D04): export succeeds, `page_url` returned, degraded page honest; and verify multi-page preview ordering matches deck page order (D17)

---

## Phase 5: User Story 3 — Editing the Finished Deck (Priority: P2)

**Goal**: the completion page's edit path points back to conversation-driven revision.

**Independent Test**: quickstart S3 — the edit control guides back to chat; a revision request produces a new completion page; the old page is unchanged.

- [x] T011 [US3] Finalize the edit control in `src/agentic_rag_mcp/ppt/completion.py`: an "Edit — ask in chat" section with the revision guidance line (e.g. "Ask in chat: 'revise page 2 of this deck'") linking back to the conversation per research R8; and update `dify/ppt-master-rulebook.md` to prefer `page_url` in the final answer's link (`[Preview & download the deck](page_url)`), then regenerate `dify/Chatflow Basic (AgenticRAG Agent + PPT-Master).yml` with the updated rulebook (re-import required — note in the completion report)

---

## Phase 6: User Story 4 — In-Chat Deck Actions (Priority: P1)

**Goal**: deck links in Chat UI answers render as the action bar (Download / Preview-Edit icons); everything else unchanged.

**Independent Test**: quickstart S1 (action bar renders, both actions work) + S5 (Dify webapp still shows the plain link).

### Tests for User Story 4 (write FIRST, must fail)

- [x] T012 [P] [US4] Write failing vitest cases in `ai-chat-landing/lib/deck-url.test.ts` (D13–D16): exports URL → page URL and back; non-deck URLs (external, relative, other localhost routes) → null; malformed deck-family URLs (missing stem, wrong extension) → null

### Implementation for User Story 4

- [x] T013 [P] [US4] Create `ai-chat-landing/lib/deck-url.ts`: the pure derivation helper recognizing exactly the two URL families (`/exports/<project>/<stem>.pptx` ⇄ `/decks/<project>/<stem>/`) with the counterpart rewrite
- [x] T014 [US4] Create `ai-chat-landing/components/deck-actions.tsx`: the deck action bar — Download action (lucide `Download` icon + label, href = the `.pptx` URL) and Preview/Edit action (lucide `Eye` icon + label, href = the page URL), theme-token styled, keyboard-focusable
- [x] T015 [US4] Add the link interceptor to `ai-chat-landing/components/markdown.tsx`: recognized deck URLs render `DeckActions` instead of the plain anchor; all other links render exactly as before (FR-012); then run `pnpm typecheck && pnpm lint && pnpm test` in `ai-chat-landing/`

---

## Phase 7: Polish & Cross-Cutting Concerns

- [x] T016 [P] Update `DEPLOY.md` Step 9 (completion-page routes + action bar + vitest battery) and `docs/NETWORK.md` (the `/decks/` URL family alongside ⑨)
- [x] T017 Rebuild and redeploy the sidecar (`dify/docker/mcp-server/Dockerfile` path unchanged), re-run the full pytest suite including spec 009 tests (D11 — 274+ tests green), and walk quickstart S1–S7 end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: no dependencies
- **Phase 2 (Foundational)**: blocks all server-side stories
- **US1 (Phase 3)**: depends on Phase 2 — builds snapshot wiring + routes
- **US2 (Phase 4)**: depends on T006/T007 (renders from the artifact state)
- **US3 (Phase 5)**: depends on US1's page; the rulebook/DSL regeneration is independent of US4
- **US4 (Phase 6)**: T012/T013 are independent of all server work; T014/T015 need only the derivation helper; end-to-end validation needs US1 deployed
- **Polish (Phase 7)**: after all stories

### User Story Dependencies

- **US1 (P1)**: after Foundational — no story dependencies
- **US2 (P1)**: needs US1's page + snapshot machinery
- **US3 (P2)**: needs US1's page
- **US4 (P1)**: pure-helper part fully parallel; E2E needs US1

### Within Each User Story

- Tests written first and failing (Constitution II)
- Helper modules before route/tool wiring

### Parallel Opportunities

- T002 ∥ T003 (different files)
- T004 ∥ T005 ∥ T012 (three separate test files)
- T013 ∥ any Phase 3/4 task (Chat UI helper vs sidecar work)
- With multiple workers: server side (US1→US2→US3) ∥ Chat UI side (US4) from the start

---

## Implementation Strategy

### MVP First (User Story 1)

1. Setup + Foundational
2. US1 (snapshot + page_url + routes)
3. **STOP and VALIDATE**: quickstart S1/S4 via direct MCP
4. Deploy/demo ready

### Incremental Delivery

Foundation → US1 (completion page) → US2 (fidelity/responsive/degraded) → US3 (edit path + rulebook) → US4 (in-chat action bar) → full battery + redeploy. Nothing breaks spec 009 at any point (D11 guards continuously).

---

## Notes

- Matrix IDs D01–D18 map to `specs/010-ppt-preview-edit/contracts/completion-page.md`
- The `page_url` field is the ONLY tool-contract change and is additive (Constitution I)
- T011's rulebook change requires re-importing chatflow v2 in Dify (user-side) — flag it in the completion report
- Never run `pnpm build` inside `ai-chat-landing/` while `pnpm dev` is running (AGENTS.md rule)

---

## Phase 8: Convergence

- [x] T018 Re-import the regenerated chatflow v2 (dify/Chatflow Basic (AgenticRAG Agent + PPT-Master).yml — rulebook now links page_url) in the Dify UI, publish it, hard-refresh the Chat UI, and run quickstart S1 (action bar renders; Preview/Edit opens the completion page; Download yields the .pptx) plus S5 (Dify webapp still shows the plain link) per US1/AC1, US4/AC1–4, SC-001, SC-006 (partial)
- [x] T019 Validate browser-side scenarios S2 and S3 from specs/010-ppt-preview-edit/quickstart.md: mobile-width readability of the completion page, and a same-chat revision producing a new completion page while the old page stays unchanged per US1/AC2, US2/AC2 (partial)
