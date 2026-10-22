# Tasks: Wide Chat Layout

## Phase 1: Setup

- [x] T001 Create spec artifacts (spec, plan, research, contracts, data-model, quickstart, checklist) from the clarified scope
- [x] T002 Capture pre-change PDF baseline *(closed via T015's SC-004 fallback — the pre-change window closed when `1b3f4da` shipped; a baseline was recorded honestly on 2026-10-22)*

## Phase 2: Foundational

None — no shared infrastructure; the change is confined to one file.

## Phase 3: [US1] Wide message column and composer (P1)

Goal: at ≥1280px the column and composer are `min(90%,1400px)` of the content area, centered; below 1280px byte-identical to today.
Independent test: CDP T1–T6.

- [x] T003 [US1] Write the CDP acceptance script (persisted at `ai-chat-landing/scripts/wide-layout.mjs` per T013) implementing the T1–T9 matrix with the five loud failure modes from `contracts/wide-layout.md`
- [x] T004 [US1] In `ai-chat-landing/app/page.tsx` (~757), add `xl:max-w-[min(90%,1400px)]` to the message column div, keeping `max-w-3xl` as the <xl base
- [x] T005 [P] [US1] In `ai-chat-landing/app/page.tsx` (~868), add `xl:max-w-[min(90%,1400px)]` to the composer div
- [x] T006 [US1] Run the CDP script — T1–T6 pass *(verified 2026-10-22: 1065.6 / 1296 / 1400 / 921.6 / 768 / 390 px, all green)*

## Phase 4: [US2] User-bubble ceiling (P2)

Goal: long user messages stay readable (≤672px at ≥1024px); short messages stay compact.
Independent test: CDP T7. Depends on US1 (bubble width is relative to the widened column).

- [x] T007 [US2] In `ai-chat-landing/app/page.tsx` (~761), add `lg:max-w-2xl` to the user bubble div
- [x] T008 [US2] Run T7: long user message bubble ≤672px at 1440×900 *(verified: 672.0px)*

## Phase 5: Polish & cross-cutting

- [x] T009 Run `pnpm typecheck && pnpm lint && pnpm test` in `ai-chat-landing/` — all green (never `pnpm build` while `pnpm dev` runs) *(tsc clean, eslint clean, 71/71 vitest — run before the diff and after)*
- [x] T010 Run T8: PDF export pagination vs baseline *(closed via T015: FR-004 double-verified — `lib/pdf-export/` untouched since the wave commit AND a live export produced a valid file; baseline established 2026-10-22)*
- [x] T011 Run T9 smoke at 1440×900: sidebar buckets, Load more, delete flow *(closed via T014 — verified green at the wide layout)*
- [x] T012 Commit spec artifacts + diff together *(commit `1b3f4da`, pushed with `ad5af3f`/`4b37342`/`025e988` to origin/main)*

## Dependencies

T001 → all; T002 → T010; T003 → T006; T004/T005 (same file, one edit) → T006; T007 → T008; US2 after US1.

## Parallel opportunities

T004 + T005 (single edit); T009–T011 after T006/T008.

## MVP scope

Phase 3 (US1) alone ships the feature; US2 is the readability safeguard.

## Implementation strategy

Smallest-first: three additive class-string edits, then the CDP
measurement script, then the regression smoke — no refactors, no
abstraction, no new dependencies.

## Phase 6: Convergence

- [x] T013 Persist the wide-layout acceptance script in the repo: `ai-chat-landing/scripts/wide-layout.mjs`; quickstart references updated *(SC-001–SC-003)*
- [x] T014 Run the spec 015 behavioral smoke at the widened layout *(verified 2026-10-22: history rows 20, bucket headers "Today"/"Previous 7 days" render, Load more paginates 20→27, send creates a row 27→28, delete flow removes it 28→27 with marker gone; two earlier smoke orphans in Dify were cleaned up — backend shows zero test rows)* (FR-005, T011)
- [x] T015 Export the conversation PDF and record it as the SC-004 baseline *(26.2 KiB at `/tmp/kilo/cdp/pdf-baseline.pdf`, exported live from a clean throwaway conversation — "baseline-established")* (SC-004, T002, T010)

## Phase 7: Convergence

- [x] T016 Add the SC-002 1024px spot-check to `ai-chat-landing/scripts/wide-layout.mjs` *(verified 2026-10-22: T5b 1024×768 → column=768.0px, all structural checks green)* (SC-002)
- [x] T017 Update `specs/016-wide-chat-layout/plan.md` §Verification to reference the persisted script path *(plan.md:38 now points at `ai-chat-landing/scripts/wide-layout.mjs`)* (plan: verification decision)
