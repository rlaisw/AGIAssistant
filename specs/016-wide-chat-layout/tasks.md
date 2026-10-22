# Tasks: Wide Chat Layout

## Phase 1: Setup

- [x] T001 Create spec artifacts (spec, plan, research, contracts, data-model, quickstart, checklist) from the clarified scope
- [ ] T002 Capture pre-change PDF baseline: with `pnpm dev` running in `ai-chat-landing/`, export a multi-turn conversation via the header ⬇ button and save it as the T8 comparison baseline *(open — manual; the layout change shipped before a baseline could be captured, so T010 will record the first export as the baseline per SC-004)*

## Phase 2: Foundational

None — no shared infrastructure; the change is confined to one file.

## Phase 3: [US1] Wide message column and composer (P1)

Goal: at ≥1280px the column and composer are `min(90%,1400px)` of the content area, centered; below 1280px byte-identical to today.
Independent test: CDP T1–T6.

- [x] T003 [US1] Write `/tmp/kilo/cdp/wide-layout.mjs` implementing the T1–T9 matrix with the five loud failure modes from `contracts/wide-layout.md`
- [x] T004 [US1] In `ai-chat-landing/app/page.tsx` (~757), add `xl:max-w-[min(90%,1400px)]` to the message column div, keeping `max-w-3xl` as the <xl base
- [x] T005 [P] [US1] In `ai-chat-landing/app/page.tsx` (~868), add `xl:max-w-[min(90%,1400px)]` to the composer div
- [x] T006 [US1] Run `node /tmp/kilo/cdp/wide-layout.mjs` — T1–T6 pass *(verified 2026-10-22: 1065.6 / 1296 / 1400 / 921.6 / 768 / 390 px, all green)*

## Phase 4: [US2] User-bubble ceiling (P2)

Goal: long user messages stay readable (≤672px at ≥1024px); short messages stay compact.
Independent test: CDP T7. Depends on US1 (bubble width is relative to the widened column).

- [x] T007 [US2] In `ai-chat-landing/app/page.tsx` (~761), add `lg:max-w-2xl` to the user bubble div
- [x] T008 [US2] Run T7: send a ≥2000-character message at 1440×900; bubble ≤672px *(verified via synthetic 2000-char bubble measured inside the real column: 672.0px)*

## Phase 5: Polish & cross-cutting

- [x] T009 Run `pnpm typecheck && pnpm lint && pnpm test` in `ai-chat-landing/` — all green (never `pnpm build` while `pnpm dev` runs) *(tsc clean, eslint clean, 71/71 vitest — run twice: pre-commit and post-diff)*
- [ ] T010 Run T8: export the same conversation as T002; pagination matches baseline (or record baseline honestly) *(open — manual; PDF export is structurally immune: `lib/pdf-export/` untouched since the wave commit, off-screen 744px container)*
- [ ] T011 Run T9 smoke at 1440×900: sidebar buckets, Load more, delete flow *(partial — structural presence verified green via CDP: sidebar, New chat, PDF button; the full 015-flow smoke remains manual, see quickstart.md)*
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
