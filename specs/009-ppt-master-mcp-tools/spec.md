# Feature Specification: PPT-Master MCP Tools — Chat-Driven PowerPoint Generation in Dify

**Feature Branch**: `009-ppt-master-mcp-tools`

**Created**: 2026-10-18

**Status**: Draft

**Input**: User description: "Setup ppt-master as MCP tools in Dify. Based on previous conversation, I choose Option A — granular MCP tools, Dify agent drives (recommended). A Dify Agent Strategy node named 'PPT-Master' (ReAct / Function Calling) interacts with ppt-master via custom tools. User types a prompt like 'help to generate a powerpoint, introduce Dify software', then 'PPT-Master' auto-generates the powerpoint."

**Existing contracts (Constitution I)**: all 16 existing MCP tool response shapes are frozen. This feature is purely additive — new `ppt_*` tools alongside existing ones; no existing tool changes.

## Clarifications

### Session 2026-10-18

- Q: How should a chat prompt reach the PPT-Master agent — via a new intent router in the existing chatflow, or by also giving the existing AgenticRAG agent the PPT tools? → A: **Option A — intent router + dedicated node**: an intent-classification step in the existing chatflow routes deck-generation requests to a dedicated PPT-Master agent node; all other prompts continue to the existing AgenticRAG agent unchanged.
- Q: After a deck is generated, should users be able to revise it in the same conversation, or is v1 generate-only? → A: **Option A — same-conversation edits only**: users may revise, append, or rewrite pages on the active project and re-export within the same conversation; cross-conversation project resume/listing is out of scope for v1.
- Q: In v1, what source material can users give the PPT-Master agent? → A: **Option A — pasted text + the agent's own research**: pasted content and agent-researched sourced facts (via the search tools available to its node) are the v1 inputs; file attachments (PDF/DOCX) are out of scope for v1.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Prompt-to-Deck Generation (Priority: P1)

A user types a request in the chat UI (or any Dify client): "help to generate a powerpoint, introduce Dify software". The Dify chatflow routes the request to the "PPT-Master" agent, which plans a small deck, authors each slide, verifies quality, exports a native editable `.pptx`, and answers with a **download link the user can click**. The user does not need to know that ppt-master, SVG authoring, or quality gates exist — they asked for a PowerPoint and received a PowerPoint.

**Why this priority**: This is the entire feature — the end-to-end journey from a natural-language prompt to a downloadable, editable PowerPoint file.

**Independent Test**: Send "generate a one-page PowerPoint introducing Dify software" through the chat UI and receive a working download link whose file opens in PowerPoint as native editable shapes and text.

**Acceptance Scenarios**:

1. **Given** the PPT-Master agent is configured in the chatflow, **When** the user sends "help to generate a powerpoint, introduce Dify software", **Then** the agent's final answer contains a clickable download link to a `.pptx` file that opens as fully editable slides (native text, not images).
2. **Given** the same prompt with a page count ("a 3-page deck about X"), **When** generation completes, **Then** the exported file contains exactly that number of slides.
3. **Given** the user pastes source content instead of a topic ("turn the following into a PPT: …"), **When** generation completes, **Then** the deck's content is grounded in the provided material without invented claims.

---

### User Story 2 — Granular Tools for the Agent (Priority: P1)

The Dify agent drives deck creation through small, composable MCP tools rather than one opaque "make me a PPT" call: create a project, register the icons it will use, write each slide page, run the quality checker, and export. Each tool returns a small, structured result the agent can act on (including checker findings as fixable error text). This lets the agent iterate — write a page, see overflow errors, fix the page, re-check — the same loop a human agent performs.

**Why this priority**: The tool granularity is what makes the agent actually converge on a passing deck; a single opaque tool cannot self-repair.

**Independent Test**: Call each tool directly over MCP (init → icon sync → write page → check → export) with a minimal one-page deck and observe a passing export with zero manual intervention between steps.

**Acceptance Scenarios**:

