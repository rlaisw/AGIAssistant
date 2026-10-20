# Feature Specification: AntV Data Visualization Tools on the AgenticRAG Sidecar

**Feature Branch**: `012-antv-visualization-tools`

**Created**: 2026-10-20

**Status**: Draft

**Input**: User description: "To add new Dify MCP Tools, based on the above conversation, I choose Option B: bridge into the agentic-rag sidecar" — i.e. add AntV data-visualization capability (statistical charts, diagrams, and infographics) as new tools on the **existing** sidecar MCP provider, usable by both the Agentic Strategy node and the PPT-Master node in the Dify chatflow.

**Existing contracts (Constitution I)**: all existing tool schemas (21 tools), routes, and app behaviors are frozen — this feature is additive `antv_*` tooling on the existing provider. No new Dify-side registration, SSRF change, or provider entry is required.

**Chosen architecture (user decision, this session)**: Option B — bridge into the agentic-rag sidecar, as one "AntV Data Visualization" capability, rather than registering the standalone chart server or a Dify custom tool.

## Clarifications

### Session 2026-10-20

- Q: Should charts embedded in exported decks be self-contained (bytes embedded) or hotlinked to the cloud chart URL? → A: **Option A — self-contained**: the deck pipeline fetches the chart image at export and embeds the bytes into the `.pptx`; if fetching fails, the quality gate fails honestly (no silent blank slide, no hotlink fallback).

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Charts in Chat Answers (Priority: P1)

A user asks in the chat: "show me the monthly ticket volume as a bar chart". The Agentic Strategy agent selects an appropriate chart type, calls the visualization tool with the data, and embeds the resulting chart image in its markdown answer — the image renders inline in the Chat UI and the Dify webapp, no different from any image.

**Why this priority**: This is the core capability — data visualization on demand in the primary chat flow.

**Independent Test**: send a "chart it" prompt through the chatflow's service API; the answer contains an image link; the link renders a chart from a browser without authentication.

**Acceptance Scenarios**:

1. **Given** a user request containing data or a data source plus a charting intent, **When** the agent responds, **Then** the answer contains a working image link whose image matches the requested chart semantics (type, categories, values).
2. **Given** an ambiguous charting request ("visualize this"), **When** the agent chooses a type, **Then** the choice follows the chart-selection guidance (e.g. trends → line/area, proportions → pie, distribution → histogram).
3. **Given** the rendering service is unreachable or rejects the request, **When** the agent calls the tool, **Then** it receives an honest machine-readable error and tells the user plainly — no fabricated image links.

---

### User Story 2 — Charts in PowerPoint Decks (Priority: P1)

The PPT-Master agent builds a deck whose page needs data visuals: it generates the chart, then embeds the chart image into the slide page, and the exported `.pptx` (and its completion-page preview) shows the chart on the slide.

**Why this priority**: This is the PPT-Master integration the user explicitly requested — the deck pipeline gains charts.

**Independent Test**: prompt for a one-page deck containing a chart of sample data; the exported file and the completion page both show the chart image on the slide.

**Acceptance Scenarios**:

1. **Given** a deck request that benefits from a chart (comparisons, trends, proportions), **When** PPT-Master authors the page, **Then** it embeds the chart image into the page and the exported deck renders the chart in place.
2. **Given** the slide authoring guidance, **When** charts are embedded, **Then** sizing and placement keep the chart readable within the page zones, and the deck still passes the quality gate.

---

### User Story 3 — Infographics (Priority: P2)

The agent produces an infographic from a topic or structured content: it writes the declarative infographic description, the tool renders it, and the user receives a viewable result (a link that opens the rendered infographic in a browser).

**Why this priority**: Infographics complement charts, but the server-side rendering approach carries verification risk the plan must retire first; charts deliver the primary value.

**Independent Test**: ask for an infographic of a small step-by-step process; the returned link opens a rendered infographic containing the given steps.

**Acceptance Scenarios**:

1. **Given** a request for an infographic (steps, comparisons, timelines, hierarchies), **When** the agent composes the infographic description and calls the tool, **Then** the returned link opens a fully rendered infographic in a browser.
2. **Given** malformed or unsupported infographic content, **When** the tool is called, **Then** the agent receives an honest, fixable error — never a blank or broken rendering presented as success.

---

### User Story 4 — Honest Degradation and Data Posture (Priority: P2)

The visualization capability is transparent about its limits: chart types that cannot be rendered by the configured service are excluded or refused honestly; and the deployment's data-handling posture (where chart data travels for rendering) is documented and, if the default is unacceptable, a private rendering option exists.

**Why this priority**: Constitution IV applied to a capability whose default rendering path is external.

**Independent Test**: request an unsupported chart type and observe an honest refusal; read the deployment documentation and find the data-posture statement.

**Acceptance Scenarios**:

1. **Given** a chart type outside the supported set for the configured rendering service, **When** the agent attempts it, **Then** the tool refuses honestly with the supported list, and the agent relays it.
2. **Given** the deployment documentation, **When** an operator reviews it, **Then** the data-posture (which rendering service is used, what leaves the network, and the private alternative) is stated.

