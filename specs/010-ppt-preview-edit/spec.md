# Feature Specification: PPT Completion Experience — Preview & Edit in the Browser

**Feature Branch**: `010-ppt-preview-edit`

**Created**: 2026-10-19

**Status**: Draft

**Input**: User description: "enhance the ppt-master function, provide a url for user to download and preview/edit the powerpoint when the powerpoint has completed."

**Existing contracts (Constitution I)**: the `ppt_export` tool's result shape (file + download URL) and the existing download route are frozen — this feature is additive on top of the delivery experience introduced in spec 009. Same-conversation revision behavior is unchanged.

## Clarifications

### Session 2026-10-19

- Q: Should the v1 edit experience be full in-browser document editing or conversation-driven revisions? → A: **Option A — conversation-driven revisions only**: the completion page's edit path points back to the chat; the agent rewrites pages and re-exports, and the downloaded file is natively editable in PowerPoint. In-browser WYSIWYG editing (office editor service) and lightweight in-browser text editing are out of scope for v1 — zero new services (Constitution III).
- Q: Should the in-chat deck action icons (Download / Preview-Edit buttons in the AI Chat UI) be part of this feature's scope, or a separate follow-up feature? → A: **Option A — part of this feature**: the Chat UI renders deck links as an action bar with Download and Preview/Edit icon buttons, planned and tested together with the completion page.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — One-Link Completion Experience (Priority: P1)

When the agent finishes a deck, its answer contains a link that opens a **completion page in the browser**: every slide visible as a faithful preview, a prominent download button for the `.pptx`, and the path to editing. The user never has to download-and-open the file just to see what was made.

**Why this priority**: This is the feature — turning the bare download link into a completion experience (preview + download + edit entry point) without breaking anything that exists.

**Independent Test**: Generate a one-page deck through the chat; click the link in the answer; verify slides render in the browser and the download button yields the same native-editable file.

**Acceptance Scenarios**:

1. **Given** a completed export, **When** the user opens the link from the chat answer, **Then** a completion page shows a visual preview of every slide in the deck, rendered in the browser without any download or Office application.
2. **Given** the completion page, **When** the user clicks the download button, **Then** the downloaded file is byte-for-byte the same exported deck the direct URL serves, opening as fully native editable content.
3. **Given** the existing direct download URL from `ppt_export`, **When** it is used as before (clicking the raw link in chat), **Then** it still downloads the file directly — no behavior change for existing users.

---

### User Story 2 — Faithful In-Browser Preview (Priority: P1)

Each slide's preview reflects the actual deck content — the same page the exported file contains — at readable quality, on desktop and mobile browser widths, without requiring a PowerPoint install or a file download.

**Why this priority**: Preview fidelity is the core of the value; a wrong or low-quality preview defeats the point.

**Independent Test**: Compare the browser preview of each slide against the exported deck opened in PowerPoint — content, layout, and text must match.

**Acceptance Scenarios**:

1. **Given** a completed multi-page deck, **When** the completion page loads, **Then** every slide is previewable, in order, and identifiable by page number.
2. **Given** a preview, **When** the browser window is narrowed (mobile width), **Then** the preview remains readable and correctly proportioned.
3. **Given** an export whose preview cannot be generated, **When** the completion page loads, **Then** the affected slide shows an honest "preview unavailable" state with the download still available — never a blank, wrong, or fabricated rendering.

---

### User Story 3 — Editing the Finished Deck (Priority: P2)

After previewing, the user wants changes. The completion page presents the edit path appropriate to the deployment: requesting revisions through the conversation (the agent rewrites pages and re-exports), and/or in-browser editing of the document itself. The v1 edit experience is a scope decision recorded below.

**Why this priority**: Editing is explicitly requested but has materially different possible scopes; the base experience (ask the agent in chat) already works from spec 009.

**Independent Test**: From the completion page, follow the presented edit path for a text change and verify the user ends up with an updated deck.

**Acceptance Scenarios**:

1. **Given** the completion page, **When** the user chooses to revise via the conversation, **Then** the page guides them back to chat, and a subsequent revision request produces a new export whose completion page reflects the changes (old links keep working, per spec 009 retention).

---

### User Story 4 — In-Chat Deck Actions (Priority: P1)

When the agent's answer in the AI Chat UI contains a completed deck's link, the chat renders it as a **deck action bar** — an icon-labelled control with a Download action for the `.pptx` and a Preview/Edit action opening the completion page — instead of a bare markdown link.

**Why this priority**: This is the user's explicit expectation for the delivery experience in the Chat UI itself, and it is the entry point that makes the completion page discoverable.

**Independent Test**: Send a deck-generation request in the Chat UI; the final answer shows the action bar; both actions work (download yields the file; preview/edit opens the completion page).

**Acceptance Scenarios**:

