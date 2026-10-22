# Feature Specification: Sidebar Full-Text Search (Case-Insensitive)

**Feature Branch**: `018-sidebar-search`

**Created**: 2026-10-22

**Status**: Draft

**Input**: User description: "implement a Full Text Search with Case-Insensitive — based on the above chat conversation" (adopts the analyzed scope: wire the existing dead sidebar search input to case-insensitive filtering of conversation titles plus currently-loaded message text; title-only matching for unopened backend conversations, documented honestly; no backend changes).

## Clarifications

### Session 2026-10-22

- Q: How much of a conversation's history does content search cover? → A: Only messages currently loaded in the UI — opened conversations load up to the last 100 messages, so very long conversations are searched over their most recent 100; older messages fall outside the same documented boundary as unopened conversations (title-only).
- Q: Is the searchable corpus all conversations, including local drafts? → A: No — verified from source: the sidebar renders only backend history rows; local demo conversations and "New chat" drafts never appear in the sidebar. Content search therefore covers (a) titles of every sidebar row and (b) loaded message text of rows whose conversation was opened (or the active conversation once it has a backend row); the demo drafts are not in the searchable surface.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Find a conversation by its title (Priority: P1)

The sidebar search input — currently inert — filters the conversation list
as the user types, case-insensitively. Because backend conversation titles
are auto-derived from the first message, a title query behaves like a
content search for the conversation's topic. Groups with no matching rows
collapse; a query with no results shows an explicit empty state; a clear
control restores the full grouped list.

**Why this priority**: The find-that-conversation case is the entire point
of the search bar; it covers every backend conversation by title.

**Independent Test**: Type "BAR" in the search input; the sidebar shows
only conversations whose title contains "bar" (any case); clear the input
and the full grouped list returns.

**Acceptance Scenarios**:

1. **Given** conversations in the sidebar, **When** the user types a
   substring of a conversation's title in any case ("BAR", "bar", "Bar"),
   **Then** the list filters to matching conversations for every casing
   after a brief debounce.
2. **Given** a filtered list, **When** no title matches the query,
   **Then** an explicit "no conversations match" empty state appears
   instead of a blank sidebar.
3. **Given** a filtered or empty state, **When** the user clicks the clear
   control (×), **Then** the query resets and the full grouped list is
   restored immediately.
4. **Given** the search is active, **When** the user clicks a filtered
   row, **Then** that conversation opens exactly as it would unfiltered.

---

### User Story 2 - Find a loaded conversation by its message content (Priority: P2)

The same query also matches the message text of sidebar conversations
whose messages are currently loaded in the UI — the open conversation
and any backend conversation opened earlier in this session (whose
messages were fetched on open). Local demo conversations and "New chat"
drafts never appear in the sidebar, so they are not in the searchable
surface at all. Unopened backend conversations match on title only — the
UI does not claim otherwise.

**Why this priority**: Extends search from titles to actual content where
content is honestly available, without pretending full coverage.

**Independent Test**: Open a conversation whose assistant reply contains
a word not in its title (e.g. "quadrant"); search that word; the
conversation remains visible in the filtered list.

**Acceptance Scenarios**:

1. **Given** a conversation with loaded messages, **When** the user
   searches a word that appears in a message but not in the title,
   **Then** the conversation matches and stays visible.
2. **Given** a word that exists only in an unopened backend
   conversation's body, **When** the user searches it, **Then** that
   conversation does NOT match (title-only for unopened) — the documented
   limitation, not a bug.

---

### Edge Cases

- Query of only whitespace → treated as empty (full list restored).
- Query with special characters or emoji → literal substring matching,
  no regex interpretation, no crash.
- Load more while a search is active → newly loaded page rows are also
  filtered by the active query (only matches appear).
- Delete a conversation while search is active → the filtered list
  updates without leaving a ghost row.
- Opening a conversation while search is active → the search stays active
  and the row was clicked from the filtered list (state unchanged).
- The "no conversations match" empty state appears only once history has
  finished loading — during loading skeleton or error states, those
  states take precedence.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The sidebar search input MUST filter the conversation list
  as the user types, using case-insensitive substring matching.
- **FR-002**: Matching MUST cover every loaded backend conversation's
  title (every row shown in the sidebar).
- **FR-003**: Matching MUST ALSO cover the message text of sidebar
  conversations whose messages are currently loaded in the UI (the open
  conversation and backend conversations opened earlier in this session;
  the local demo conversations and "New chat" drafts never appear in the
  sidebar and are not part of the searchable surface).
- **FR-004**: The grouped list MUST show only matching rows, hiding
  entire recency groups that contain no matches.
- **FR-005**: A query with zero matches MUST render an explicit empty
  state (e.g. "No conversations match ‹query›"), never a blank sidebar.
- **FR-006**: A clear control MUST reset the query and restore the full
  grouped list in one action.
- **FR-007**: Filtering MUST be debounced (not applied on every
  keystroke) so typing stays smooth.
- **FR-008**: Search MUST be a client-side, session-local behavior: no
  backend/API changes, no persistence, no new dependencies.
- **FR-009**: The UI MUST NOT claim full-text coverage it does not have —
  unopened backend conversations match on title only (documented
  limitation, no misleading "searches everything" affordance).
- **FR-010**: Existing sidebar behaviors (recency buckets, Load more,
  resume-on-click, delete flow) MUST remain intact while search is active
  and after clearing (regression guard, specs 014/015).

### Key Entities

- None — a client-side filter over existing conversation records; no new
  data model, persistence, or state machine.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Typing a query filters the sidebar to matching
  conversations within 1 second of input settling (no perceptible stall
  on a 100-row list).
- **SC-002**: Case-insensitivity verified: "BAR", "bar", and "Bar"
  produce identical result sets.
- **SC-003**: A query matching only a loaded conversation's message body
  (not its title) surfaces that conversation.
- **SC-004**: Zero-match queries show the explicit empty state; one
  clear action restores the full list.
- **SC-005**: Change scope contains no backend/API edits and no new
  dependencies (verifiable by change scope).
- **SC-006**: Spec 014/015 sidebar acceptance behaviors (buckets, Load
  more, delete, resume) re-verified green with search present.

## Assumptions

- The title-only limitation for unopened backend conversations is
  accepted for v1 (a true body search needs a search proxy paging through
  Dify — out of scope, possible v2).
- Results are filtered rows only — no match highlighting, no
  scroll-to-match (v1).
- Filtering activates from the first typed character (it's cheap
  client-side); debounce ≈200 ms.
- The existing placeholder text ("Search chats") is kept; a × clear
  control appears only when the query is non-empty.
- Opened conversations load up to the last 100 messages into the UI —
  content search covers exactly those loaded messages; older messages in
  longer conversations are outside scope (same honesty boundary as the
  title-only rule).
- Case-insensitivity uses Unicode-lowercase comparison (covers the
  observed title languages).
- Escape also clears the query (standard behavior); the × control and
  Escape are equivalent.
