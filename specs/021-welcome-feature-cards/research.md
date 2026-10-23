# Research: Welcome Feature Cards

## R1 — Card data lives in `page.tsx` near the empty state

- **Decision**: a `FEATURE_CARDS` array of six records next to the empty-state
  render (replacing the `suggestions` array in place).
- **Rationale**: the data is static, app-local, and used in exactly one
  place — the replaced array's location is the house pattern.
- **Alternatives considered**: a `lib/` module — rejected (one consumer, no
  logic; indirection for six literals).

## R2 — Sibling button + link, never nested

- **Decision**: each card is a container `div` holding a send `<button>`
  (title, icon, description) and a sibling `<a>` (the label) — never a link
  inside a button.
- **Rationale**: nested interactive elements are invalid HTML and create
  propagation hazards; siblings give the two click behaviors structurally
  (button sends, link navigates) with no stopPropagation scripting.
- **Alternatives considered**: link-inside-button with stopPropagation —
  rejected (invalid markup, fragile event handling).

## R3 — No vitest additions; CDP is the acceptance instrument

- **Decision**: acceptance is the CDP render/send/link matrix
  (contracts/welcome-cards.md T1–T6); no unit tests.
- **Rationale**: the change is a static data set plus presentational
  structure — no pure logic to cover (house convention; the 79 existing
  tests stay green).
- **Alternatives considered**: a test asserting the array's length —
  rejected (tautological constant assertion).

## R4 — Grid classes reused unchanged

- **Decision**: keep `grid w-full max-w-2xl gap-3 sm:grid-cols-2` — the six
  cards flow into two columns × three rows at ≥640px, stacked below.
- **Rationale**: zero new layout code; the locked "existing pattern" is
  literally the current classes.
- **Alternatives considered**: a three-column grid at desktop — rejected
  (changes the locked 2×3 design).

## Error handling (user-requested)

| Condition | Behavior |
|---|---|
| Placeholder URLs 404 (until real pages exist) | accepted temporary state — the link opens a new tab to a 404; only the URL strings change later (spec Edge Cases) |
| Link inside a clickable card (propagation) | structural separation: button and link are siblings (R2) — clicking the label never sends |
| Invalid nested-interactive HTML | avoided by R2's structure (no `<a>` inside `<button>`) |
| Emoji rendering | plain text emojis — no icon font/library dependency (FR-006) |
| Keyboard access | real `<button>` (focus + Enter sends) and real `<a>` (native link) — no custom key handling |
| Spec-020 landing check card count (4 → 6) | the `/tmp/kilo/cdp/landing-check.mjs` assertion is updated to 6 cards and re-run (regression scope, not a break) |
| Old suggestion prompts removed | superseded by design (spec Clarifications); a future variant could re-add quick-prompt chips separately |