1. **Given** an assistant answer containing the deck's export link, **When** it renders in the Chat UI, **Then** it appears as an action bar with distinct Download and Preview/Edit actions, each carrying a visible label or icon.
2. **Given** the action bar, **When** Download is chosen, **Then** the file downloaded is the exported deck (same artifact the direct URL serves).
3. **Given** the action bar, **When** Preview/Edit is chosen, **Then** the completion page opens (Story 1).
4. **Given** any other link in any assistant answer, **When** it renders, **Then** it stays an ordinary link — no other markdown rendering changes.

---

### Edge Cases

- What happens when a preview rendering fails or is stale after a re-export? (Each export artifact carries its own preview; re-exports create new artifacts with fresh previews — old completion pages stay consistent with their own file.)
- What happens on very large decks? (Preview pages load progressively; the page count bound of spec 009 v1, ≤ 5 pages, keeps this bounded.)
- What happens when the user opens a completion link for a deck whose files were removed (retention/cleanup)? (Honest not-found page; the download and preview states both say so — never a fake or silently empty page.)
- What happens on browsers without modern capabilities? (Preview degrades to the download experience with an honest notice.)
- What happens when the chat answer is viewed in a client that is not the AI Chat UI (e.g. the Dify webapp)? (The deck link degrades gracefully to the ordinary markdown link — the action bar is a Chat UI enhancement, never a dependency for the link to work.)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: When a deck export completes, the user MUST be able to open a completion page in a browser that presents, for that export: a visual preview of every slide, a download control for the `.pptx`, and the edit path.
- **FR-002**: Slide previews MUST faithfully represent the corresponding pages of the exported file (content, layout, and text) and MUST be produced as part of export without any user action.
- **FR-003**: The existing `ppt_export` result contract and direct download URL behavior MUST remain unchanged (additive-only; existing consumers see no difference).
- **FR-004**: The completion page MUST render in modern desktop and mobile browsers without requiring a download, an Office application, or an account.
- **FR-005**: The completion experience MUST degrade honestly: missing or failed previews show an explicit unavailable state while the download remains available; a removed deck shows an honest not-found page.
- **FR-006**: The edit path for v1 MUST be conversation-driven revision: the completion page directs the user back to the chat, where revision requests produce a re-export; the downloaded file is natively editable in PowerPoint. In-browser document editing is out of scope for v1.
- **FR-007**: Every completion page MUST correspond to exactly one export artifact; a re-export MUST produce a new completion page, and previously issued pages MUST keep working for the life of their artifact (spec 009 retention).
- **FR-008**: Preview generation failures MUST NOT block export delivery: the deck is still exported, downloadable, and the completion page reports the degraded preview state honestly.
- **FR-009**: The completion experience MUST match the deployment's existing security posture (local-trust network, unauthenticated, consistent with the download route).
- **FR-010**: The AI Chat UI MUST render deck export links in assistant answers as a deck action bar with distinct Download and Preview/Edit actions, each carrying a visible icon or label.
- **FR-011**: The action bar's Download action MUST deliver the same export artifact the direct URL serves, and the Preview/Edit action MUST open that export's completion page.
- **FR-012**: The action bar MUST apply only to deck export links; all other links and markdown rendering in the Chat UI MUST remain unchanged.

### Key Entities

- **Completion Page**: the per-export browser experience (preview set, download control, edit path); one per Export Artifact.
- **Slide Preview**: the visual rendering of one slide on the completion page; belongs to exactly one Completion Page; ordered by page number.
- **Export Artifact**: unchanged from spec 009 (immutable per export; re-exports append).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user opening the completion link sees the first slide preview within 3 seconds on the local network.
- **SC-002**: 100% of successfully exported decks have a working completion page with a functioning download control.
- **SC-003**: Preview content matches the exported file for every slide in at least 95% of test decks (remainder = honest degraded states, never mismatched content).
- **SC-004**: The direct download URL from `ppt_export` continues to work unchanged for 100% of existing references.
- **SC-005**: A user with no PowerPoint install can view every slide and download the file from the completion page in one visit.
- **SC-006**: Deck export links in Chat UI answers render as the action bar in 100% of test cases, with all other links rendering unchanged.

## Assumptions

- The single-user, local-network deployment and its unauthenticated posture carry over from spec 009.
- The deck page count bound (≤ 5 pages v1) carries over, bounding preview size.
- The underlying PPT toolchain already produces per-page visual masters during export; the preview experience reuses artifacts of the pipeline rather than re-rendering from scratch (planning decides the exact mechanism).
- In-browser WYSIWYG document editing, if chosen, introduces a new self-hosted editing service — a Constitution III (minimal dependencies) decision that the clarification question resolves explicitly.
- Same-conversation agent revisions from spec 009 are the edit path for v1 (Clarifications, 2026-10-19); the completion feature adds the browser-facing entry point. No new editing service enters the deployment.
