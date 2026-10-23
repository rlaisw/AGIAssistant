# Implementation Plan: Welcome Feature Cards

**Branch**: `021-welcome-feature-cards` | **Date**: 2026-10-23 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/021-welcome-feature-cards/spec.md`

## Summary

Replace the four generic suggestion cards in the welcome empty state with
a six-card feature showcase (title, emoji icon, one-line description,
example-prompt label). A card's send area is a real `<button>` that sends
the label text as the prompt; the label is a sibling `<a>` (new tab) — no
nested interactive elements. Heading and subtext unchanged; grid stays
`sm:grid-cols-2` (three rows).

## Technical Context

- **Language/Version**: TypeScript (Next.js 16.4.2, React 19.3, Tailwind v4)
- **Primary Dependencies**: none added — static card data + existing elements
- **Storage**: N/A
- **Testing**: `pnpm typecheck && pnpm lint && pnpm test` (79/79); CDP
  render/send/link matrix T1–T6 (contracts/welcome-cards.md); no vitest
  additions (static data — house convention, research R3)
- **Target Platform**: web (desktop 2×3 grid, mobile stacked)
- **Constraints**: no invalid nested-interactive markup (button and link
  are siblings, not nested); no backend/API changes; six placeholder URLs
  documented as temporary

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Contract Preservation**: PASS — UI empty state only.
- **II. Tests-First**: PASS — the runnable check is the CDP matrix
  (contracts/welcome-cards.md T1–T6) written before the edit; the data is
  static (no pure logic for vitest — house convention).
- **III. Minimal Dependencies**: PASS — zero (text emojis, no icon library).
- **IV. Honest Answers**: PASS — placeholder URLs are documented as
  404-until-real-pages (temporary), and cards 4–6's navigational nature is
  stated, not disguised as capability.
- **V. Spec-Driven Replacement**: PASS — the four generic suggestion cards
  are replaced (documented supersession); no dead suggestion data left.

No violations; Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/021-welcome-feature-cards/
├── plan.md              # This file
├── research.md          # R1–R4 decisions + error handling
├── data-model.md        # FEATURE_CARDS shape (6 records)
├── contracts/
│   └── welcome-cards.md # card mapping + T1–T6 check matrix + error handling
├── quickstart.md        # Validation guide
├── checklists/
│   └── requirements.md  # (from /speckit.specify)
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
ai-chat-landing/app/
└── page.tsx            # replace `suggestions` (4 records) with `FEATURE_CARDS`
                        # (6 records + url); empty-state grid renders container
                        # cards (button send area + sibling label link)
ai-chat-landing/scripts/ (none — the spec-020 landing check lives in /tmp
                        # and gets its card-count assertion updated 4 → 6)
```

**Structure Decision**: one app file changed (~60 lines); the card data is a
static array near the empty state (house pattern, matches the replaced
`suggestions` array).

## Design

- **Data**: `FEATURE_CARDS: { title, icon, description, label, url }[]` —
  the six locked records (spec Acceptance table).
- **Structure** (valid, no nested interactive):
  container `div` (border, hover) → send `<button>` (title + icon +
  description; `onClick={() => send(label)}`) → sibling `<a href target=
  "_blank" rel="noopener noreferrer">{label}</a>`. Button and link never
  nest — propagation separation is structural, not scripted.
- **Grid**: unchanged classes (`grid w-full max-w-2xl gap-3 sm:grid-cols-2`)
  → two columns × three rows at ≥640px, stacked below.
- **Keyboard/a11y**: real `<button>` (focusable, Enter sends) and real `<a>`
  (native link semantics).

## Verification

1. Gates: typecheck, lint, 79/79 vitest.
2. CDP T1–T6 per `contracts/welcome-cards.md`: six cards render with exact
   titles/descriptions and 2-col grid at 1440 / 1-col at 390; body click
   sends the label prompt (user bubble appears); all six links carry the
   expected `example1–6.html` hrefs with `target="_blank"`; a label click
   sends nothing; heading/subtext unchanged; the spec-020 landing check is
   updated to expect 6 cards and stays green; wide-layout matrix re-run
   green.
