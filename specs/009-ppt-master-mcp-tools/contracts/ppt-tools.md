# Contract — PPT-Master MCP Tools (Phase 1)

Interface contract for the five additive MCP tools on the AgenticRAG sidecar, plus the exports HTTP route. **Constitution I: additive only — the existing 16 tool schemas are byte-identical after this feature; `tools/list` grows 16 → 21.**

All successful results are JSON objects; all failures use the **error envelope** (FR-010):

```json
{
  "error": {
    "code": "PPT_CHECK_FAILED",
    "message": "01_cover.svg: <text> exceeds bounds ... (verbatim checker issue, ≤2000 chars)",
    "hint": "Rewrite page 1 with shorter lines or wider zones, then call ppt_check again."
  }
}
```

Error codes: `PPT_INVALID_PROJECT` · `PPT_INVALID_INPUT` · `PPT_MISSING_ICON` · `PPT_SCRIPT_TIMEOUT` · `PPT_SCRIPT_FAILED` · `PPT_CHECK_FAILED` · `PPT_EXPORT_BLOCKED` · `PPT_WORKSPACE_ERROR`. A tool NEVER returns an empty success where an error is truthful (Constitution IV).

## Tool schemas

### 1. `ppt_project_init`

```json
Input:  { "name": "string (1-64, url-safe)" }
Output: { "project_id": "dify_20261018_a1b2", "workspace": "/opt/ppt-master/projects/dify_20261018_a1b2", "max_pages": 5 }
Errors: PPT_INVALID_INPUT (bad name), PPT_WORKSPACE_ERROR (unwritable root), PPT_SCRIPT_FAILED
```

### 2. `ppt_icon_sync`

```json
Input:  { "project_id": "string", "icons": ["tabler-outline/star", "simple-icons/dify"] }
Output: { "synced": ["tabler-outline/star", "simple-icons/dify"], "missing": [] }
Errors: PPT_INVALID_PROJECT, PPT_MISSING_ICON (with the missing list + library search hint), PPT_SCRIPT_FAILED
```

### 3. `ppt_write_page`

```json
Input:  { "project_id": "string", "page_number": 1, "name": "overview", "svg": "<svg …complete page…>" }
Output: { "file": "svg_output/01_overview.svg", "bytes": 4182 }
Errors: PPT_INVALID_PROJECT, PPT_INVALID_INPUT (page out of 1..max_pages, bad name, SVG sanitization failure — message names the rejected construct), PPT_WORKSPACE_ERROR
```

### 4. `ppt_check`

```json
Input:  { "project_id": "string" }
Output: { "passing": true, "blocking_errors": 0, "warnings": 1, "details": ["[WARN] …"] }
        { "passing": false, "blocking_errors": 2, "warnings": 0, "details": ["[ERROR] 01_overview.svg: …verbatim issue + fix guidance…"] }
Errors: PPT_INVALID_PROJECT, PPT_SCRIPT_TIMEOUT, PPT_SCRIPT_FAILED (checker crash)
```

### 5. `ppt_export`

```json
Input:  { "project_id": "string" }
Output: { "file": "exports/dify_20261018_a1b2_104508.pptx", "url": "http://localhost:28080/exports/dify_20261018_a1b2/dify_20261018_a1b2_104508.pptx" }
Errors: PPT_INVALID_PROJECT, PPT_EXPORT_BLOCKED (pages failing check — includes the current blocking summary), PPT_SCRIPT_FAILED
```

## HTTP route (sidecar wrapper server)

`GET /exports/<project_id>/<filename>.pptx` → the file (200) or `404` honest not-found. Static root = configured `projects_root`; path traversal rejected; content-type `application/vnd.openxmlformats-officedocument.presentationml.presentation`. Posture: unauthenticated on the local-trust network, matching `/healthz`.

## Test-case matrix (Constitution II — defined before implementation)

Legend: U = unit (`test_ppt_bridge.py`), I = integration (`test_ppt_pipeline.py`), C = contract (`test_ppt_contract.py`).

| # | Case | Tier | Expected |
|---|------|------|----------|
| T01 | init with valid name | I | workspace exists, id matches `<slug>_<date>_<rand>` |
| T02 | init with empty / non-url-safe / >64-char name | U+C | `PPT_INVALID_INPUT` envelope |
| T03 | init when projects root unwritable | U | `PPT_WORKSPACE_ERROR` envelope |
| T04 | icon_sync with all-valid icons | I | `synced` complete, `missing` empty |
| T05 | icon_sync with unknown icon | I+C | `PPT_MISSING_ICON` listing missing names + search hint; no partial silent success |
| T06 | icon_sync on unknown project | C | `PPT_INVALID_PROJECT` |
| T07 | write_page with valid SVG | I | file persisted at `<NN>_<name>.svg` |
| T08 | write_page with `<script>` / `<foreignObject>` / `class` / event attr | U+C | `PPT_INVALID_INPUT` naming the rejected construct; file NOT persisted |
| T09 | write_page with page_number 0 / > max_pages | U+C | `PPT_INVALID_INPUT` |
| T10 | write_page oversized SVG (>256 KB) | U | `PPT_INVALID_INPUT` |
| T11 | write_page malformed XML | U | `PPT_INVALID_INPUT` |
| T12 | write_page path traversal via `name` (`../x`) | U+C | `PPT_INVALID_INPUT`; nothing escapes workspace |
| T13 | check on passing fixture pages | I | `passing: true`, `blocking_errors: 0` |
| T14 | check on failing fixture pages (text overflow) | I | `passing: false`, details contain verbatim fixable issue text |
| T15 | check on unknown project | C | `PPT_INVALID_PROJECT` |
| T16 | check when script exceeds timeout | U | `PPT_SCRIPT_TIMEOUT` envelope |
| T17 | export after passing check | I | file exists; opened with python-pptx has native text frames (not images); URL resolves 200 |
| T18 | export with failing pages | I+C | `PPT_EXPORT_BLOCKED` + blocking summary; NO file produced |
| T19 | export on unknown project | C | `PPT_INVALID_PROJECT` |
| T20 | revision flow: rewrite page → check → re-export | I | new artifact filename; old artifact still resolvable |
| T21 | concurrent init×2, interleaved writes | C | disjoint workspaces; no cross-contamination (SC-006) |
| T22 | tools/list before/after | C | 16 → 21; existing entries schema-identical (Constitution I) |
| T23 | every error code produces the envelope shape | C | envelope has code+message+hint; message non-empty |
| T24 | script stderr surfaced | U | failing script's stderr (truncated) appears in `message` |
| T25 | /exports route: valid file, missing file, traversal attempt | C | 200 / 404 / 400 respectively |

Fixtures: one passing one-page SVG and one failing SVG (known text overflow) live in `tests/fixtures/ppt/`.
