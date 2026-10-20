# Implementation Plan: AntV Data Visualization Tools on the Sidecar

**Branch**: `012-antv-visualization-tools` | **Date**: 2026-10-20 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/012-antv-visualization-tools/spec.md`

**Note**: User directive: original architecture plus explicit **test-case creation** and **error handling** as first-class deliverables.

## Summary

Two additive tools on the existing sidecar provider — `antv_chart(chart_type, data, title)` (calls the GPT-Vis chart rendering HTTP API, returns a hosted image URL for markdown answers and deck pages) and `antv_infographic(description)` (stores the declarative syntax, serves a browser-rendered HTML page from the sidecar) — plus self-contained deck chart embedding (remote images inlined as data URIs at page-write time), agent guidance (chart-selection in tool docstrings, charts-in-decks in the PPT rulebook), battery scenarios, and data-posture documentation. No new Dify registration, no new runtime services.

## Technical Context

**Language/Version**: Python 3.12 (sidecar tools + bridge change), HTML (infographic page), no new dependencies (httpx already installed; infographic engine loads from CDN in the browser).

**Primary Dependencies**: the chart rendering HTTP service — default `https://antv-studio.alipay.com/api/gpt-vis`, POST `{type, data, title}` → `{success, resultObj: image-url, errorMessage}` (**verified live this session**); optional private replacement via GPT-Vis-SSR configured as `[antv] chart_service_url`; the infographic engine UMD from CDN (**verified reachable, HTTP 200**). Rendering happens browser-side for infographics — no server-side DOM, no puppeteer.

**Storage**: filesystem — infographic syntax files under a served directory (same pattern as `/exports`); no chart bytes stored (hosted URLs for chat; inlined at write time for decks).

**Testing**: pytest three-tier + battery scenarios. Matrix in [contracts/antv-tools.md](contracts/antv-tools.md) (Constitution II).

**Target Platform**: existing Linux Docker sidecar + Dify 1.17 chatflow v2 (both agent nodes gain the tools via DSL regeneration).

**Performance Goals**: `antv_chart` ≤ 30 s end-to-end (SC-001); infographic route serves in ≤ 100 ms.

**Constraints**: additive-only (tool count 21 → 23); no new runtime services (Constitution III); deck charts self-contained (Clarification 2026-10-20 — bytes embedded, honest gate failure); geo chart types excluded; all failures honest machine-readable (Constitution IV).

**Scale/Scope**: single user; chart data bounded by the rendering service's limits; infographic syntax size-capped.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Justification |
|-----------|--------|---------------|
| I. Contract Preservation | PASS | Two new `antv_*` tools only; all existing schemas unchanged; existing suites must stay green (matrix item) |
| II. Tests-First | PASS | Matrix defined in `contracts/antv-tools.md` before implementation, including every error path and the self-containment proof |
| III. Minimal Dependencies | PASS | No new packages, services, or Dify registration; rendering is an HTTP call (charts) and browser-side CDN (infographics) |
| IV. Honest Answers | PASS | Error envelope for unsupported types, service failures, malformed syntax, oversized images; no fabricated links (FR-003/FR-006) |
| V. Spec-Driven Replacement | N/A | Additive feature |

## Project Structure

### Documentation (this feature)

```text
specs/012-antv-visualization-tools/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── antv-tools.md   # tool schemas, error envelope, infographic route, test matrix
└── tasks.md            # (/speckit.tasks output)
```

### Source Code (repository root)

```text
src/agentic_rag_mcp/
├── config.py                      # + [antv] section (chart_service_url, timeouts, caps)
├── server.py                      # + antv_chart / antv_infographic registrations
├── antv/
│   ├── __init__.py
│   ├── errors.py                  # AntvError hierarchy -> honest envelope
│   ├── charts.py                  # type list + validation, payload, HTTP call, response mapping
│   └── infographic.py             # syntax validation, storage, HTML page rendering, URL
└── ppt/bridge.py                  # write_page: inline remote <image href> as data URIs (self-containment)

dify/docker/mcp-server/server.py   # + GET /infographics/<id>/ route (HTML page)

dify/ppt-master-rulebook.md        # + "Charts in decks" section; DSL regenerated (both nodes gain tools)

tests/
├── unit/test_antv_tools.py        # type validation, payload, error mapping, syntax caps
├── integration/test_antv_pipeline.py  # live chart call (network-gated), infographic route, deck self-containment
└── contract/test_antv_contract.py     # schemas, additive count 21→23, error envelope, battery scenarios

src/agentic_rag_mcp/deploy/battery.py  # + antv-chart, antv-infographic, chart-in-deck scenarios

DEPLOY.md                          # + data-posture section (FR-009)
```

**Structure Decision**: mirrors spec 009 — one new sidecar module (`antv/`) with its own error taxonomy, one additive bridge change (image inlining), and route + battery extensions on existing surfaces.

## Complexity Tracking

No violations to justify.
