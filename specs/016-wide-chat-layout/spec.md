# Feature Specification: Wide Chat Layout

**Feature Branch**: `016-wide-chat-layout`

**Created**: 2026-10-21

**Status**: Draft

**Input**: User description: expand the chat column from its fixed
768px (`max-w-3xl`) reading width toward a wide layout (~90% of the
available content area) while keeping long-form text readable.

## Clarifications

### Session 2026-10-21

- Q: What maximum width should the chat column and composer use at desktop? → A: 1400px cap — `min(90%, 1400px)` of the content area, centered.
- Q: Should long user-message bubbles keep 85%-of-column width? → A: (defaulted to recommendation) add an absolute ceiling at desktop so long user messages never become full-width walls of text.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Wide message column and composer (Priority: P1)

At desktop viewports (≥1280px), the message column and the composer expand
to `min(90%, 1400px)` of the content area (viewport minus the sidebar when
open), staying centered. Below 1280px the layout is exactly what it is
today — no viewport ever gets a narrower column than the current design.

**Why this priority**: This is the entire feature; every other story guards
it.

**Independent Test**: At 1440×900 with the sidebar open, the message column
and composer each measure ≥85% of the 1184px content area (≈1066px); at
1920×1080 they measure exactly 1400px; at 1279px they measure no more than
today's 768px cap.

**Acceptance Scenarios**:

1. **Given** a ≥1280px viewport, **When** the chat renders, **Then** the
   message column and composer are `min(90%, 1400px)` wide, centered, and
   never wider than 1400px.
2. **Given** a <1280px viewport, **When** the chat renders, **Then** the
   layout is identical to today's (`max-w-3xl` behavior unchanged).
3. **Given** the sidebar open or closed, **When** the width is measured,
   **Then** the column tracks 90% of the *content area* (after the sidebar),
   not the raw viewport.
4. **Given** wide content (tables, code blocks, images), **When** rendered,
   **Then** it uses the wider column without horizontal overflow of the
   page.

---

### User Story 2 - Readable long user messages (Priority: P2)

User-message bubbles currently cap at 85% of the column; at 1400px that is
a ~1190px wall of text. Long user messages get an absolute ceiling so they
stay readable, while short messages remain visually compact.

**Why this priority**: Guards the readability the wide layout must not
destroy.

**Independent Test**: Send a ≥2000-character user message at 1440×900; its
bubble never exceeds the 672px absolute ceiling; a short message's bubble
stays at its natural compact width.

**Acceptance Scenarios**:

1. **Given** a long user message at a ≥1024px viewport, **When** rendered,
   **Then** the bubble width never exceeds 672px (`max-w-2xl`).
2. **Given** a short user message, **When** rendered, **Then** the bubble
   keeps its current compact behavior (no stretching to the ceiling).

---

### Edge Cases

- Viewports 1024–1279px: the wide class does not apply; today's `max-w-3xl`
  behavior is preserved (a global `min(90%,…)` would *narrow* the column
  here — measured: 691px vs 720px at 1024px — which is why the wide class is
  gated to ≥1280px).
- Mobile (<768px): no sidebar exists; the column keeps full width; the
  wide class never binds.
- Streaming replies: column width is static during streaming; no layout
  shift beyond what exists today.
- PDF export: structurally immune — it renders an off-screen 744px
  container (`lib/pdf-export/render.tsx`), never the live DOM, so exported
  output is byte-stable across this change.
- Empty-state suggestions grid: out of scope; stays `max-w-2xl`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: At ≥1280px viewports the message column and composer MUST be
  `min(90%, 1400px)` of the content area, centered, capped at 1400px.
- **FR-002**: Below 1280px the layout MUST be identical to the current
  `max-w-3xl` design (no viewport may get a narrower column than today).
- **FR-003**: Long user-message bubbles MUST NOT exceed 672px at ≥1024px
  viewports; short messages MUST remain compact.
- **FR-004**: The PDF export output MUST be unchanged by this feature
  (spec 013 regression guard).
- **FR-005**: Sidebar grouping, Load more, resume, and delete behaviors
  (specs 014/015) MUST remain green at the widened layout (regression
  guard).

### Key Entities

- None — layout-only change; no data model, state machine, or interface
  changes.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: At 1440×900 with sidebar open, the message column and
  composer each measure ≥85% of the 1184px content area (expected ≈1066px)
  and at 1920×1080 exactly 1400px (cap binds), measured via CDP.
- **SC-002**: At every viewport below 1280px the computed column width
  equals today's (spot-checked: 1279px, 1024px, 390px).
- **SC-003**: A ≥2000-character user message bubble measures ≤672px at
  1440×900.
- **SC-004**: PDF export of the same conversation before/after the change
  paginates identically (or, if no pre-change baseline exists, establishes
  one honestly and marks the comparison "baseline-established").
- **SC-005**: Spec 013/014/015 acceptance scenarios re-verified green at
  the widened layout; typecheck, lint, and the vitest suite stay green.

## Assumptions

- The 1400px cap is the readability guard, chosen over "pure 90%" because
  prose beyond ~75 characters per line degrades scanning; tables and code
  benefit from width (Session 2026-10-21 clarification).
- The bubble ceiling was defaulted from the recommendation (the user
  dismissed the question without an answer); removing it is a one-class
  revert if unwanted.
- The empty-state suggestions grid, sidebar internals, and mobile design
  are out of scope for v1.
- The header "…" placeholder button is a known adjacent defect, tracked
  separately — not part of this feature's acceptance.
