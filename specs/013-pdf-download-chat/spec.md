# Feature Specification: PDF Download of Chat Conversations

**Feature Branch**: `013-pdf-download-chat`

**Created**: 2026-10-21

**Status**: Draft

**Input**: User description: "i want to add a new function (PDF Download). The "PDF Download" function provide a download icon, User can download the chat conversation to PDF file."

## Clarifications

### Session 2026-10-21

- Q: Should the PDF export include the assistant's reasoning/trace metadata (decision routing, provenance badges, reflection records) that the UI shows in its reasoning panel, or only the visible chat text (questions and answers)? → A: Visible chat text plus citations/sources (links), but not internal routing/reflection metadata.
- Q: When an answer contains images (e.g., research results with `[image: URL]` markers or chart images), should the PDF show the actual embedded images, or just labeled links to them? → A: Embed actual images (fetched client-side); any image that fails to fetch degrades to its labeled link, never a blank box or broken icon.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Download the current conversation as PDF (Priority: P1)

A user who has been chatting with the assistant — questions, answers, and any
rendered artifacts (tables, images, deck action bars) — clicks a **PDF download
icon** in the chat header. The browser downloads a single PDF file that
faithfully reproduces the conversation: each user question followed by the
assistant's answer, in chronological order, readable on any PDF viewer.

**Why this priority**: This is the entire feature. Every other story is
polish or edge handling; without this, nothing ships.

**Independent Test**: Open a chat with at least 3 question/answer pairs
(including one answer with a table and one with a deck action bar), click the
PDF icon, open the downloaded file — the full conversation is present, ordered,
and readable.

**Acceptance Scenarios**:

1. **Given** a conversation with ≥ 3 turns, **When** the user clicks the PDF
   download icon, **Then** a PDF file downloads via the browser and opens in a
   standard PDF viewer showing every turn in chronological order.
2. **Given** an answer containing a markdown table, **When** the PDF is
   generated, **Then** the table renders as a grid (not raw pipe characters).
3. **Given** an answer containing a deck action bar (Download / Preview-Edit)
   or an infographic/chart link, **When** the PDF is generated, **Then** the
   link text appears as a clickable URL label without broken layout.
4. **Given** an empty conversation (no messages), **When** the PDF icon is
   clicked, **Then** the user is told there is nothing to export and no
   file is produced.

---

### User Story 2 - Sensible file name and non-blocking behavior (Priority: P2)

The downloaded file carries a meaningful name derived from the conversation
(first user question or a timestamp), not a random string. While the PDF is
being prepared the icon shows a busy state; the chat stays usable and the user
can cancel nothing that would freeze the page.

**Why this priority**: Trust and usability — a `download-1739284.pdf` mystery
file or a frozen UI undermines the feature even when it works.

**Independent Test**: Trigger a download on a long conversation; observe the
busy state during generation, verify the file name matches the first question
(truncated sensibly) and the page remains interactive throughout.

**Acceptance Scenarios**:

1. **Given** a conversation whose first user question is "How do I deploy the
   stack?", **When** the PDF downloads, **Then** the file name starts with a
   readable slug of that question (e.g., `how-do-i-deploy-the-stack…pdf`).
2. **Given** a long conversation that takes seconds to render, **When** the
   user triggers the export, **Then** the icon shows a busy state until the
   download starts and the page stays responsive.
3. **Given** PDF generation fails (renderer error), **When** the user clicks
   the icon, **Then** a clear error message appears and the icon returns to
   its normal state.

---

### User Story 3 - Light and dark theme fidelity (Priority: P3)

The PDF renders in light styling regardless of the app theme so text is always
on a printable white background; nothing invisible (e.g., dark-mode colors on
white paper) ships.

**Why this priority**: Print fidelity matters but is invisible until someone
prints or shares the file; core export value comes first.

**Independent Test**: Switch the UI to dark mode, export, open the PDF —
background is white, all text legible.

**Acceptance Scenarios**:

1. **Given** the app in dark mode, **When** the conversation is exported,
   **Then** the PDF uses a light/print palette and every message is legible.

---

### Edge Cases

- What happens when the conversation contains only an in-flight (still
  streaming) assistant answer? → The export renders the completed turns and
  the partial answer up to the streamed text; no crash.
- What happens when a message contains a very long single-line code block or
  an oversized image? → Content is wrapped/scaled to page width, never
  clipped silently beyond page bounds or overflowing the margin.
