# Tasks: Welcome Feature Cards

**Input**: Design documents from `/specs/021-welcome-feature-cards/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/welcome-cards.md

**Tests**: No vitest additions (research R3 — static card data, no pure logic). The acceptance instrument is the CDP check matrix T1–T6 from `contracts/welcome-cards.md`.

**Organization**: Single user story (US1, P1).

## Phase 1: Setup (Shared Infrastructure)

- [x] T001 Create spec artifacts per implementation plan (spec, plan, research, data-model, contracts/welcome-cards.md, quickstart, checklist)

## Phase 2: Foundational (Blocking Prerequisites)

None — no shared infrastructure; one app file changed.

## Phase 3: User Story 1 - Discover and launch a capability from the welcome page (Priority: P1) 🎯 MVP

**Goal**: the welcome empty state shows the six locked feature cards (title, emoji, description) in a 2×3 desktop grid / stacked mobile; body click sends the label prompt; the label is a new-tab link.

**Independent Test**: CDP T1–T5 green (render, grid, body-send, links, no-send-on-label) + heading/subtext unchanged.

### Implementation for User Story 1

- [x] T002 [P] [US1] Write `/tmp/kilo/cdp/welcome-cards.mjs` implementing T1–T5 from `contracts/welcome-cards.md`
- [x] T003 [US1] In `ai-chat-landing/app/page.tsx`: replaced `suggestions` with `FEATURE_CARDS` (six locked records); container-card structure (send `<button>` + sibling `<a target="_blank">`, never nested); removed the now-unused lucide imports (`Code`, `FileText`, `Lightbulb`, `SquarePen` — verified suggestions-only usages)
- [x] T004 [US1] Updated `/tmp/kilo/cdp/landing-check.mjs`: card-count assertion 4 → 6; selector moved from `button.rounded-2xl` to the container `div.rounded-2xl` (the new structure puts those classes on the container, not the button)
- [x] T005 [US1] Ran `/tmp/kilo/cdp/welcome-cards.mjs` — **T1–T5 all green**: six cards with exact locked titles/descriptions, 2-col grid at 1440 and 1-col at 390, heading/subtext unchanged, body click sends "How to create PPT", all six `example1–6.html` hrefs with `target="_blank"`, label click sends nothing

## Phase 4: Polish & Cross-Cutting Concerns

- [x] T006 Ran `pnpm typecheck && pnpm lint && pnpm test` in `ai-chat-landing/` — all green (tsc, eslint, 79/79)
- [x] T007 Regression scope (T6): landing-check (updated, **6 cards confirmed** — header "New chat", empty state, T4 first-send + cleanup) + `node scripts/wide-layout.mjs` structural — both green
- [x] T008 Boundary check: diff limited to `ai-chat-landing/app/page.tsx` (+56/−33) + `specs/021-welcome-feature-cards/`
- [ ] T009 Commit spec artifacts + diff together

## Dependencies & Execution Order

- T001 → all; T002 ∥ T003 (different files, independent) → T004 → T005 → T006, T007 → T008 → T009

### Parallel Opportunities

- T002 (write the check script) and T003 (the page edit) are independent files — [P]
- T006 and T007 are sequential (one browser for CDP re-runs)

### Parallel Example: User Story 1

```text
Task: "Write welcome-cards.mjs (T1–T5)"
Task: "Replace suggestions with FEATURE_CARDS and the sibling button/link structure in page.tsx"
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. T001 → T002 (check script) → T003 (data + structure edit) → T004 (landing-check update) → T005 (green run)
2. Polish: gates, regression re-runs, boundary, commit

US1 is the entire feature; delivery = the card data + structure, verified by the T1–T6 matrix.
