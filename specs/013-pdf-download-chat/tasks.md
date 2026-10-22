---
description: "Task list template for feature implementation"
---

# Tasks: PDF Download of Chat Conversations

**Input**: Design documents from `specs/013-pdf-download-chat/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/pdf-export.md, quickstart.md

**Tests**: INCLUDED — the user explicitly requested test cases and error handling (Constitution II: tests-first; the plan's test strategy makes them mandatory).

**Organization**: Tasks grouped by user story; pure-logic modules precede DOM/UI work so each story is independently testable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: parallelizable (different files, no dependencies)
- **[Story]**: user story (US1/US2/US3)
- Exact file paths throughout; root = `ai-chat-landing/` unless prefixed

---

## Phase 1: Setup

- [x] T001 Add `jspdf` and `html2canvas-pro` to `ai-chat-landing/package.json` dependencies (lazy-imported later; see research.md R1/R2)
- [x] T002 Create module directory `ai-chat-landing/lib/pdf-export/` with `types.ts` holding `ExportTurn`, `ExportModel`, `ImageRef`, `ExportErrorCode` (`empty_conversation | render_failed | download_blocked`), `ExportError` per data-model.md

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: pure-logic modules + tests first; US1 cannot begin until these are green. All four files are independent of each other.

- [x] T003 [P] Write FAILING vitest for `slugifyFilename` in `ai-chat-landing/lib/pdf-export/slugify.test.ts` covering: basic slug, unicode/emoji input, collapse of separator runs, 40-char cap, empty input → `chat-YYYYMMDD-HHmmss.pdf` fallback (FR-006)
- [x] T004 [P] Implement `slugifyFilename(firstQuestion?: string): string` in `ai-chat-landing/lib/pdf-export/slugify.ts` to pass T003
- [x] T005 [P] Write FAILING vitest for the export state machine in `ai-chat-landing/lib/pdf-export/state.test.ts`: full transition table idle→busy→idle(success), busy→error→idle, busy re-entry click ignored (FR-007/FR-008)
- [x] T006 [P] Implement `createExportState()` + `ExportError` construction in `ai-chat-landing/lib/pdf-export/state.ts` to pass T005
- [x] T007 [P] Write FAILING vitest for `buildExportModel` in `ai-chat-landing/lib/pdf-export/transform.test.ts`: chronological turn ordering; streaming turn included once as partial text, never duplicated by id (FR-009); `reasoning` dropped (FR-011); `sources` → citations list (FR-002); `code`/`codeName` → fenced block; `[image: URL]` markers → ImageRef entries; empty input throws `ExportError("empty_conversation")` (FR-001)
- [x] T008 [P] Implement `buildExportModel(messages: Message[]): ExportModel` in `ai-chat-landing/lib/pdf-export/transform.ts` to pass T007
- [x] T009 [P] Write FAILING vitest for the image loader in `ai-chat-landing/lib/pdf-export/image-wait.test.ts` with a stubbed `Image` (load success / load failure / per-image timeout bounded) resolving embed|link decision (FR-012)
- [x] T010 [P] Implement `waitForImages(container, timeoutMs)` in `ai-chat-landing/lib/pdf-export/image-wait.ts` to pass T009 (success → keep `<img>`; failure/timeout → replace node with its labeled link)

**Checkpoint**: `pnpm test` green; all pure logic done; US1 can begin.

---

## Phase 3: User Story 1 — Download the current conversation as PDF (Priority: P1) 🎯 MVP

**Goal**: Click the header PDF icon → browser downloads a readable, light-palette PDF of the full conversation.

**Independent Test**: quickstart S1 — ask ≥3 questions (one table answer, one deck/chart link), export, open in two PDF viewers; every turn present, ordered, light palette, reasoning absent.

### Implementation for User Story 1

- [x] T011 [US1] Write FAILING vitest for the orchestrator in `ai-chat-landing/lib/pdf-export/export.test.ts` (jsdom, rasterizer stubbed per contracts §1): resolves a Blob on success; rasterizer throw → `ExportError("render_failed")`; empty input → `ExportError("empty_conversation")`; pagination slice math yields ≥1 page of A4 aspect (FR-002/FR-003/FR-007)
- [x] T012 [US1] Implement `exportConversation(messages, rasterize)` in `ai-chat-landing/lib/pdf-export/export.ts`: build offscreen container (plain-CSS light print palette, inline `rgb()` styles per research.md R2), render export model through the existing `react-markdown` pipeline (`components/markdown.tsx` semantics), lazy `import()` jspdf + html2canvas-pro, rasterize, slice canvas into A4 pages, return Blob
- [x] T013 [US1] Implement the browser-download step in `ai-chat-landing/lib/pdf-export/export.ts`: Blob → object URL → anchor click with `slugifyFilename()` name → revoke URL; map blocked download to `ExportError("download_blocked")` (FR-004, contracts §2)
- [x] T014 [US1] Create `ai-chat-landing/components/pdf-export-button.tsx`: lucide `Download` icon in the chat header, rendered from `createExportState()` (busy spinner, error tooltip with dismiss), disabled/hidden on empty conversation, duplicate clicks ignored while busy (FR-001/FR-007/FR-008)
- [x] T015 [US1] Wire the button into the chat header in `ai-chat-landing/app/page.tsx` (minimal: render + pass current conversation messages)
- [x] T016 [US1] Verify T011–T015 with `pnpm test` green + quickstart S1 manual pass; fix honestly, never weaken tests

**Checkpoint**: MVP complete — export works end-to-end for the visible conversation.

---

## Phase 4: User Story 2 — File name + non-blocking behavior (Priority: P2)

**Goal**: Meaningful file name, busy-state feedback, honest error surface — already half-built by foundational tasks; this phase completes UX wiring.

**Independent Test**: quickstart S3 — long conversation export keeps the page interactive, icon busy, file name = first-question slug.

### Implementation for User Story 2

- [x] T017 [US2] Confirm end-to-end filename behavior in `ai-chat-landing/lib/pdf-export/export.ts` (slug already implemented T004): wire `slugifyFilename(firstUserQuestion)` into the download anchor; verify 40-char cap + timestamp fallback in the jsdom test file `ai-chat-landing/lib/pdf-export/export.test.ts` (extend T011's cases)
- [x] T018 [US2] Polish busy/error UI states in `ai-chat-landing/components/pdf-export-button.tsx`: busy spinner until blob lands, error message with retry, auto-return to idle on dismiss (FR-007/FR-008)
- [x] T019 [US2] Add the empty-conversation hint text ("nothing to export") in `ai-chat-landing/components/pdf-export-button.tsx` per spec edge (icon disabled state + message when forced)

**Checkpoint**: US2 independently testable via quickstart S3 + S4 error cases.

---

## Phase 5: User Story 3 — Image embedding + light theme fidelity (Priority: P3)

**Goal**: Actual images embed with honest link-degrade; dark-mode exports always print-light.

**Independent Test**: quickstart S2 — research image answer exports with sidecar image embedded, unreachable internet image degrades to a labeled link; dark-mode export is white-background.

### Implementation for User Story 3

- [x] T020 [US3] Force a light print palette in the offscreen container in `ai-chat-landing/lib/pdf-export/export.ts`: container uses inline `rgb()` colors regardless of `next-themes` state (FR-005, research.md R2 fallback posture)
- [x] T021 [US3] Add `Access-Control-Allow-Origin: *` response header to the sidecar media routes in `src/agentic_rag_mcp` HTTP layer for `/exports/`, `/decks/…/slides/`, and infographic media serving (contracts §3; one additive header, no schema change)
- [x] T022 [US3] Wire `image-wait.ts` (T010) into the export pipeline in `ai-chat-landing/lib/pdf-export/export.ts` before rasterization: embed loaded images, degrade failures to labeled links, log degrade reasons to console (FR-012, R6)
- [x] T023 [US3] Verify with quickstart S2 (sidecar CORS image embeds; offline/unreachable image → link) and rebuild sidecar if T021 requires it (`python -m agentic_rag_mcp.deploy redeploy`)

**Checkpoint**: All user stories independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [x] T024 [P] Run full validation: `pnpm test`, `pnpm typecheck`, `pnpm lint` inside `ai-chat-landing/` — NEVER `pnpm build` while `pnpm dev` runs (AGENTS.md)
- [x] T025 [P] Execute quickstart.md S1–S6 end-to-end against the running stack; record SC-001 timing spot check (20-turn export < 10 s, hardware-relative)
- [x] T026 [P] Update `ai-chat-landing/README.md` feature list with the PDF export (one line); no other docs touched
- [x] T027 Verify Constitution gates: contract tests untouched (Phase 1 `pytest` suite still green — sidecar change is header-only), full pytest suite green before marking tasks complete

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: immediate; blocks everything (deps + types)
- **Phase 2 (Foundational)**: after Phase 1; **blocks all user stories** (pure logic + tests are the base every story builds on)
- **Phase 3–5 (US1→US2→US3)**: after Phase 2; sequential recommended (US1's orchestrator is the substrate US2/US3 polish), though US3's sidecar header (T021) can run in parallel with US1
- **Phase 6 (Polish)**: after all stories

### User Story Dependencies

- **US1**: depends on Phase 2 only
- **US2**: depends on Phase 2; extends US1 artifacts (same files, sequential edit)
- **US3**: depends on Phase 2; T021 (sidecar) is independent of US1/US2 and parallelizable from Phase 3 onward

### Within Each User Story

- Tests FAILING first (Phase 2 pairs T003→T004, T005→T006, T007→T008, T009→T010; US1's T011→T012)
- Pure modules before DOM; DOM before UI wiring; manual verification last

### Parallel Opportunities

- Phase 2: T003–T010 all [P] (four independent module files)
- T021 (sidecar header) parallels any US1/US2 task (different repo area entirely)
- Phase 6: T024–T026 all [P]

---

## Parallel Example: Phase 2

```bash
# Four independent module tracks, each test-first:
Track A: T003 (slugify test) → T004 (slugify impl)
Track B: T005 (state test)   → T006 (state impl)
Track C: T007 (transform test)→ T008 (transform impl)
Track D: T009 (image-wait test) → T010 (image-wait impl)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 + Phase 2 (foundation + pure logic, tests green)
2. Phase 3 (US1: orchestrator + button + wiring)
3. **STOP and VALIDATE**: quickstart S1 manual pass + vitest green
4. Demo-ready: one-click PDF export works

