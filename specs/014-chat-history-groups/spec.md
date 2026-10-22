# Feature Specification: Time-Grouped Chat History

**Feature Branch**: `014-chat-history-groups`

**Created**: 2026-10-21

**Status**: Draft

**Input**: User description: "i want to add chat history (Today, Yesterday, Previous 7 days, Last month, Few months ago) like this uploaded image" (reference image unreadable — grouping buckets taken from the text description)

## Clarifications

### Session 2026-10-21

- Q: Should the conversation list survive a page reload — fetched from the chat backend when the app opens — or is it enough to group only the conversations started in the current browser session? → A: Backend-backed: sidebar populates from the chat backend on app open; conversations survive reloads and browser restarts.
- Q: If the chat backend holds more conversations than it returns in a single response page, how far should the sidebar go to show them? → A: Show the first page instantly; a "Load more" control at the list's end fetches the next page each time it is used.
- Q: Should a brand-new chat appear in the grouped history before its first message is sent, or only after? → A: Only after the first message is sent; before that it is a session-only draft.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Sidebar shows conversations grouped by time (Priority: P1)

The chat sidebar lists the user's past conversations under recency headings
— **Today**, **Yesterday**, **Previous 7 days**, **Last month**, **Few
months ago** — with each conversation appearing under exactly one heading
based on when it was last active. Headings with no conversations are hidden
rather than shown empty. The "New chat" action stays above the groups.

**Why this priority**: The grouping IS the feature — without it nothing
else matters.

**Independent Test**: Open the chat with conversations of varying ages;
each appears under the correct heading, empty headings are absent, and the
order within a group is most-recent-first.

**Acceptance Scenarios**:

1. **Given** conversations last active at different times (this morning,
   yesterday, 3 days ago, 3 weeks ago, 2 months ago), **When** the sidebar
   renders, **Then** each appears under exactly one heading (Today /
   Yesterday / Previous 7 days / Last month / Few months ago).
2. **Given** no conversation was active yesterday, **When** the sidebar
   renders, **Then** no empty "Yesterday" heading appears.
3. **Given** two conversations in the same heading, **When** the sidebar
   renders, **Then** the more recently active one is listed first.

---

### User Story 2 - Resume a past conversation from the sidebar (Priority: P2)

Clicking a conversation in any group loads it into the chat pane with its
message history, and continuing the conversation appends to it (not to a new
session).

**Why this priority**: A grouped list without resume is decoration; resume
makes the history useful.

**Independent Test**: Click a conversation under "Previous 7 days"; its
messages appear; send a follow-up; the reply continues that conversation and
it moves to "Today".

**Acceptance Scenarios**:

1. **Given** a conversation under "Last month", **When** the user clicks it,
   **Then** its full message history loads in the chat pane.
2. **Given** a resumed conversation, **When** the user sends a new message,
   **Then** the reply arrives in that same conversation and the sidebar entry
   moves to "Today".

---

### User Story 3 - Groups stay current without manual refresh (Priority: P3)

Starting a new chat, sending a message, or resuming an old conversation
updates the grouping immediately — a conversation from "Few months ago" that
receives a new message lands under "Today" right away.

**Why this priority**: Stale grouping erodes trust in the whole list, but
it is a refinement over the static structure.

**Independent Test**: Resume a "Few months ago" conversation and send one
message; its sidebar entry moves to "Today" without reloading the page.

**Acceptance Scenarios**:

1. **Given** a conversation under "Few months ago", **When** the user sends
   a message in it, **Then** the entry re-groups under "Today" immediately.

---

### Edge Cases

- What about conversations older than "Few months ago"? → They remain under
  "Few months ago" (the last bucket is a floor, not a window).
- What about a conversation active at 00:01 and it is now 23:59 the same
  day? → Still "Today"; buckets are computed in the user's local time from
  last-activity timestamps.
- What about a conversation with no readable timestamp? → It is grouped
  under the oldest-safe bucket with a console warning, never dropped
  silently (Constitution IV).
- What if the backend cannot provide history (offline / demo mode)? → The
  sidebar shows an honest inline notice; canned demo conversations may be
  shown pre-grouped and marked as sample data.
