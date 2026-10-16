# Contract: OneDrive On-Demand Tools & Staleness Reminder

**Feature**: `specs/007-onedrive-on-demand` | **Frozen by**: Constitution I (FR-014)

New tools are additive; existing tool response shapes are frozen — only message *values* inside existing string fields change where the superseded design dictated sync behavior.

## Superseded behaviors (removed — spec 006, Constitution V)

| Removed | Replacement behavior |
|---|---|
| `sources_add(type:"onedrive")` returning "initial sync on next watcher cycle (≤5 min)" | Returns on-demand notice; **nothing is ever auto-synced** |
| `sources_auth` background thread calling `pipeline.sync_onedrive()` after sign-in | Sign-in only; source healthy; zero ingestion |
| `Watcher.sync_once()` onedrive branch (delta sync every 5 min) | Branch deleted; watcher issues zero Graph requests |
| `OneDriveSource.delta()/_get_url()/sync()` (delta-link machinery) | Replaced by `list_files()`, `resolve()`, `get_metadata()`, `download()` |
| `sources_sync(source_id)` syncing a onedrive source's drive | Honest on-demand notice (no sync) |

## Tool: `onedrive_list_files` (NEW)

**Purpose**: browse file metadata only — no content is downloaded.

**Input**:

```json
{ "source_id": "str", "search": "str = ''", "folder": "str = '/'", "limit": "int = 100" }
```

**Output (200)**:

```json
{
  "source_id": "str",
  "folder": "str",
  "files": [FileListingEntry, ...],     // data-model.md shape; empty [] when no match — honest, not an error
  "truncated": false                      // true when the bound cut the listing short
}
```

**Errors**: `source not found` (unknown id) · `source is not a onedrive source` · `Microsoft sign-in required` (source → degraded) · Graph-unreachable error string.

## Tool: `onedrive_embed_files` (NEW)

**Purpose**: download and embed ONLY the named files, one-time per call (FR-006).

**Input**:

```json
{ "source_id": "str", "files": ["str", ...] }   // paths and/or item ids; no count cap (FR-006); processed sequentially
```

**Output (200)** — always per-file outcomes, never all-or-nothing (FR-007, user decision):

```json
{
  "source_id": "str",
  "results": [EmbedOutcome, ...],       // exactly one entry per named file, request order preserved
  "embedded": 2, "updated": 0, "skipped": 1, "not_found": 0, "failed": 0
}
```

**Errors (tool-level)**: `source not found` · `source is not a onedrive source` · `Microsoft sign-in required` (source → degraded; nothing embedded).
**Per-file (in `results[]`)**: see EmbedOutcome — every `skipped/not_found/failed` carries a mandatory `reason` string; a mid-batch cloud throttling/error never aborts the remaining files (user decision 2026-10-11).

## Tool: `ask` (EXISTING — additive field)

All existing fields unchanged. New additive field on every response:

```json
{
  "...all existing fields unchanged...": "",
  "freshness_warnings": [StalenessReminder, ...]   // [] when none; reminder also appended to answer text
}
```

`kind` ∈ `stale | deleted`. Probe rules (FR-010/012/013): ≤5s total budget, parallel, cited onedrive files only, identity by item id, timeout → no reminder (answer unaffected), probe-auth-failure → source degraded (visible in `degraded_sources`) and no reminder. Local-file citations are never probed.

## Tool: `sources_add(type:"onedrive")` (EXISTING — message values change)

Response shape frozen: `{source_id, status, sync|message}`. Value changes: valid-token path returns `status:"ok"` with on-demand notice `"registered; on-demand source — use onedrive_list_files and onedrive_embed_files"`; `needs_auth` path unchanged in shape.

## Tool: `sources_auth` (EXISTING — no-sync semantics)

Shape frozen: `{status, sign_in_url?, user_code?, message?}`. After sign-in completes the source is healthy and **no ingestion occurs** (FR-002).

## Tool: `sources_sync` (EXISTING — onedrive notice)

Shape frozen: `{source_id: {...}}` map. A onedrive target returns `{"status":"on_demand","message":"OneDrive sources are on-demand; use onedrive_embed_files to embed chosen files."}` — never a sync (FR-004).

## Error-response matrix (single source of truth)

| Scenario | Response |
|---|---|
| list/embed with expired token | Error `Microsoft sign-in required`; source → `degraded`; other sources unaffected |
| embed names a missing path | That file: `{request, locator:null, status:"not_found", reason:"no file at this path/id"}`; others proceed |
| embed names a PNG / 80 MB file | `{status:"skipped", reason:"unsupported format: .png"}` / `{"...file too large: 80 MB > 50 MB"}` |
| Graph 429 on file 2 of 5 | Files 1 succeeded, 2 `failed: "cloud rate-limited — re-run embed for this file"`, 3–5 proceed |
| probe times out at 5s | Answer returned normally, `freshness_warnings: []`, debug log only |
| cited file deleted in cloud | Answer + `freshness_warnings:[{kind:"deleted", message:"...last available version"}]` |
| probe hits expired token | Answer + `degraded_sources` includes the source; no reminder fabricated |

## Test matrix (contract + unit + integration — every row is a named test)

| # | Level | Test case | Asserts |
|---|-------|-----------|---------|
| C1 | contract | `onedrive_list_files` response shape | fields/types incl. `truncated` on over-bound listing |
| C2 | contract | `onedrive_embed_files` response shape | per-file `results[]` + counters agree |
| C3 | contract | `ask` keeps all frozen fields | existing field set identical + additive `freshness_warnings` present (empty ok) |
| C4 | contract | `sources_add` onedrive notices | shape frozen; message values = on-demand |
| C5 | contract | `sources_auth` no-sync | sign-in completion does not change document count |
| C6 | contract | `sources_sync` onedrive | on-demand notice, no drive sync attempted |
| U1 | unit | listing recursion + pagination + filter | nested folders found; `@odata.nextLink` followed; substring filter; empty [] honest |
| U2 | unit | resolve path vs id; 404 → not_found | one Graph call per file; id stored as locator |
| U3 | unit | embed outcomes + no-cap sequential | 60-file list processed in order, all outcomes reported |
| U4 | unit | dedup idempotent; changed content evicts | re-embed same content → no dup; changed → orphan vectors deleted |
| U5 | unit | snapshot write/read round-trip | `origins.snapshot` set; `item_id == locator` invariant |
| U6 | unit | probe: stale / unchanged / deleted / timeout / auth-fail | reminder, none, deleted-note, none+answer-ok, degraded+none |
| U7 | unit | probe identity survives rename | id probe → reminder correct though path changed |
| U8 | unit | migration: pending set only; idempotent | second run = no-op; deleted-at-migration keeps copy + honest reason; auth-expired → retried; empty = no-op |
| I1 | integration | SC-001 connect → 0 docs | no ingest after auth + watcher cycles |
| I2 | integration | SC-002 embed 3 of 50 | exactly 3 searchable; others never return |
| I3 | integration | SC-003 reminder on ask | cloud edit → reminder same turn, timestamps included |
| I4 | integration | SC-004 explicit update | re-embed → new content only; reminder gone |
| I5 | integration | watcher isolation | registered onedrive source + watcher cycle → zero Graph requests (mock counts calls) |
| I6 | integration | SC-005 local regression | local_folder auto-sync tests unchanged and green |
| X1 | unit | error taxonomy rows | every row of the error-response matrix above |

**Gate**: 100% green before completion (Constitution II); superseded 006 sync tests are deleted in the same change set — never weakened.
