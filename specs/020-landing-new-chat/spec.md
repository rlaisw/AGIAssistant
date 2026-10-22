# Feature Specification: Landing Page Starts on "New Chat"

**Feature Branch**: `020-landing-new-chat`

**Created**: 2026-10-22

**Status**: Draft

**Input**: User description: "set the first landing page of AGI Chat UI to 'New Chat'" (with a screenshot of the desired state: header title "New chat", the "How can I help you today?" empty state with suggestions). Today the app initializes into the first demo conversation ("Q3 roadmap draft" with pre-filled demo messages); the user wants the first screen to be a fresh, empty "New chat" draft instead.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - First load opens a fresh "New chat" draft (Priority: P1)

On every fresh page load — desktop, phone, remote or local, with or
without backend history — the app's first screen is a fresh, empty "New
chat" conversation: the header title reads "New chat" and the content
area shows the "How can I help you today?" empty state with the four
suggestion cards. No demo/pre-filled conversation content appears by
default. The demo conversation fixtures that used to provide the initial
content are removed (they would otherwise be unreachable dead data); the
demo-reply fallback used when Dify is unavailable is unaffected.

**Why this priority**: It is the entire feature — the app's first
impression should be a clean starting point, not a sample thread.

**Independent Test**: Load the app in a fresh tab (any viewport); the
header shows "New chat" and the empty state with suggestions; no
pre-existing messages. Send a message; it behaves exactly like a send
from any new chat (creates the conversation, adds the sidebar row,
streams the reply).

**Acceptance Scenarios**:

1. **Given** a fresh page load, **When** the app renders, **Then** the
   header title reads "New chat" and the content shows the empty state
   with suggestion cards and no messages.
2. **Given** the initial draft, **When** the user sends a message (or
   clicks a suggestion), **Then** the send behaves exactly like today's
   "New chat" send (conversation created, sidebar row added on first
   response, reply streams).
3. **Given** the codebase, **When** searched for the demo fixtures
   ("Q3 roadmap draft" and its siblings), **Then** none remain; the
   demo-reply fallback (canned replies when Dify is down) still works.
4. **Given** an opened history conversation, **When** the user reloads,
   **Then** the app again lands on a fresh "New chat" draft (consistent
   with today's no-local-persistence behavior; history is re-opened from
   the sidebar).

---

### Edge Cases

- No backend history at all → same fresh draft, same empty state.
- Reload mid-draft → reload always returns to a fresh draft (unchanged
  from today: local drafts never persisted; backend conversations are
  re-opened from the sidebar).
- The initial draft uses the same shape as "New chat" drafts created by
  the New chat button (same id counter family, no collisions).
- PDF export on the empty initial draft stays disabled (no messages) —
  existing behavior.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The app's initial active conversation on every fresh load
  MUST be an empty "New chat" draft (header title "New chat", zero
  messages, empty state with suggestions).
- **FR-002**: The demo conversation fixtures (the pre-filled sample
  threads) MUST be removed — they are unreachable once nothing opens on
  them (no dead data; Constitution V).
- **FR-003**: The demo-reply fallback (canned streaming replies when the
  backend is unreachable) MUST continue to work in any conversation,
  including the initial draft.
- **FR-004**: All other behaviors MUST be unchanged: sending from the
  draft, sidebar history/search/delete (014/015/018), wide layout (016),
  PDF export (013), mobile drawer (019), and the demo mode when no API
  key is set.

### Key Entities

- None — an initialization change to existing state; no new data model.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A fresh load at any viewport shows header title "New chat"
  and the empty-state prompt with 0 pre-existing messages (rendered
  check).
- **SC-002**: The first send from the initial draft creates the
  conversation and adds its sidebar row, verified end-to-end (reuse the
  throwaway flow).
- **SC-003**: Zero remaining occurrences of the demo fixture titles
  ("Q3 roadmap draft" etc.) in the app source; the demo-reply fallback
  still streams on a failed send.
- **SC-004**: Typecheck, lint, and the vitest suite (79) stay green; the
  sidebar search, delete, Load more, wide-layout matrix, and drawer
  checks are unaffected (regression scope: rerun the standing CDP
  checks).

## Assumptions

- The demo fixtures are removed rather than kept-but-hidden — once the
  app no longer opens on one, there is no path to view them, so they
  would be dead data (if you actually want them kept for some demo
  purpose, that's a one-line revert).
- "First landing page" means the initial state on every fresh load
  (desktop and mobile, local and remote) — no per-user persistence of the
  last conversation is added (that's a separate possible feature).
- The initial draft is indistinguishable from a draft created by the
  "New chat" button (same shape/id family).