- What about many conversations in one bucket? → The sidebar list scrolls
  within its existing layout; the backend list is paged and the visible set
  grows only via the explicit "Load more" control (FR-013) — nothing is
  silently invisible.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The sidebar MUST group conversations into the buckets Today,
  Yesterday, Previous 7 days, Last month, Few months ago — each
  conversation under exactly one bucket, computed from its last-activity
  time in the user's local time.
- **FR-002**: Buckets MUST be defined as: Today = since local midnight;
  Yesterday = the previous local calendar day; Previous 7 days = the 7
  calendar days before yesterday (inclusive); Last month = the 30 days
  before that; Few months ago = everything older.
- **FR-003**: Empty buckets MUST NOT render (no empty headings).
- **FR-004**: Within a bucket, conversations MUST be ordered most-recently-
  active first.
- **FR-005**: Clicking a conversation MUST load its message history into
  the chat pane and route subsequent messages to that conversation.
- **FR-006**: A conversation's last-activity time MUST update when the user
  sends or resumes it, and the sidebar MUST re-group immediately without a
  page reload.
- **FR-007**: Conversations older than the Last month window MUST remain
  under Few months ago (floor bucket, never dropped).
- **FR-011**: The conversation list MUST be fetched from the chat backend
  when the app opens; history survives page reloads and browser restarts
  (per Clarification 2026-10-21). Until the fetch completes the sidebar
  shows a loading state; on failure it shows the FR-008 notice and remains
  usable for new chats.
- **FR-008**: When conversation history is unavailable from the chat backend,
  the sidebar MUST show an honest notice (never a fabricated or silently
  empty list); demo/sample data, if shown, MUST be visibly marked.
- **FR-009**: The existing "New chat" action MUST remain directly accessible
  above the groups.
- **FR-010**: Bucketing MUST NOT depend on the conversation's title or
  content — only its last-activity timestamp.
- **FR-012**: Conversation titles MUST come from the chat backend's stored
  name when available; when absent, the sidebar derives a readable fallback
  from the conversation's first user question (capped), never "Untitled".
- **FR-013**: When the backend returns conversations in pages, the sidebar
  MUST show the first page immediately; a visible "Load more" control at
  the end of the list MUST fetch the next page on each use, and MUST be
  absent when no further pages remain (per Clarification 2026-10-21).
  Conversations beyond unfetched pages MUST NOT be silently invisible —
  the control's presence is the honest signal that more exist.
- **FR-014**: A conversation MUST appear in the grouped history only after
  its first message is sent; before that it exists only as a session-only
  draft and never reaches the backend or the buckets (per Clarification
  2026-10-21).

### Key Entities

- **Conversation**: id, title, last-activity timestamp; the timestamp is
  the single grouping input (FR-010).
- **Time bucket**: one of five fixed labels (Today / Yesterday / Previous
  7 days / Last month / Few months ago), each mapping to a local-time
  date range (FR-002); the last is open-ended downward.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of conversations with known timestamps appear under the
  correct bucket in a 20-conversation fixture spanning all five buckets.
- **SC-002**: A resumed conversation moves to "Today" within one
  user-perceptible step (no page reload) in at least 9 of 10 test attempts.
- **SC-003**: Sidebar grouping adds no visible delay: conversation list
  renders within 1 second of data availability on a typical laptop.
- **SC-004**: All grouping logic is testable without a live chat backend
  (fixtures with synthetic timestamps cover every bucket and boundary).

## Assumptions

- Buckets use the **user's local time** and conversation **last-activity**
  (most recent message), not creation time.
- The chat backend can provide each conversation's last-activity timestamp;
  if it cannot, FR-008's honest-notice path applies.
- v1 reuses the existing sidebar layout and conversation-switching
  behavior; visual redesign is out of scope.
- Search-within-history, pinning, renaming, and deleting conversations are
  out of scope for v1 (the sidebar's existing affordances stay as they are).
- One deterministic grouping pass at render plus an immediate re-group on
  activity (FR-006); no background polling in v1.