1. **Given** no PPT project exists, **When** the project-init tool is called with a topic/name, **Then** a new project workspace is created and its identifier returned.
2. **Given** the agent requests icons, **When** the icon tool is called with icon names, **Then** successfully prepared icons are confirmed and missing names are reported honestly with re-pick suggestions (never silently substituted).
3. **Given** a written slide page, **When** the check tool runs, **Then** the result distinguishes blocking errors from advisory warnings as structured text the agent can act on.
4. **Given** a project with pages that pass the quality check, **When** the export tool runs, **Then** a `.pptx` file is produced and a downloadable URL for it is returned.

---

### User Story 3 — Download Delivery (Priority: P2)

The generated file is delivered as a link in the agent's chat answer. The link resolves in the user's browser (Chat UI or Dify webapp) and downloads the file without authentication friction beyond what the deployment already imposes.

**Why this priority**: Without a working delivery path, generation has no user-visible value.

**Independent Test**: From the Chat UI, click the link in the agent's answer and verify the downloaded file is the exported deck.

**Acceptance Scenarios**:

1. **Given** a completed export, **When** the user clicks the download link in the chat answer, **Then** the `.pptx` file downloads successfully.
2. **Given** the user asks for a previously generated deck again, **When** the agent re-answers with the prior link, **Then** the link still resolves (exports are retained, not garbage-collected mid-conversation).

---

### User Story 4 — Honest Status and Failure (Priority: P3)

Long generations are visible: the agent narrates progress (which slide is being authored, that checks are running). Failures are honest — if a slide cannot pass quality checks after reasonable attempts, or the request is out of scope (e.g., animated video decks), the agent says so instead of delivering a broken file or pretending success.

**Why this priority**: Trust during multi-minute tool runs; Constitution IV applied to a new surface.

**Independent Test**: Induce a failure (e.g., request an unsupported feature) and verify the agent answers with an honest explanation and no fabricated download link.

**Acceptance Scenarios**:

1. **Given** a deck where one page repeatedly fails the quality check, **When** the agent exhausts its repair attempts, **Then** it reports which page failed and why, and delivers no broken file.
2. **Given** a request outside the tool's capabilities (e.g., "make an animated video"), **When** the agent evaluates it, **Then** it declines honestly with what it can do instead.

---

### Edge Cases

- What happens when two users request decks concurrently? (Projects must be isolated; no cross-project file collisions.)
- What happens when the requested icon does not exist in the library? (Honest missing report with search guidance — never a substitute icon.)
- What happens when the export target folder is full or unwritable? (Explicit error surfaced to the agent, not a fabricated link.)
- What happens when the agent's tool-call loop exceeds the Dify node's iteration limit mid-deck? (Partial state remains inspectable; the agent reports progress and offers resume or a smaller page count.)
- What happens to old projects and exports over time? (Retention/cleanup behavior defined at planning; at minimum, exports must survive the current conversation.)
- What happens when the user requests an edit to a deck from a previous conversation? (Out of scope for v1 — the agent explains this and offers to regenerate the deck in the current conversation.)
- What happens when the user attaches a file expecting it in the deck? (Out of scope for v1 — the agent explains the limitation and offers paste-the-text or research-from-topic alternatives.)
- What happens when the user's prompt names a page count too large for one run? (Agent proposes a smaller deck or a continuation strategy rather than truncating silently.)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST expose granular PPT tools over the existing MCP server surface: create/initialize a PPT project, prepare (sync) icons, write a slide page, run the slide quality check, and export the deck. All tools are additive — existing tool schemas unchanged.
- **FR-002**: The project-init tool MUST accept a short project name (and optional source material) and return a unique project identifier plus the workspace path, isolating each generation in its own directory.
- **FR-003**: The icon tool MUST accept a list of icon references, sync the resolvable ones into the project, and report missing ones individually with library-appropriate search guidance — never substituting icons on its own.
- **FR-004**: The page-write tool MUST accept the project identifier, a page number, a slide name, and the slide's SVG content, persisting it as a page file in the project workspace.
- **FR-005**: The check tool MUST run the slide quality gate and return a structured result distinguishing blocking errors from advisory warnings, including the specific violation text (file, element, issue) so the calling agent can repair the page.
- **FR-006**: The export tool MUST only export projects whose pages pass the quality gate (zero blocking errors), and MUST refuse export (with the current error summary) otherwise.
- **FR-007**: A successful export MUST return the file location and a resolvable download URL for the generated `.pptx`.
- **FR-008**: The exported file MUST contain fully native, editable slide content (text frames, shapes, icons — not baked images) for slides authored as such.
- **FR-009**: A "PPT-Master" agent node in the Dify chatflow MUST be able to complete the full loop — plan, author, check, repair, export — using only the exposed tools and its own reasoning, with a distilled authoring rulebook (style and SVG contract essentials) as its instructions.
- **FR-010**: Every tool MUST return honest, machine-readable errors on failure (invalid project id, unwritable workspace, unknown icon, checker crash) — never empty results masquerading as success (Constitution IV).
- **FR-011**: Tool responses MUST include only additive fields relative to the existing MCP envelope conventions; the full tool list after this feature ships remains discoverable by Dify via the standard tools/list refresh.
- **FR-012**: The system MUST support concurrent projects without cross-contamination (unique project directories, per-project state).
- **FR-013**: Generated decks MUST be grounded in user-provided material or agent-researched sourced facts; the generation flow MUST retain the fact-provenance discipline of the underlying PPT tooling for content sourced during generation.
- **FR-014**: The chatflow MUST include an intent-classification step that routes deck-generation requests (e.g., prompts mentioning PowerPoint, deck, or slide generation) to the PPT-Master agent node, while all other prompts continue to the existing general agent with unchanged behavior.
- **FR-015**: Within the same conversation, users MUST be able to request revisions to the active deck (revise, append, or rewrite pages) followed by a re-export; cross-conversation project resume and listing are out of scope for v1.