- What happens when an image in an answer cannot be fetched at export time
  (unreachable URL, offline)? → The PDF shows the image's labeled link in
  place of the image; never a blank box or broken icon (FR-012).
- What happens with non-Latin characters (Chinese, emoji) in messages? →
  Characters render correctly in the PDF (no tofu boxes) or are replaced
  with a visible placeholder, never dropped silently.
- What happens when the user triggers the icon twice quickly? → At most one
  in-flight export; re-trigger is ignored until the current one finishes.
- What happens when the browser blocks the download (permission)? → A hint
  tells the user the download was blocked, consistent with the app's error
  style.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The chat UI MUST present a PDF download icon in the chat
  header, visible whenever at least one completed message pair exists, hidden
  or disabled when the conversation is empty.
- **FR-002**: Clicking the icon MUST produce a single PDF file containing all
  completed conversation turns in chronological order: user questions and
  assistant answers, visually distinguished, with any citations/sources
  attached to an answer included as clickable reference links.
- **FR-003**: The PDF rendering MUST preserve the essential content of each
  answer: headings, lists, tables as grids, code blocks in monospace, and
  images embedded as actual images — matching the on-screen markdown semantics
  the chat already renders (Constitution I: reuse the existing markdown
  pipeline rather than a parallel one).
- **FR-004**: The download MUST be triggered through the browser's native
  download mechanism; no server round-trip beyond what the rendering itself
  needs, and no persistence of exported files on any server.
- **FR-005**: The exported PDF MUST use a light, print-appropriate palette in
  all cases.
- **FR-006**: The file name MUST be derived from the conversation's first
  user question (slugified, length-capped) or a timestamp fallback when no
  question exists.
- **FR-007**: The system MUST handle export failure honestly (Constitution
  IV): a visible error, the icon restored to normal state, and no partial or
  corrupted file silently delivered.
- **FR-008**: The export MUST NOT block the chat UI (busy indicator instead
  of a freeze) and MUST ignore duplicate triggers while an export is running.
- **FR-009**: Streaming answers MUST be exportable as their current partial
  text; in-flight turns never appear twice (header timestamp/turn metadata is
  monotonic).
- **FR-010**: The export MUST include conversation-external artifacts
  (deck action bars, infographic/chart URLs) as their visible link labels,
  not as broken interactive components.
- **FR-011**: The export MUST NOT include internal reasoning metadata —
  routing decisions, provenance badges, reflection records — even though
  the UI displays them in its reasoning panel; the PDF mirrors the visible
  conversation only (per Clarification 2026-10-21).
- **FR-012**: Images referenced in answers MUST be embedded in the PDF as
  actual images (fetched client-side at export time); an image that cannot
  be fetched MUST degrade to its labeled link — never a blank box, broken
  icon, or silently missing content (per Clarification 2026-10-21).

### Key Entities

- **Conversation**: the ordered set of messages (user questions, assistant
  answers, tool artifacts) currently loaded in the chat session; source of
  truth for the export, read at export time.
- **Exported PDF document**: the rendered file; name derived per FR-006;
  contains a title block (conversation title/timestamp) and the rendered
  turns.
- **Export action state**: idle | busy | error; drives the icon's busy state
  and the duplicate-trigger guard (FR-008).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can export a 20-turn conversation to a readable PDF in
  under 10 seconds on a typical laptop (hardware-relative per Constitution
  quality gates).
- **SC-002**: 100% of exported PDFs open without warnings in two standard
  viewers (one browser viewer + one OS viewer) on the sample conversations.
- **SC-003**: 90% of user-test sessions where the participant is asked to
  "save this conversation as a PDF" complete it on the first attempt without
  assistance.
- **SC-004**: The export adds no new runtime service to the stack
  (Constitution III): everything needed ships inside the existing web app.

## Assumptions

- Export scope is the **current conversation only** (no cross-conversation
  history browser) — v1 keeps it to what's on screen.
- The chat session already holds the rendered markdown tree; the export
  reuses that structure rather than re-fetching from the API.
- Client-side rendering is acceptable and expected (nothing leaves the
  machine — supports FR-004's no-persistence posture).
- Print-oriented light styling is the only theme for v1; theme-faithful
  export is out of scope.
- Non-Latin coverage follows whatever font stack the renderer ships;
  acceptable for v1 if emojis degrade visibly, not silently (per Edge Cases).