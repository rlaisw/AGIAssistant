# Research — AntV Visualization Tools (Phase 0)

Decisions with rationale and rejected alternatives. Two spec-deferred unknowns were resolved empirically before this plan was finalized.

## R1. Chart rendering path (empirically verified)

**Decision**: `antv_chart` calls the GPT-Vis chart HTTP API directly — default `https://antv-studio.alipay.com/api/gpt-vis`, `POST {type, data, title}` → `{success, resultObj: <hosted image URL>, errorMessage}`. A live call this session returned `success: true` with an image URL on the Alipay CDN. The endpoint is configurable (`[antv] chart_service_url`) so a private GPT-Vis-SSR deployment can replace it without code changes (FR-009).

**Rationale**: calling the documented HTTP API directly avoids proxying the 26-tool MCP server, keeps a single parameterized tool (the agent picks the type; guidance in the docstring), and matches the sidecar's existing HTTP-call patterns.

**Alternatives**: registering the official mcp-server-chart as a second Dify MCP server (rejected: two providers, 26 tool entries, SSRF/registration work — the user chose Option B); MCP-to-MCP proxying through the sidecar (rejected: complexity for zero benefit).

## R2. Supported chart types and exclusions

**Decision**: a curated type list mirroring the service's supported families — line, area, bar, column, pie, radar, scatter, histogram, funnel, treemap, sankey, dual-axes, word-cloud, boxplot, venn, liquid, plus the diagram types (flow, mind-map, fishbone, organization, network) if the service accepts their payloads — validated against the live service during implementation; geography-dependent types (district-map, path-map, pin-map) are excluded by default (region-limited, unsupported in private deployments). The type list lives in code as the honest single source (FR-003's "supported set").

**Rationale**: the spec requires unsupported types refused honestly with the supported list; a code-level list makes the refusal and the guidance agree.

**Alternatives**: exposing all 26 service tools as parameters without curation (rejected: honest-refusal requirement); runtime discovery of supported types (planning-scope creep).

## R3. Infographic rendering: browser-side, served by the sidecar

**Decision**: `antv_infographic(description)` validates the declarative syntax (non-empty, size-capped), stores it under the projects-adjacent served directory, and returns a URL to a small HTML page served by the sidecar at `GET /infographics/<id>/` — the page loads the `@antv/infographic` UMD build from CDN (**verified reachable, HTTP 200**) and renders the stored syntax client-side. The result is a browser-viewable link satisfying FR-004 with zero server-side DOM.

**Rationale**: the engine is DOM-oriented; browser-side rendering is its native mode, avoids puppeteer/jsdom (Constitution III), and the "browser-viewable" spec requirement is met exactly. Failure modes are honest: bad syntax → validation error; CDN unreachable → the page still serves with a clear error shown in-page (and the tool result notes the dependency).

**Alternatives**: server-side SVG via jsdom/puppeteer (rejected: heavyweight, fragile); community infographic-cli (rejected: third-party wrapper, same DOM problem); returning raw syntax for the Chat UI to render (rejected: Dify webapp users lose the capability).

## R4. Deck chart self-containment (Clarification 2026-10-20, Option A)

**Decision**: `ppt_write_page` gains remote-image inlining: at write time, every `<image href="https://…">` in the submitted SVG is fetched (size-capped), base64-encoded, and re-embedded as `data:` URIs — the sanitizer already permits data URIs. A failed or oversized fetch is an honest, named error (the page is rejected until fixed). Pages become self-contained before export, so the exported `.pptx` carries chart bytes regardless of ppt-master's exporter internals — SC-003 proven at the file level.

**Rationale**: write-time inlining is deterministic and under our control; relying on the exporter's unverified remote-image handling would leave SC-003 to luck.

**Alternatives**: fetch-and-embed at export time inside svg_to_pptx (rejected: modifies ppt-master internals or duplicates its logic); hotlinks (explicitly rejected by the user).

## R5. Agent guidance (FR-002/FR-007/FR-008/FR-011)

**Decision**: the `antv_chart` docstring carries the distilled chart-selection table (intent → type: trends → line/area; comparisons → bar/column; proportions → pie/treemap; distribution → histogram/boxplot; relationship → scatter/dual-axes; hierarchy → treemap/organization; flow → sankey/flow; ranking → sorted bar/column); the PPT rulebook gains a "Charts in decks" section (when to chart, sizing within zones, embedding via image reference — noting the write-time inlining); the chatflow DSL is regenerated with both `antv_*` tools added to the Agentic Strategy and PPT-Master node tool lists, republished via the existing `chatflow` deploy command.

**Alternatives**: installing the AntV skills server-side (rejected — FR-011: distill, don't install); a separate guidance document the agents never see.

## R6. Configuration surface

**Decision**: `[antv]` section in config.toml — `chart_service_url` (default the AntV endpoint), `chart_timeout_s` (default 30), `max_inline_image_bytes` (default 2 MB), `infographic_max_syntax_bytes` (default 64 KB). Env overrides per the existing convention.

**Rationale**: matches the `[ppt]`/`[dify]` pattern; every knob needed for the private-rendering path and honest caps.

## R7. Error taxonomy (user directive: error handling)

**Decision**: `src/agentic_rag_mcp/antv/errors.py` — `AntvInvalidType` (names the supported set), `AntvInvalidInput` (malformed data/syntax, oversized), `AntvServiceError` (success=false / non-200, verbatim service message), `AntvServiceTimeout`, all mapping to the same `{"error": {code, message, hint}}` envelope used by the ppt tools (codes: `ANTV_INVALID_TYPE`, `ANTV_INVALID_INPUT`, `ANTV_SERVICE_ERROR`, `ANTV_SERVICE_TIMEOUT`). The bridge's inlining failures reuse `PPT_INVALID_INPUT` with the image href named.

**Rationale**: Constitution IV and the spec's FR-006; symmetry with the ppt tools keeps the agent-side contract uniform.

## R8. Test strategy (user directive: test cases)

**Decision**:
- **unit** (`test_antv_tools.py`): type validation (supported/excluded lists), payload construction, response mapping (success/failure/timeout), syntax caps, HTML page rendering contains syntax + engine reference, inlining (fake fetch → data URI; oversized → honest error).
- **integration** (`test_antv_pipeline.py`, network-gated with skipif): one live chart call returns a serving image URL; infographic route serves HTML that renders; a deck page with a remote image exports with embedded bytes (zip inspection: media in `ppt/media/`, no hotlink).
- **contract** (`test_antv_contract.py`, fake HTTP per the conftest pattern): tool schemas, tools/list 21 → 23 with existing unchanged, every error code's envelope shape, infographic route 404/400 semantics.
- **battery**: `antv-chart` (tool call → image URL serves), `antv-infographic` (route serves with syntax), `chart-in-deck` (exported deck contains the chart bytes).

**Alternatives**: mocking the chart service in integration (rejected — the live contract is the point; network-gated skip keeps CI honest).
