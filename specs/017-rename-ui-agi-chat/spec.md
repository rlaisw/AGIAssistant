# Feature Specification: Rename UI Skin to AGI Chat

**Feature Branch**: `017-rename-ui-agi-chat`

**Created**: 2026-10-22

**Status**: Draft

**Input**: User description: "rename AgenticRAG and AI Chat ONLY in UI skin — change AI Chat to 'AGI Chat', DO NOT CHANGE the backend system's real name; ONLY change 'AgenticRAG' to 'AGI Chat' in the UI skin."

## Clarifications

### Session 2026-10-22

- Q: Does the seven-location set cover every user-visible surface? → A: Initially believed yes; bounded re-verification found an eighth location — the PDF export's metadata line (`lib/pdf-export/render.tsx`, "… · AgenticRAG Chat"). The set is now eight and confirmed complete across `app/`, `components/`, `lib/`, and `public/` (no Next.js error pages exist; no other component or lib file carries the names).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Consistent "AGI Chat" branding across the chat UI (Priority: P1)

Every user-visible label in the Chat UI that currently reads "AgenticRAG"
or "AI Chat" reads "AGI Chat" instead: the sidebar brand, the header badge,
the label under each assistant message, the composer input placeholder, the
composer's model label, the footer disclaimer, and the browser tab title.
The backend system's real name (the Dify chatflow "Chatflow Basic
(AgenticRAG Agent)", the MCP server, and all repo documentation) is NOT
changed — this is a UI-skin rename only.

**Why this priority**: This is the entire feature — one cohesive renaming
pass with a hard scope boundary.

**Independent Test**: Open the chat UI and inspect the sidebar, header,
a conversation with assistant replies, the composer, and the browser tab —
every one shows "AGI Chat"; no "AgenticRAG" or "AI Chat" text remains
anywhere in the rendered page.

**Acceptance Scenarios**:

1. **Given** the chat UI loads, **When** the user looks at the sidebar
   brand (top-left), **Then** it reads "AGI Chat".
2. **Given** the chat UI loads, **When** the user looks at the header
   badge (top-right), **Then** it reads "AGI Chat".
3. **Given** a conversation with at least one assistant reply, **When**
   the user reads the label under a reply, **Then** it reads "AGI Chat".
4. **Given** the composer, **When** the user reads the input placeholder
   and the label beside the send button, **Then** they read "Message AGI
   Chat…" and "AGI Chat".
5. **Given** the footer below the composer, **When** the user reads the
   disclaimer, **Then** it reads "AGI Chat can make mistakes…".
6. **Given** any page, **When** the user looks at the browser tab title,
   **Then** it starts with "AGI Chat".
7. **Given** the completed rename, **When** the backend artifacts are
   inspected, **Then** the Dify chatflow name, MCP server naming, and repo
   documentation are byte-identical to before (backend name untouched).
8. **Given** a conversation with replies, **When** the user exports the
   conversation PDF, **Then** the exported document's metadata line reads
   "Exported … · AGI Chat" (no "AgenticRAG Chat").

---

### Edge Cases

- Assistant footer appears once per reply — verify on a conversation with
  replies, not just the empty state.
- The disclaimer and placeholder contain the name mid-sentence — only the
  name changes, surrounding text is preserved exactly.
- The exported PDF carries the brand in its metadata line — generated
  documents are user-visible output and are in scope (location 8).
- No other name variants exist in the UI (verified by bounded enumeration
  across app/, components/, lib/, public/: eight locations, all listed in
  Acceptance Scenarios 1–6 and 8).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The sidebar brand text MUST read "AGI Chat".
- **FR-002**: The header badge text MUST read "AGI Chat".
- **FR-003**: The label under each assistant message MUST read "AGI Chat".
- **FR-004**: The composer input placeholder MUST read "Message AGI Chat…".
- **FR-005**: The composer model label beside the send button MUST read
  "AGI Chat".
- **FR-006**: The footer disclaimer MUST read "AGI Chat can make mistakes.
  Check important info."
- **FR-007**: The browser tab title MUST begin with "AGI Chat".
- **FR-008**: No user-visible text in the chat UI MAY contain "AgenticRAG"
  or "AI Chat" after the rename (the eight locations — seven in the live
  page, one in exported PDFs — are the complete enumerated set).
- **FR-009**: The backend system's real name MUST NOT change: the Dify
  chatflow name, MCP server/tooling names, and repo documentation
  (README/DEPLOY/NETWORK/specs/tests) stay byte-identical; the change
  surface is limited to the Chat UI's rendered strings (and one accuracy
  touch-up in the Chat UI's own README describing the badge text).
- **FR-010**: The exported PDF's metadata line MUST read "Exported
  <timestamp> · AGI Chat" (replacing "… · AgenticRAG Chat").

### Key Entities

- None — static UI strings; no data model, state machine, or persistence.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 0 occurrences of "AgenticRAG" or "AI Chat" remain in any
  user-visible text of the chat UI, verified by inspecting the rendered
  page (sidebar, header, assistant messages, composer, footer, tab title)
  and the exported PDF's metadata line.
- **SC-002**: 0 changes outside the Chat UI surface — backend name-bearing
  artifacts (chatflow name, server, repo docs) are untouched, verifiable by
  change scope.
- **SC-003**: All existing quality gates stay green (typecheck, lint,
  unit tests) and the rendered result matches the acceptance scenarios when
  inspected.

## Assumptions

- All eight enumerated locations are in scope (sidebar brand, header
  badge, assistant footer, placeholder, composer label, footer disclaimer,
  tab title, and the exported-PDF metadata line — the eighth was added
  after bounded re-verification found it outside `app/`).
- "AGI Chat" is the exact replacement string in every location, including
  inside the placeholder and disclaimer sentences.
- The backend system name "AgenticRAG" is intentionally retained
  everywhere outside the UI skin; users who encounter it in docs or the
  Dify console see the real product name — that is accepted.
- One accuracy touch-up in the Chat UI's own README (the line describing
  the badge text) accompanies the rename so the doc matches the new UI.
