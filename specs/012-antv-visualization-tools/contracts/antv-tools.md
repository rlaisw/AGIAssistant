# Contract — AntV Visualization Tools (Phase 1)

Interface contract for the two additive MCP tools and the infographic route. **Constitution I: additive only — the existing 21 tool schemas are frozen; `tools/list` grows 21 → 23.**

Error envelope (uniform with the ppt tools, Constitution IV):

```json
{ "error": { "code": "ANTV_INVALID_TYPE | ANTV_INVALID_INPUT | ANTV_SERVICE_ERROR | ANTV_SERVICE_TIMEOUT",
             "message": "<verbatim/precise>", "hint": "<agent-actionable>" } }
```

## Tool schemas

### 1. `antv_chart`

```json
Input:  { "chart_type": "bar", "data": [ { "category": "A", "value": 30 } ], "title": "Monthly volume" }
Output: { "chart_type": "bar", "image_url": "https://…/original", "usage": "Embed image_url in your markdown answer as ![chart](<url>). For PPT pages, embed it as <image href=…> — the deck pipeline makes it self-contained." }
Errors: ANTV_INVALID_TYPE (with the supported list), ANTV_INVALID_INPUT (empty/oversized/malformed data, title > 200), ANTV_SERVICE_ERROR (service success=false or non-200, verbatim message), ANTV_SERVICE_TIMEOUT
```

`chart_type` supported list (curated; the tool's docstring carries the selection guidance so agents choose without prompting): line, area, bar, column, pie, radar, scatter, histogram, funnel, treemap, sankey, dual-axes, word-cloud, boxplot, venn, liquid + diagram types (flow, mind-map, fishbone, organization, network) as verified against the service. Geography types excluded by design.

### 2. `antv_infographic`

```json
Input:  { "description": "infographic list-row-simple-horizontal-arrow\ndata\n  lists\n    - label Step 1 …" }
Output: { "url": "http://<host>:28080/infographics/<id>/", "usage": "Give the user the url as a markdown link — it opens the rendered infographic in a browser." }
Errors: ANTV_INVALID_INPUT (empty syntax, > 64 KB), storage failures → honest envelope
```

## HTTP route (sidecar wrapper)

| Route | Success | Errors |
|---|---|---|
| `GET /infographics/<id>/` | 200 `text/html` — page loads the engine from CDN and renders the stored syntax | 404 unknown id; 400 malformed id |

## Deck self-containment (bridge change)

`ppt_write_page` accepts remote `<image href="https://…">` in submitted SVG and **must** inline every one as a `data:` URI at write time (fetch capped by `[antv] max_inline_image_bytes`, default 2 MB). Failure or oversize → `PPT_INVALID_INPUT` naming the href; the page is not persisted. The sanitizer's existing data-URI allowance is the enabling rule.

## Config contract

| Key | Env | Default |
|---|---|---|
| `[antv] chart_service_url` | `ANTV_CHART_SERVICE_URL` | `https://antv-studio.alipay.com/api/gpt-vis` |
| `[antv] chart_timeout_s` | — | `30` |
| `[antv] max_inline_image_bytes` | — | `2097152` |
| `[antv] infographic_max_syntax_bytes` | — | `65536` |

## Test-case matrix (Constitution II — defined before implementation)

Legend: U = unit (`test_antv_tools.py`), I = integration (`test_antv_pipeline.py`, network-gated), C = contract (`test_antv_contract.py`).

| # | Case | Tier | Expected |
|---|------|------|----------|
| A01 | antv_chart with valid bar data (fake service) | C | `{chart_type, image_url, usage}` shape |
| A02 | unsupported chart_type (incl. a geo type) | U+C | `ANTV_INVALID_TYPE` naming the supported set |
| A03 | empty / oversized / malformed data | U+C | `ANTV_INVALID_INPUT` per rule |
| A04 | service returns success=false | U+C | `ANTV_SERVICE_ERROR` with verbatim message |
| A05 | service timeout | U | `ANTV_SERVICE_TIMEOUT` |
| A06 | live chart call returns a serving image URL | I | image_url HTTP 200, image content-type |
| A07 | antv_infographic valid syntax → url; route serves HTML containing the syntax + engine reference | U+C | 200 `text/html` |
| A08 | empty / oversized syntax | U+C | `ANTV_INVALID_INPUT` |
| A09 | infographic route unknown id / malformed id | C | 404 / 400 |
| A10 | write_page inlines a remote image (fake fetch) as data URI | U | persisted SVG contains `data:image/…`, no `https://` image hrefs remain |
| A11 | inline fetch failure / oversize | U+C | `PPT_INVALID_INPUT` naming the href; nothing persisted |
| A12 | deck with a remote chart image exports self-contained | I | exported pptx media contains the image bytes; no hotlink in slide XML |
| A13 | tools/list 21 → 23, existing entries unchanged | C | additive-only proven (Constitution I) |
| A14 | every error code → envelope shape with non-empty hint | C | uniform honesty |
| A15 | existing suites stay green (ppt, completion, deploy) | C | full suite + battery unchanged-behavior guard |
| A16 | battery: antv-chart scenario | battery | tool call → image URL serves |
| A17 | battery: antv-infographic scenario | battery | route serves rendered HTML |
| A18 | battery: chart-in-deck scenario | battery | exported deck contains chart bytes |

Fixtures: a small valid chart payload and infographic syntax under `tests/fixtures/antv/`.
