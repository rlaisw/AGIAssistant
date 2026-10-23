# Research: "Thinking" Assistant Indicator

## R1 — One local component, two usages

- **Decision**: a tiny top-level `ThinkingIndicator` component in `page.tsx`,
  used in both the waiting and streaming spots.
- **Rationale**: the two spots render identical output — a shared component
  prevents drift; duplicating the JSX would fork the design.
- **Alternatives considered**: a shared component in `components/` — rejected
  (one consumer, two usages in one file; colocation is the house pattern).

## R2 — One row in both states

- **Decision**: the indicator renders as its own row
  (`flex items-center gap-2 pt-2.5`) — replacing the waiting dots block
  in place, and appearing below the content while streaming (replacing the
  inline caret).
- **Rationale**: the "Thinking" label is a row-level signal (Clarifications
  placement pin); a row works identically in both conditions.
- **Alternatives considered**: inline after the markdown (caret-style) —
  rejected (the label doesn't belong inline; the user's screenshot shows a
  row indicator).

## R3 — No vitest additions

- **Decision**: acceptance is the CDP matrix
  (contracts/thinking-indicator.md T1–T6); no unit tests.
- **Rationale**: a presentational component with no logic — no pure logic to
  cover (house convention; the 79 existing tests stay green).
- **Alternatives considered**: a render test asserting the component exists —
  rejected (tautological; adds a testing-library dependency for nothing).

## R4 — Locked a11y set

- **Decision**: `LoaderCircle` with `motion-safe:animate-spin` (static ring
  under reduced motion), `text-[#82D2F6]` (user's explicit color, no
  gradient), `aria-hidden="true"` on the icon, `role="status"` on the row —
  the bold text is the accessible signal.
- **Rationale**: the double-clarify's accessibility decisions (decorative
  ring + text-as-signal + reduced-motion gate).
- **Alternatives considered**: the gradient spinner from the first analysis —
  superseded by the user's explicit `#82D2F6` choice.

## Error handling (user-requested)

| Condition | Behavior |
|---|---|
| Error or abort mid-stream | indicator clears when `streaming` flips false — same lifecycle as the old caret (error text or demo fallback replaces it) |
| Whitespace first chunk | waiting block (`!m.text`) flips to the streaming branch seamlessly — same condition as before, one indicator throughout |
| 120 s watchdog abort | error text replaces the indicator (unchanged watchdog path) |
| Delete mid-stream | spec-015 active-delete switches to a fresh draft — the message (and its indicator) is gone |
| Reduced motion | static ring via `motion-safe:` gate (text still signals state) |
| Multiple messages | one stream at a time (single send path) — one indicator at most |
| Theme legibility | ring is decorative (`aria-hidden`); the bold "Thinking" text carries the accessible signal at full theme contrast |
