# Tasks: "Thinking" Assistant Indicator

**Input**: Design documents from `/specs/022-thinking-indicator/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/thinking-indicator.md

**Tests**: No vitest additions (research R3 — presentational component, no pure logic). The acceptance instrument is the CDP check matrix T1–T6 from `contracts/thinking-indicator.md`.

**Organization**: Single user story (US1, P1).

## Phase 1: Setup (Shared Infrastructure)

- [x] T001 Create spec artifacts per implementation plan (spec, plan, research, data-model, contracts/thinking-indicator.md, quickstart, checklist)

## Phase 2: Foundational (Blocking Prerequisites)

None — no shared infrastructure; one app file changed.

## Phase 3: User Story 1 - Unified "Thinking" indicator while the assistant works (Priority: P1) 🎯 MVP

**Goal**: one indicator (spinning `#82D2F6` LoaderCircle + bold "Thinking") replaces the waiting dots and the streaming caret; it clears exactly when generation ends.

**Independent Test**: CDP T1–T6 green (waiting + streaming show it, old indicators gone, completion and delete clear it, a11y attributes present).

### Implementation for User Story 1

- [x] T002 [P] [US1] Write `/tmp/kilo/cdp/thinking-check.mjs` implementing T1–T6 from `contracts/thinking-indicator.md`
- [x] T003 [US1] In `ai-chat-landing/app/page.tsx`: added the `ThinkingIndicator` component (row `flex items-center gap-2 pt-2.5`, `role="status"`; `LoaderCircle` `size-4 motion-safe:animate-spin text-[#82D2F6]`, `aria-hidden="true"`; bold `text-sm font-semibold` "Thinking") + the lucide import; replaced the waiting-dots block and the streaming caret with it
- [x] T004 [US1] Old-indicator grep (T4): zero matches for the dot spans (`animate-pulse rounded-full bg-current`, `animation-delay`) and the caret span (`h-4 w-2 animate-pulse rounded-sm bg-foreground/50`) in `app/`
- [x] T005 [US1] Ran `/tmp/kilo/cdp/thinking-check.mjs` — **T1–T6 all green**: waiting shows the row (spin computed, color `rgb(130, 210, 246)`, bold "Thinking" weight 600, dots gone); streaming shows it below content (caret gone); completion clears (footer shows); delete-mid-stream clears; `aria-hidden` + `role="status"` + `motion-safe:` present

## Phase 4: Polish & Cross-Cutting Concerns

- [x] T006 Ran `pnpm typecheck && pnpm lint && pnpm test` in `ai-chat-landing/` — all green (tsc, eslint, 79/79); also fixed two lint warnings from yesterday's persisted scripts (unused `version` variable in `landing-check.mjs` and `welcome-cards.mjs`)
- [x] T007 Boundary check: diff limited to `ai-chat-landing/app/page.tsx`, the two script lint fixes, and `specs/022-thinking-indicator/`
- [x] T008 Commit spec artifacts + diff together *(committed and pushed)*

## Phase 5: Convergence

- [x] T009 Persist the acceptance script in the repo (done — `ai-chat-landing/scripts/thinking-check.mjs` runs green from the repo location; lint-safe): copy `/tmp/kilo/cdp/thinking-check.mjs` to `ai-chat-landing/scripts/thinking-check.mjs` and run it from there (the recurring check for the indicator; its siblings wide-layout/landing-check/welcome-cards are already persisted) (Constitution II) (partial)

## Dependencies & Execution Order

- T001 → all; T002 ∥ T003 (different files, independent) → T004 → T005 → T006 → T007 → T008

### Parallel Opportunities

- T002 (write the check script) and T003 (the page edit) are independent files — [P]

### Parallel Example: User Story 1

```text
Task: "Write thinking-check.mjs (T1–T6)"
Task: "Add ThinkingIndicator and replace both old indicator spots in page.tsx"
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. T001 → T002 (check script) → T003 (component + both replacements) → T004 (grep) → T005 (green run)
2. Polish: gates, boundary, commit

US1 is the entire feature; delivery = one component replacing two indicator spots, verified by the T1–T6 matrix.