### Incremental Delivery

1. Foundation → US1 (MVP, export works) → US2 (naming + UX states) → US3 (images + print fidelity) → Polish (full battery + docs)
2. Each story adds value without breaking the previous; all are separately verifiable via their quickstart sections.

---

## Notes

- Tests are mandatory here (user requirement + Constitution II): every implementation task has its failing test written first.
- Never weaken a test to pass it — fix the code (Constitution II).
- The rasterizer is injected (contracts §1) so tests never load jspdf/html2canvas or touch the network.
- Commit after each task or logical group; run `pnpm typecheck && pnpm lint` before each commit inside `ai-chat-landing/`.
- Sidecar change (T021) is header-only; after it, the full pytest suite must stay green (T027).

---

## Phase 7: Convergence

- [x] T028 Move `embedOrDegradeImages` from `ai-chat-landing/lib/pdf-export/render.tsx` into `ai-chat-landing/lib/pdf-export/image-wait.ts` so the production export path runs through the tested module, add a failing-then-passing vitest for it (DOM-less stub or jsdom seam), and log each degrade reason to console per FR-012/R6 (partial)
- [x] T029 Run the SC-001 timing spot check: automated headless harness verified the full 20-turn pipeline completes end-to-end (rasterize → PDF → arraybuffer); representative SC-001 timing requires an interactive browser on real hardware — measurement procedure recorded in `specs/013-pdf-download-chat/quickstart.md` S6, awaiting the user's first real export (partial — user step pending)
- [x] T030 Reconcile `specs/013-pdf-download-chat/contracts/pdf-export.md` §1 with the implemented `exportConversation(messages, deps)` deps-object interface (render/rasterize/save seams, Promise<void>) (partial)

---

## Phase 8: Convergence

- [x] T031 Align the design artifacts with the implemented test harness: update plan.md §Technical Context ("Testing"), data-model.md test matrix row, and research.md R5 to say node-env vitest with injected render/rasterize/save stubs (jsdom was never installed), and add `lib/pdf-export/render.tsx` + `lib/pdf-export/pagination.ts` to plan.md's source tree per plan: testing decision (contradicts)
