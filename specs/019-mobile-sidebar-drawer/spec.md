# Feature Specification: Mobile Sidebar Drawer

**Feature Branch**: `019-mobile-sidebar-drawer`

**Created**: 2026-10-22

**Status**: Draft

**Input**: User report: "on mobile I can chat but cannot expand/access the sidebar menu" — the sidebar is `hidden md:flex`, so below 768px it never renders and the toggle does nothing visible. This feature makes the sidebar available on mobile as an on-demand overlay drawer. **It supersedes spec 016's edge-case decision "Mobile (<768px): no sidebar exists"** — mobile now has the drawer, closed by default.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Open and close the sidebar on mobile (Priority: P1)

On a phone-width viewport, the sidebar toggle opens the sidebar as a
left-side overlay drawer over the chat content, with a dim backdrop behind
it. The drawer closes when the user taps the backdrop, presses Escape, taps
the toggle again, or picks a conversation / New chat inside it. On first
page load at phone width the drawer is closed (it must not cover the chat).

**Why this priority**: Mobile users currently have no way to reach
history, search, or delete — the entire sidebar feature surface is absent
below 768px.

**Independent Test**: At 390×844, the sidebar is hidden on load; tapping
the toggle shows it as a left overlay with a backdrop; tapping the
backdrop hides it again. Desktop (≥768px) behavior is unchanged.

**Acceptance Scenarios**:

1. **Given** a fresh page load at 390×844, **When** the page renders,
   **Then** the sidebar is not visible and the chat fills the viewport.
2. **Given** the drawer closed, **When** the user taps the sidebar toggle,
   **Then** the sidebar appears as a left overlay (~256px wide) with a dim
   backdrop covering the rest of the screen.
3. **Given** the drawer open, **When** the user taps the backdrop,
   **Then** the drawer closes and the chat is fully visible again.
4. **Given** the drawer open, **When** the user presses Escape or taps the
   toggle again, **Then** the drawer closes.
5. **Given** the drawer open, **When** the user taps a conversation row or
   "New chat", **Then** that action runs AND the drawer closes (mobile
   only).
6. **Given** a viewport ≥768px, **When** the sidebar is toggled,
   **Then** the behavior is exactly the current static sidebar (no
   overlay, no backdrop).

---

### Edge Cases

- Desktop → mobile resize while the drawer is open: the drawer stays in
  overlay form (state persists); it does not snap to the static layout
  until the viewport crosses 768px again.
- Initial open-then-close: on first mobile load the sidebar state starts
  open (desktop default) and a mount effect closes it on small screens —
  a brief overlay flash is acceptable for v1.
- Drawer content scrolls independently (long history lists) — the drawer
  is full-height with its own scroll.
- Search inside the drawer (spec 018) works on mobile exactly as on
  desktop.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Below 768px, the sidebar MUST be available as an on-demand
  left overlay drawer opened by the sidebar toggle.
- **FR-002**: The open drawer MUST show a dim backdrop over the rest of
  the screen; tapping the backdrop MUST close the drawer.
- **FR-003**: The drawer MUST close on Escape, on toggle tap, and after a
  conversation row or "New chat" is chosen (mobile only — desktop
  selection does not close the sidebar).
- **FR-004**: On first load below 768px the drawer MUST start closed.
- **FR-005**: At ≥768px the sidebar behavior MUST be unchanged from today
  (static column, toggle show/hide, no overlay/backdrop).
- **FR-006**: All existing sidebar features (history groups, Load more,
  delete, search — specs 014/015/018) MUST work inside the drawer exactly
  as on desktop.
- **FR-007**: No new dependencies; the drawer is built from the existing
  sidebar markup plus an overlay/backdrop (no drawer library).

### Key Entities

- None — presentational state (`sidebarOpen`) plus a mount-time viewport
  check.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: At 390×844, measured: sidebar hidden on load; after toggle,
  a left overlay of width ≈256px with a backdrop is visible; after
  backdrop tap, hidden again.
- **SC-002**: Drawer close paths verified: backdrop, Escape, toggle,
  row-select, New-chat-select — each closes the drawer at 390px.
- **SC-003**: At ≥768px the existing sidebar behavior and the spec 016
  layout matrix stay green (regression guard).
- **SC-004**: Spec 018 search works inside the drawer at 390px (type →
  rows filter).
- **SC-005**: No new dependencies; typecheck, lint, and the vitest suite
  stay green.

## Assumptions

- The sidebar toggle is the single entry point to the drawer on mobile
  (no swipe gesture in v1).
- A brief open-then-close flash on first mobile load is acceptable
  (state starts open for desktop, a mount effect closes it below 768px).
- The drawer reuses the exact existing sidebar content — no duplicated
  mobile-only sidebar copy.
- Spec 016's "no sidebar on mobile" edge case is amended by this spec;
  the persisted layout-acceptance script's mobile check is updated to
  assert "drawer closed on fresh mobile load" instead of "no sidebar".
