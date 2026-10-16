# Data Model: OneDrive On-Demand Embedding with Staleness Reminder

**Feature**: `specs/007-onedrive-on-demand` | **Plan**: [plan.md](plan.md)

All entities live in the existing SQLite state store or are tool-level value shapes. No new tables; one new nullable column.

## Storage changes (SQLite state store)

### `origins` table — extended

| Column | Type | Rule |
|--------|------|------|
| `document_id` | TEXT NOT NULL | FK → documents, unchanged |
| `source_id` | TEXT NOT NULL | unchanged |
| `locator` | TEXT NOT NULL | for onedrive origins: the Graph **item id** (cloud-stable identity); `UNIQUE(source_id, locator)` unchanged |
| `last_seen_at` | TEXT NOT NULL | set by embed/migration, unchanged semantics |
| `snapshot` | TEXT NULL | **NEW** — JSON `FreshnessSnapshot`, present for every successfully embedded OneDrive file; NULL = legacy (pending migration) or migration-failed |

Validation: `snapshot` is written only inside the embed transaction; its `item_id` MUST equal the row's `locator`.

### `sources` table — unchanged schema

`sync_state` for onedrive sources becomes unused and is not read or written by any new code path (kept only because the column is shared with local/sqlite sources). `health` transitions unchanged (`healthy | degraded | down`).

## StateStore — new/changed methods

| Method | Signature | Behavior |
|--------|-----------|----------|
| `set_origin_snapshot` | `(source_id, locator, snapshot: dict) -> None` | Upsert `origins.snapshot`; called at embed/migration success |
| `get_origin_snapshot` | `(source_id, locator) -> dict \| None` | Read one snapshot |
| `origins_for_document` | `(doc_id) -> list[{source_id, locator, snapshot}]` | Map cited document → origins (probe entry point) |
| `onedrive_origins_without_snapshot` | `(source_id) -> list[{locator, document_id}]` | Migration pending set; empty = no-op migration |

## Tool-level value shapes

### FileListingEntry (onedrive_list_files items)

| Field | Type | Rule |
|-------|------|------|
| `locator` | str | Graph item id |
| `title` | str | file name incl. extension |
| `path` | str | full drive path, e.g. `/Documents/report.docx` |
| `size` | int | bytes |
| `last_modified` | str | ISO-8601 UTC |
| `embeddable` | bool | extension ∈ {pdf, docx, xlsx, pptx} **and** size ≤ source `max_file_size_mb` |

### EmbedOutcome (onedrive_embed_files per-file results)

| Field | Type | Rule |
|-------|------|------|
| `request` | str | the path/id exactly as the user named it |
| `locator` | str \| null | Graph item id when resolved; null when not found |
| `status` | enum | `embedded \| updated \| skipped \| not_found \| failed` — exactly one per named file |
| `reason` | str \| null | mandatory for `skipped/not_found/failed` (see error taxonomy); null for embedded/updated |

### FreshnessSnapshot (origins.snapshot JSON)

| Field | Type | Rule |
|-------|------|------|
| `item_id` | str | MUST equal origin locator (validation above) |
| `last_modified` | str | cloud last-modified of the content actually embedded |
| `etag` | str \| null | optional change token when Graph provides one |
| `embedded_at` | str | embed time, ISO-8601 UTC |

### StalenessReminder (ask response `freshness_warnings[]` + answer-text suffix)

| Field | Type | Rule |
|-------|------|------|
| `title` | str | file name at embed time |
| `path` | str | last known drive path |
| `locator` | str | Graph item id (usable for the update command) |
| `embedded_at` | str | from snapshot |
| `modified_at` | str | current cloud timestamp (absent for the deleted-cloud variant) |
| `kind` | enum | `stale \| deleted` |
| `message` | str | human-readable reminder (research.md D5 templates) |

## Source config (OneDriveSourceConfig) — carried from spec 006, sync-only fields dropped

| Field | Type | Default | Rule |
|-------|------|---------|------|
| `client_id` | str | required | Azure app registration |
| `tenant_id` | str | `"common"` | unchanged |
| `client_secret` | str | `""` | app-only auth path, unchanged |
| `user` | str | `""` | app-only target user, unchanged |
| `folder_path` | str | `"/"` | **listing scope root** (browse starts here) |
| `include_subfolders` | bool | `true` | listing recursion depth (root-only when false) |
| `max_file_size_mb` | int | `50` | embed skip bound, unchanged |

## State transitions

### Source health (onedrive)

```
registered ──(no token)──> needs_auth ──(sources_auth completes)──> healthy
healthy ──(expired token on user-initiated list/embed/probe)──> degraded(sign-in required)
degraded ──(sources_auth completes)──> healthy
```

The watcher never transitions onedrive health (FR-003): only user-initiated operations and probes do.

### Origin/snapshot lifecycle

```
(named file embedded) ──> origin upserted + snapshot written ──> tracked
tracked ──(re-embed, same content)──> tracked (no duplicate, outcome=updated)
tracked ──(re-embed, changed content)──> doc swapped, orphan vectors deleted, snapshot refreshed
legacy origin (snapshot NULL) ──(startup migration success)──> tracked
legacy origin ──(migration failure: deleted/throttle/auth)──> legacy (retried next startup)
tracked ──(file deleted in cloud)──> tracked + deleted-cloud note on citations (no data change)
(source removed) ──> origins + documents + vectors dropped (existing behavior)
```

## Error taxonomy (binding mapping)

| Condition | Error type | Tool-visible result |
|-----------|-----------|---------------------|
| Token missing/expired on list/embed/probe | `SourceAuthError` | Error response "Microsoft sign-in required"; source health → `degraded` |
| Graph 429 / 5xx / network on resolve or download | `ProviderError` | Per-file `failed` + reason; batch continues |
| Path/id 404 on resolve | — (handled) | Per-file `not_found` + reason `no file at this path/id` |
| Unsupported extension / oversize | — (handled) | Per-file `skipped` + explicit reason |
| Missing download URL on an otherwise-resolved item | — (handled) | Per-file `failed` + reason `no download URL` |
| Probe timeout / budget exhaustion | — (handled) | No reminder; answer returned; debug log |
| Probe 404 by item id | — (handled) | `deleted` reminder kind ("last available version") |
| Unknown source_id on new tools | `NotFoundError` | Error response "source not found" |
| Non-onedrive source_id on new tools | `NotFoundError` | Error response "source is not a onedrive source" |

Never fabricated, never silent: every non-success path above has a named test (see [contracts/onedrive-on-demand.md](contracts/onedrive-on-demand.md) test matrix).
