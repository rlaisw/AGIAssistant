# Research — PPT Completion Experience (Phase 0)

Decisions resolving the plan's unknowns. Format: Decision / Rationale / Alternatives considered.

## R1. Preview rendering source

**Decision**: reuse the ppt-master pipeline's own self-contained per-slide renderings. At export time the bridge invokes the pipeline's finalize step (already part of the toolchain, already used in the manual Dify deck run) to produce self-contained page SVGs, then **snapshots** them into a per-artifact directory `<project>/previews/<artifact-stem>/`. The completion page serves those snapshot files as slide previews.

**Rationale**: the renderings are the exact masters the `.pptx` is converted from — faithfulness by construction (FR-002/SC-003), zero new rendering code, and the snapshot makes each artifact's preview immutable so a re-export never mutates an issued completion page (FR-007).

**Alternatives**: render from the `.pptx` via a converter (new dependency, fidelity risk); render previews on page load from current project state (breaks per-artifact immutability); screenshot via headless browser (heavyweight new runtime).

## R2. Completion page delivery

**Decision**: a server-rendered HTML page on the sidecar wrapper at `GET /decks/<project_id>/<artifact_stem>/`, plus a slide-asset route `GET /decks/<project_id>/<artifact_stem>/slides/<file>` serving the snapshot SVGs (traversal-safe). Static HTML + inline CSS from the theme tokens; no JavaScript framework, no build step.

**Rationale**: one process (the existing sidecar) already serves the download route — adding two routes reuses it (Constitution III); a plain page works on desktop and mobile browsers with no assets beyond the slide SVGs; the URL family sits beside, not inside, the frozen `/exports/` path.

**Alternatives**: a Next.js page in the Chat UI (couples deck delivery to the chat app); a static HTML file written into the project at export time (served identically, but the dynamic route derives the page from the artifact state — cleaner degraded/404 handling); a separate static file server (new service).

## R3. How the export tool exposes the page

**Decision**: `ppt_export`'s result gains one additive field `page_url` (`http://…/decks/<project>/<stem>/`). `file` and `url` remain byte-compatible. The rulebook is updated to prefer `page_url` as the link in the final answer (the page carries the download control), so the agent's answer has one primary link.

**Rationale**: Constitution I explicitly permits additive fields; keeping the old fields lets spec 009 consumers (including the deployed chatflow before its rulebook is refreshed) work unchanged.

**Alternatives**: replacing the answer link shape (breaking); returning only the page URL and deriving downloads (further from the frozen contract).

## R4. Preview failure handling (user directive: error handling)

**Decision**: the snapshot step is wrapped in its own failure boundary: if finalize or the snapshot fails, the export still completes, `page_url` is still returned, and the completion page renders in a **degraded mode** — download available, each slide showing an honest "preview unavailable" state. A `preview_degraded` marker file in the artifact's preview directory records the state so the page renders consistently on reload.

**Rationale**: FR-008 (preview failure never blocks delivery) + Constitution IV (explicit degraded state, never blank/fabricated).

**Alternatives**: failing the export on preview failure (violates FR-008); retry loops (adds latency for a degraded-mode-acceptable outcome).

## R5. In-chat action bar + URL derivation (Chat UI)

**Decision**: a pure helper (`ai-chat-landing/lib/deck-url.ts`) recognizes two URL shapes — the direct download (`/exports/<project>/<file>.pptx`) and the completion page (`/decks/<project>/<stem>/`) — and derives the counterpart URL deterministically (shared project + stem). The markdown renderer's link override routes recognized links to a `DeckActions` component: Download action → the `.pptx` URL, Preview/Edit action → the page URL, with lucide icons and accessible labels. Non-matching links render exactly as before.

**Rationale**: derivation from a single link keeps the agent contract unchanged (either link shape works); the pure helper is unit-testable (Constitution II) without a component-render harness; FR-012's no-regression rule is enforced by the interceptor only matching the two exact URL families.

**Alternatives**: agent emits structured metadata instead of a link (bigger contract change); fetching artifact metadata from the sidecar for each link (network dependency in the renderer); iframes of the completion page inside the chat (cluttered, mobile-hostile).

## R6. Chat UI test tooling

**Decision**: add `vitest` as a dev-only dependency to `ai-chat-landing` (node environment, no react renderer) covering the pure derivation helper and the recognition patterns. The action bar's visual behavior is validated by quickstart browser scenarios.

**Rationale**: Constitution II demands a runnable check for non-trivial logic; the derivation is the only non-trivial pure logic on the client. A full component-render harness (testing-library + jsdom) would add dependencies for little marginal coverage beyond what the browser scenarios exercise — the tradeoff is documented here deliberately.

**Alternatives**: no Chat UI tests (constitution violation); full component testing stack (dependency weight not justified by the two-branch component).

## R7. Test strategy (user directive: test cases)

**Decision**:
- **unit** (`test_ppt_completion.py`): snapshot logic (copies, ordering, stem mapping), degraded-marker behavior, completion-page HTML contains download link + slide count + degraded states, URL/traversal validation.
- **integration** (`test_ppt_completion_pipeline.py`, real toolchain): export → preview snapshot exists per artifact; re-export → second artifact, first artifact's page and files unchanged (FR-007); forced finalize failure → export succeeds + degraded page (FR-008).
- **contract** (`test_ppt_completion_contract.py`, fake scripts): `/decks/` page 200 with expected HTML, slide asset 200 with svg content-type, honest 404 for unknown artifact, 400/404 for traversal; `ppt_export` result keeps `file`+`url` byte-compatible and adds `page_url`; the entire spec-009 contract suite re-runs green (Constitution I).
- **vitest**: derivation helper both directions, non-matching URLs return null, malformed paths rejected.

**Alternatives**: manual-only validation (constitution violation); mocking the toolchain in integration (would not prove snapshot/re-export isolation against the real finalize output).

## R8. Edit path on the completion page

**Decision**: the page's edit control links back to the conversation with a short instruction line ("Ask in chat: 'revise page 2 of this deck'"), matching the clarified Option A (conversation-driven revisions only). No query parameters or special routing into Dify — a plain, honest pointer.

**Rationale**: zero coupling to the chat client; works identically from the Dify webapp and the AI Chat UI; the revision machinery (rewrite page → re-check → re-export) already exists and is instruction-driven.

**Alternatives**: deep-link into the chat with prefilled text (client-specific, fragile); in-browser editing (explicitly out of scope per Clarifications).
