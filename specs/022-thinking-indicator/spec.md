# Feature Specification: "Thinking" Assistant Indicator

**Feature Branch**: `022-thinking-indicator`

**Created**: 2026-10-23

**Status**: Draft

**Input**: User description: "change animated icon to 'LoaderCircle with animate-spin in #82D2F6 (no gradient)' + 'Thinking' TEXT" — replace the assistant's two in-progress indicators (three gray pulsing dots while waiting for the first chunk, and the gray streaming caret after text starts) with one unified indicator: a spinning ring in light sky blue (`#82D2F6`) plus bold "Thinking" text. Decisions locked in the preceding conversation: unify both states into one indicator; use the lucide `LoaderCircle` icon with `animate-spin` (house icon library, zero new dependencies); color `#82D2F6` with no gradient; bold text.

## Clarifications

### Session 2026-10-23

- Q: Is `#82D2F6` on light backgrounds a contrast concern? → A: the ring is decorative — the bold "Thinking" text carries the accessible signal at full theme contrast; the ring's low luminance contrast on white is acceptable for a decorative accent (user's explicit color choice).
- Q: Should the spin respect reduced-motion settings? → A: yes — use `motion-safe:animate-spin`; reduced-motion users get a static ring (the "Thinking" text still signals state). One-word gate, better than today's pulses which ignore the setting.
- Q: How is the icon exposed to assistive tech? → A: the ring is decorative (`aria-hidden="true"`); the "Thinking" text announces itself as real content — no extra ARIA needed.
- Placement (from the developer perspective): one row in both states — below the streaming content while text arrives, and in place of the three waiting dots before the first chunk.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See a unified "Thinking" indicator while the assistant works (Priority: P1)

Whenever an assistant reply is in progress — waiting for the first chunk
or streaming text — the user sees a single indicator: a rotating light-sky-blue
ring next to the bold word "Thinking", in place of today's three gray dots
and gray vertical bar. The indicator stops and disappears the moment the
reply completes (or errors/aborts), and the message footer appears as usual.

**Why this priority**: it is the entire feature — one clear, branded
in-progress signal instead of two plain gray ones.

**Independent Test**: send a message; while the reply generates, the blue
ring + "Thinking" are visible; when the reply completes, both are gone.

**Acceptance Scenarios**:

1. **Given** a message sent, **When** the assistant has not produced the
   first chunk, **Then** the blue ring + "Thinking" show (replacing the
   three gray dots).
2. **Given** the reply streaming, **When** text is arriving, **Then** the
   blue ring + "Thinking" show (replacing the gray caret).
3. **Given** the reply completes, **When** it finishes, **Then** the
   indicator disappears and the message footer shows (no lingering
   indicator).
4. **Given** either theme, **When** the indicator shows, **Then** the
   ring is colored `#82D2F6` and the text is bold.

---

### Edge Cases

- Error or abort mid-stream: the indicator clears exactly as today's
  indicators do (message state flips to non-streaming; error text or the
  demo fallback replaces the indicator) — lifecycle unchanged.
- Multiple messages: the indicator renders per-message while that message
  streams (only one message streams at a time in this app).
- Dark and light themes: `#82D2F6` is legible on both; the "Thinking"
  text uses the theme default color.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: While an assistant message is being generated (waiting for
  the first chunk OR streaming), a single indicator MUST be shown: a
  rotating ring icon plus the bold text "Thinking".
- **FR-002**: The ring MUST be the lucide `LoaderCircle` icon with a
  continuous spin animation, colored `#82D2F6` (light sky blue), with no
  gradient; the text MUST be bold.
- **FR-003**: The indicator MUST disappear exactly when generation ends
  (reply complete, error, or abort) — no lingering or double indicators.
- **FR-004**: The two previous indicators (three gray pulsing dots and
  the gray streaming caret) MUST be fully replaced — no dead indicator
  code remains.
- **FR-005**: No new dependencies; no backend/API changes.

### Key Entities

- None — a presentational indicator tied to the existing message
  `streaming` state.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Rendered check mid-generation: a rotating ring (color
  computed as `#82D2F6`) and the text "Thinking" are present, and no gray
  dots/bar remain.
- **SC-002**: On reply completion, the indicator is absent and the
  message footer shows — verified via a live throwaway send (created and
  deleted after).
- **SC-003**: Zero remaining references to the old indicators in the app
  source (grep for the dot-pulse spans and the caret span); typecheck,
  lint, and the vitest suite (79) stay green.

## Assumptions

- Both states (waiting + streaming) unify into the one indicator (accepted
  default from the analysis).
- The lucide `LoaderCircle` icon (already installed, house icon library)
  with Tailwind's `animate-spin`; color via `text-[#82D2F6]` (no
  gradient, per the user's explicit choice).
- The "Thinking" text is bold, body-size, theme-default color; it sits
  inline in the assistant message area where today's indicators live.
- The indicator's lifecycle follows the existing `streaming` flag — no
  new state machinery.
- The spin animation is gated on `motion-safe:` — reduced-motion users
  see a static ring (the bold text still signals state).
- The icon is decorative (`aria-hidden="true"`); the bold "Thinking"
  text is the accessible signal and announces itself.