---

### Edge Cases

- Chart data that is too large or malformed for the rendering service → honest error, agent summarizes or samples.
- Rendering service outage mid-session → agents answer with text/table fallback and say so, never fake image links.
- Image links from a previous session after artifact cleanup → links degrade to an honest not-found, consistent with existing retention.
- Concurrent chart requests → no interference (stateless rendering calls).
- A deck page embedding a chart whose image cannot be fetched at export time → the quality gate fails honestly with the failing page named (self-containment requirement, 2026-10-20) — never a blank frame, never a silent hotlink.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a chart-generation tool on the existing MCP provider that accepts a chart type, data, and title, and returns an image URL usable in markdown answers and embeddable in deck pages.
- **FR-002**: The chart tool MUST support the common chart families (trends, comparisons, proportions, distributions, relationships, hierarchies, flows) through a parameterized type list, with chart-selection guidance embedded in the tool's description so agents choose well without extra prompting.
- **FR-003**: Chart types unsupported by the configured rendering service (including geography-dependent ones) MUST be excluded or refused with an honest, machine-readable error naming the supported set.
- **FR-004**: The system MUST provide an infographic tool that accepts a declarative infographic description and returns a browser-viewable rendered result (link), with the server-side rendering approach validated during planning.
- **FR-005**: Both tools MUST be additive: existing tool schemas and count relationships documented in prior specs remain intact; the deploy automation's re-sync surfaces the new tools without new Dify-side registration.
- **FR-006**: Failures (service unreachable, unsupported type, malformed data, rendering error) MUST return honest machine-readable errors with agent-actionable hints — never empty success or fabricated links (Constitution IV).
- **FR-007**: The deck authoring guidance (PPT rulebook) MUST be extended with chart embedding: when to use a chart, how to size and place it within page zones, and embedding via image references. **Exported decks MUST be self-contained**: the pipeline fetches each chart image at export time and embeds the image bytes into the `.pptx`; a fetch failure MUST fail the quality gate honestly rather than exporting a blank or hotlinked frame (Clarifications, 2026-10-20).
- **FR-008**: The primary agent's instructions MUST mention the visualization capability so ordinary questions get charted when appropriate.
- **FR-009**: The deployment documentation MUST state the data-handling posture: which rendering service chart data travels to by default, and the supported private-rendering alternative.
- **FR-010**: The verification battery MUST gain scenarios proving the chart and infographic tools end-to-end (tool call → image/result link → link serves), and the full existing test suite MUST stay green (additive-only).
- **FR-011**: The chart-selection guidance and infographic syntax guidance (from the AntV skills material) MUST be distilled into tool descriptions and agent instructions — not installed as separate IDE skills on the server.

### Key Entities

- **Chart Request**: chart type + data + title (+ optional styling hints) submitted by an agent; produces a **Chart Artifact**.
- **Chart Artifact**: a rendered chart image identified by a URL; usable in markdown and deck pages; lifecycle tied to the rendering service's retention.
- **Infographic Artifact**: a rendered infographic identified by a viewable link; produced from a declarative description.
- **Rendering Service**: the configured endpoint that turns chart/infographic descriptions into artifacts; default public, private alternative documented.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A "chart it" prompt through the chatflow returns an answer containing a working chart image within 30 seconds of the prompt.
- **SC-002**: 100% of chart tool successes return an image URL that serves the image from a fresh browser session without authentication.
- **SC-003**: A one-page deck generated with a chart requirement embeds the chart image **bytes** into the exported `.pptx` (the file shows the chart with no network dependency) and on its completion page — verified by the battery scenario.
- **SC-004**: 100% of tested failure paths (unsupported type, service down, malformed data) return an honest machine-readable error the agent relays — no fabricated links (verifiable by battery probes).
- **SC-005**: The existing test suite (319+ tests) and the deploy battery remain green after the addition, with the new scenarios included.

## Assumptions

*(defaults per the user's standing directive: follow recommendations, ask as few questions as possible)*

- **Option B confirmed**: tools live on the existing sidecar provider; no second MCP server, no Dify custom tool, no Dify marketplace plugin, no SSRF/registration changes.
- **Single parameterized chart tool** (one tool with a type parameter) instead of ~26 per-type tools — keeps agent tool lists lean; the skills' chart-selection guidance substitutes for per-type discoverability.
- **Default rendering uses the AntV public chart service** (chart data leaves the network; requires outbound internet). A private rendering service remains a documented, supported alternative for later. Geography-dependent charts are excluded (they are region-limited and unsupported in private deployments).
- **Infographic rendering approach** (server-side SVG vs. browser-rendered page served by the sidecar) is a planning-time decision, resolved by empirical verification — the spec requires only "a browser-viewable rendered result".
- Deck pages embed charts as image references, which the existing deck pipeline already permits; no new deck-format capability is required.
- Single-user local-trust deployment posture carries over; rendered artifacts follow the rendering service's own retention (documented), with link-degradation honesty matching existing patterns.
