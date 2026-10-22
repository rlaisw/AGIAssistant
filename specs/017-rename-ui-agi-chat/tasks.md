# Tasks: Rename UI Skin to AGI Chat

**Input**: Design documents from `/specs/017-rename-ui-agi-chat/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/rename-mapping.md

**Tests**: No vitest tasks — research R2 verified zero test coupling (no test/snapshot references the brand strings). The acceptance instrument is the CDP rendered check per `contracts/rename-mapping.md` (constitution II).

**Organization**: Single user story (US1, P1) — the complete rename surface.

## Phase 1: Setup (Shared Infrastructure)

- [x] T001 Create spec artifacts per implementation plan (spec, plan, research, data-model, contracts/rename-mapping.md, quickstart, checklist)

## Phase 2: Foundational (Blocking Prerequisites)

None — no shared infrastructure; the change is string literals in existing files.

## Phase 3: User Story 1 - Rename every UI-skin brand string to "AGI Chat" (Priority: P1) 🎯 MVP

**Goal**: All eight enumerated brand strings read "AGI Chat"; zero "AgenticRAG"/"AI Chat" remains in any user-visible surface including exported PDFs; backend artifacts untouched.

**Independent Test**: negative grep of `ai-chat-landing/{app,components,lib,public}` returns zero brand strings; CDP rendered checks pass rows 1–8 of `contracts/rename-mapping.md`; `git diff --name-only` is confined to the three source files + `ai-chat-landing/README.md`.

### Implementation for User Story 1

- [x] T002 [P] [US1] Replace the six brand strings in `ai-chat-landing/app/page.tsx` — line ~594 `AI Chat`→`AGI Chat` (sidebar brand), ~678 `AgenticRAG`→`AGI Chat` (header badge), ~820 `AgenticRAG`→`AGI Chat` (assistant footer), ~872 placeholder `Message AI Chat…`→`Message AGI Chat…`, ~885 `AgenticRAG`→`AGI Chat` (composer label), ~900 `AI Chat can make mistakes.`→`AGI Chat can make mistakes.` (disclaimer)
- [x] T003 [P] [US1] Replace the metadata title in `ai-chat-landing/app/layout.tsx` (~16): `AI Chat — A simple, modern interface for AI conversations` → `AGI Chat — A simple, modern interface for AI conversations` (prefix-swap; subtitle kept per research R4)
- [x] T004 [P] [US1] Replace the PDF metadata line in `ai-chat-landing/lib/pdf-export/render.tsx` (~45): `… · AgenticRAG Chat` → `… · AGI Chat` (contract row 8)
- [x] T005 [US1] Negative check: grep `ai-chat-landing/{app,components,lib,public}` for `AgenticRAG|AI Chat` returns zero matches *(verified: exit 1, zero hits)*
- [x] T006 [US1] CDP rendered checks for contract rows 1–7 *(verified: sidebar, header, placeholder, composer, disclaimer, `document.title` = "AGI Chat — …"; no AgenticRAG/AI-Chat text anywhere in the rendered page)*
- [x] T007 [US1] CDP live-flow checks for contract rows 3+8 *(verified: fresh draft → throwaway send → assistant footer "AGI Chat" → PDF export (28.5 KiB) → render-container metadata line "· AGI Chat", no AgenticRAG → throwaway deleted, marker gone. Two check-logic fixes along the way: reply-done = Copy-response button exists (send button is always disabled with empty input); PDF metadata verified in the 744px render container (pages are rasterized, pdftotext can't see it))*

**Checkpoint**: US1 complete — every user-visible surface shows "AGI Chat"

## Phase 4: Polish & Cross-Cutting Concerns

- [x] T008 Accuracy touch-up in `ai-chat-landing/README.md` (~45): badge now described as displaying "AGI Chat"
- [x] T009 Run `pnpm typecheck && pnpm lint && pnpm test` in `ai-chat-landing/` — all green *(tsc clean, eslint clean, 71/71 vitest)*
- [x] T010 Boundary check: modified files exactly `app/page.tsx`, `app/layout.tsx`, `lib/pdf-export/render.tsx`, `ai-chat-landing/README.md` — nothing else (SC-002/FR-009)
- [ ] T011 Commit spec artifacts + diff together

## Dependencies & Execution Order

- T001 → all
- T002 ∥ T003 ∥ T004 (three different files, independent) → T005 → T006, T007 → T008, T009 → T010 → T011
- T006 and T007 share no state (T007 uses its own fresh draft); run sequentially or in either order

### Parallel Opportunities

- T002, T003, T004 run in parallel (distinct files)
- T006 and T007 can overlap if two tabs are used (T007 drives its own throwaway conversation)

### Parallel Example: User Story 1

```text
# Apply the three file edits together:
Task: "Replace the six brand strings in ai-chat-landing/app/page.tsx"
Task: "Replace the metadata title in ai-chat-landing/app/layout.tsx"
Task: "Replace the PDF metadata line in ai-chat-landing/lib/pdf-export/render.tsx"
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. T001 artifacts → T002–T004 edits (parallel) → T005 negative grep (instant)
2. T006 + T007 CDP verification (rendered + live flow + PDF)
3. T008–T011 polish, gates, boundary, commit

### Incremental Delivery

US1 is the entire feature; there is no second increment. Delivery = the three file edits verified by the contract's rendered/negative/boundary checks, committed as one change.