### Key Entities

- **PPT Project**: an isolated generation workspace (identifier, name, created timestamp, pages, icon pool, exports); lifecycle managed by the init/export tools.
- **Slide Page**: one authored page (number, name, SVG content, check status) belonging to exactly one project.
- **Export Artifact**: a generated `.pptx` file (project reference, filename, timestamp, download URL, quality-gate result at export time).
- **Agent Rulebook**: the distilled authoring instructions (style defaults, canvas rules, SVG constraints, check-repair loop) that the PPT-Master agent node uses.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user requesting a one-page deck on a known topic receives a working download link within 5 minutes of the prompt.
- **SC-002**: 100% of delivered decks pass the slide quality gate (zero blocking errors) at export time.
- **SC-003**: Every delivered file opens in PowerPoint as native editable content (selectable text, movable shapes) — verified by opening each test export.
- **SC-004**: Tool responses to invalid inputs (bad project id, missing icon, failing check) return an explicit error in 100% of tested cases — no silent empty successes.
- **SC-005**: A user with no knowledge of the underlying pipeline can complete the prompt-to-download journey in one conversational turn, without leaving the chat.
- **SC-006**: Concurrent deck requests (two users) complete without file collisions or cross-project interference.

## Assumptions

- The ppt-master installation (git clone with its own Python environment and script set) remains available on the host that runs the MCP server; deployment packaging (mounting/co-locating it with the sidecar) is a planning concern, not a spec decision.
- The existing Dify chatflow gains an intent-classification step and a dedicated "PPT-Master" agent node (Clarifications, 2026-10-18); the existing AgenticRAG agent and its prompt remain unchanged. Dify tool-cache refresh semantics apply after tool changes.
- The first release targets the quick-generation profile (single-pass authoring, minimal gates) to keep agent loops and latency manageable; the full staged design flow is a future extension.
- v1 source material is pasted text and agent-researched sourced facts; file attachments (PDF/DOCX) uploaded in chat are out of scope for v1 and a future extension. The deck's language follows the user's prompt language.
- Deck size for v1 is bounded (suggest ≤ 5 pages per run); larger decks use continuation or follow-up requests.
- The chat client renders markdown links (both the Chat UI and Dify webapp do), so download delivery via a link in the answer needs no client changes.
- Existing sources of the PPT tooling (fact provenance, icon libraries, checker) are used as-is; this feature wraps them, it does not modify their behavior.
- Exports are served over the same HTTP surface as the MCP server's health endpoint, on the existing host port convention; authentication matches the deployment's current posture (local network trust).
