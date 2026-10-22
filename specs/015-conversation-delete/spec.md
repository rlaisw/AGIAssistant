# Feature Specification: Delete Conversation

**Feature Branch**: `015-conversation-delete`

**Created**: 2026-10-21

**Status**: Draft

**Input**: User description: "Add new feature: enable: (option-1) 'Right-Click' the AI Chat to delete (option-2) your suggestion!?"

**Interaction decision (user's option-2)**: right-click was rejected — it hijacks the
browser context menu and is undiscoverable. The chosen interaction is a visible
per-conversation "…" affordance with a Delete menu item plus a confirmation step,
matching the app's existing dropdown-menu patterns and standard chat-UI
conventions.

## Clarifications

### Session 2026-10-21

- Q: The "…" menu could contain just Delete, or Delete plus Rename — which should v1 include? → A: Delete only in v1; the menu structure accommodates Rename as a future sibling without redesign.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Delete a conversation from the sidebar (Priority: P1)

The user hovers or focuses a conversation in the grouped sidebar; a small "…"
icon appears on the row. Clicking it opens a menu containing **Delete**.
Choosing Delete asks for confirmation ("Delete this chat? This cannot be
undone."); confirming removes the conversation from the sidebar immediately and
deletes it from the chat backend so it never returns after reload.

**Why this priority**: This is the entire feature.

**Independent Test**: Create two throwaway conversations; delete one via the
"…" menu; it disappears instantly, the other remains, and a reload does not
resurrect the deleted one.

**Acceptance Scenarios**:

1. **Given** a conversation under any time bucket, **When** the user hovers
   its row and clicks the "…" icon, **Then** a menu opens with a clearly
   destructive-labeled Delete item.
2. **Given** the Delete menu item, **When** the user clicks it, **Then** a
   confirmation appears before anything is deleted.
3. **Given** a confirmed delete, **When** the backend call completes,
   **Then** the row disappears from every bucket immediately — no reload,
   no stale entry.
4. **Given** a confirmed delete, **When** the user later reloads the app,
   **Then** the conversation is still gone (deleted on the backend, not
   hidden locally).

---

### User Story 2 - Safe state transitions (Priority: P2)

Deleting the conversation that is currently open in the chat pane switches
the pane to a fresh draft chat (never a dangling reference to deleted
messages). Cancelling the confirmation leaves everything untouched. A delete
failure keeps the row and tells the user honestly.

**Why this priority**: Guarding against broken UI states after deletion is
what makes the feature trustworthy rather than just present.

**Independent Test**: Open conversation A, delete A via the sidebar; the chat
pane becomes a new empty draft. Delete conversation B and cancel; B is still
there and still opens.

**Acceptance Scenarios**:

1. **Given** the open conversation in the chat pane, **When** it is deleted,
   **Then** the pane switches to a new empty draft chat with the sidebar's
   "New chat" behavior.
2. **Given** the confirmation dialog, **When** the user cancels, **Then** the
   conversation remains and the menu closes with no state change.
3. **Given** a backend delete failure, **When** the user confirms, **Then**
   the row stays in the sidebar and an honest error is shown; nothing is
   removed locally (Constitution IV).

---

### Edge Cases

- What about deleting the last remaining conversation? → The sidebar shows
  the same empty state as a fresh install; "New chat" remains available.
- What about the "…" on the active conversation row? → Available (deleting
  the active chat is supported, US2/AC1).
- What about a delete racing a resume click? → The menu closes on row
  removal; the delete wins and the pane falls back per US2/AC1.
- What about keyboard users? → The "…" icon is focusable and opens the menu
  with Enter; Delete and the confirmation are reachable by keyboard.
- What about double-clicking Delete in the confirmation? → The action is
  disabled while the delete request is in flight.
- What about deleting the active conversation while a reply is still
  streaming? → The delete aborts the in-flight stream (the same abort
  mechanism the chat already uses) before switching the pane to a fresh
  draft; no stream writes land in the deleted conversation.
- What about another browser tab showing a conversation deleted here? → The
  next action on it fails with the backend's not-found and surfaces the
  per-action honest error (spec 014's pattern); no silent breakage.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Each conversation row in the grouped sidebar MUST show a "…"
  affordance on hover/focus that opens a menu containing a Delete item.
- **FR-002**: Choosing Delete MUST show a confirmation before any deletion;
  cancel is the default-safe path (no data changes on cancel).
- **FR-003**: Confirming MUST delete the conversation on the chat backend
  (not merely hide it locally) and remove the row from the sidebar
  immediately.
- **FR-004**: Deleting the currently-open conversation MUST switch the chat
  pane to a new empty draft (US2/AC1).
- **FR-005**: A failed backend delete MUST keep the row and surface an
  honest error; no local-only removal (Constitution IV).
- **FR-006**: The delete action MUST be disabled while its request is in
  flight (no double-submits).
- **FR-007**: The "…" affordance and menu MUST be keyboard-accessible
  (focusable, Enter-to-open, arrow/Enter in menu).
- **FR-008**: Drafts (never-sent "New chat" state) MUST NOT offer Delete —
  there is nothing on the backend to delete (spec 014 FR-014 lifecycle); they
  are discarded by simply starting another chat.

### Key Entities

- **ConversationRecord** (spec 014): the row being deleted; deletion removes
  it from the sidebar store and the backend in one action.
- **Delete action state**: idle → confirming → in-flight → (done | failed);
  drives confirmation visibility, button disable, and error display.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of confirmed deletes remove the conversation from the
  sidebar within one user-perceptible step and keep it gone after reload on
  a 10-conversation fixture.
- **SC-002**: 0 dangling references — deleting the active conversation always
  leaves a usable empty draft chat pane (verified over every conversation in
  the fixture).
- **SC-003**: All grouping behaviors from spec 014 (buckets, Load more,
  resume, draft promotion) remain green after a delete — the feature adds
  removal without regressing any spec-014 acceptance scenario.
- **SC-004**: The delete path (including confirmation, in-flight guard, and
  failure notice) is testable without a live backend (fetch seams stubbed).

## Assumptions

- The interaction is option-2 (hover "…" menu + confirmation); option-1
  (right-click) is rejected because it hijacks the browser context menu and
  is undiscoverable; recorded here so the decision is traceable.
- The chat backend can delete conversations by id (verified: the service API
  exposes conversation deletion); the proxy pattern from specs 014 applies
  unchanged (key stays server-side).
- Delete is permanent — no trash/undo in v1; the confirmation copy says so
  honestly ("This cannot be undone").
- v1 deletes one conversation at a time; bulk delete, rename, and archive are
  out of scope — the menu carries only Delete in v1 and is structured so
  Rename can be added later as a sibling item (per Clarification 2026-10-21).
- Deletion only affects the shared single-tenant history (same posture as
  spec 014 — the app has one user identity).
