# Research: OneDrive On-Demand Embedding with Staleness Reminder

**Feature**: `specs/007-onedrive-on-demand` | **Date**: 2026-10-11

All decisions resolved against the spec (FR-001..FR-016), the existing code (verified), and Microsoft Graph v1.0 documented semantics. No NEEDS CLARIFICATION remained entering Phase 0 — the spec's Clarifications section carries eight ratified user decisions.

## D1: Metadata-only listing — recursive `children` traversal, not delta-as-listing

**Decision**: list files via `GET /me/drive/root:{path}:/children`, recursing into `folder` facets, following `@odata.nextLink`, requesting only metadata fields via `$select` (`id,name,parentReference,path,size,file,lastModifiedDateTime`), with an optional case-insensitive name-substring filter and a default result bound (100) that the caller may raise.

**Rationale**: `children` is folder-scoped — it structurally cannot enumerate the whole drive unless asked to; the superseded `delta` endpoint's first call (no cursor) is drive-wide enumeration by design, which is exactly the behavior FR-005 forbids. Pagination already exists in `GraphBase._get()` (kept from spec 006).

**Alternatives considered**: (a) delta endpoint with `$select` — rejected: drive-wide first enumeration violates the on-demand invariant even if we discarded the items; (b) `/me/drive/special/documents` — rejected: misses non-Documents folders; (c) search endpoint `GET /me/drive/root/search(q)` — rejected as primary (server-side relevance is opaque; a plain substring filter on the real listing is predictable and honest), kept as a non-goal.

## D2: Embed file resolution — one call per file, path or item id

**Decision**: each entry in the `files` list is resolved by exactly one Graph call: paths (leading `/` optional) via `GET /me/drive/root:{path}`, ids via `GET /me/drive/items/{id}`. The response provides id, name, size, `lastModifiedDateTime`, and `@microsoft.graph.downloadUrl` in a single round trip — resolution, size-cap check, snapshot capture, and download URL acquisition are one step. 404 from resolution is the honest "not found" per-file reason.

**Rationale**: no listing pass is required before embedding (a user may paste a path directly); one call minimizes Graph quota; the returned id is the locator stored on the origin, so future probes and updates are identity-stable even after renames.

**Alternatives considered**: resolving via the listing tool's cache — rejected (no cache exists; listings are metadata views, not a store); resolving paths via `/me/drive/root/children` walks — rejected (multi-call, ambiguous with duplicate names).

## D3: Freshness snapshot — per-origin column, not per-source sync_state

**Decision**: add a nullable `snapshot` JSON column to the existing `origins` table; store `{item_id, last_modified, etag?, embedded_at}` where `last_modified` is the cloud timestamp of the content actually embedded. StateStore gains `set_origin_snapshot()`, `get_origin_snapshot()`, `origins_for_document()`, and `onedrive_origins_without_snapshot()`.

**Rationale**: freshness is a property of the (source, locator) origin — the same table that already enforces `UNIQUE(source_id, locator)` and drives eviction. A per-source blob would grow unboundedly with embedded files and race with sync_state semantics; a new table adds a join for no benefit (Constitution III: reuse the ladder).

**Alternatives considered**: (a) `sources.sync_state` map — rejected: unbounded, abuses sync semantics; (b) new `snapshots` table — rejected: the origin row is already the right grain; (c) storing in LanceDB metadata — rejected: state DB is the system of record for origins/documents, vectors are derived data.

## D4: Staleness probe — bounded parallel, identity by item id, honest outcomes

**Decision**: after synthesis, `ask()` maps cited `document_id`s to origins via `origins_for_document()`; for origins whose source is a onedrive source, it probes `GET /me/drive/items/{item_id}?$select=id,lastModifiedDateTime,eTag,name` — run in a `ThreadPoolExecutor(max_workers=4)`, each request with a 4-second timeout, and the whole probe capped by a 5-second budget. Outcomes: cloud `lastModifiedDateTime` > snapshot → reminder; not found by id → "deleted — embedded copy is the last version" note; transient error/timeout → no reminder, answer unaffected; auth error → source marked degraded, no reminder (the existing `degraded_sources` field surfaces it). The reminder is appended to the answer text and exposed as an additive `freshness_warnings` list on the `ask` response.

**Rationale**: user decision 2026-10-11 fixed the 5-second budget; item-id identity (D2/D3) makes renames/moves invisible to staleness (id persists) while an unfindable id genuinely means deleted. Threads (not asyncio) match the synchronous FastMCP server; a process pool would be heavyweight for 1–3 requests.

**Alternatives considered**: (a) asyncio probe — rejected: the server path is synchronous; converting the `ask` pipeline to async would ripple far beyond this feature; (b) sequential probes — rejected: 3 cited files × 4s worst case would blow the 5s budget; (c) probe at session-save time — rejected: reminder must appear on the answer the user is reading (SC-003, same conversation turn).

## D5: Staleness reminder content — timestamps + actionable identifier

**Decision**: each reminder carries `title`, `path` (last known), `item_id`, `embedded_at`, `modified_at`, and a message: `"'{title}' was modified in OneDrive on {modified_at} UTC — after it was embedded on {embedded_at} UTC. The answer above is from the older copy. To update it, ask to re-embed '{path}' (or use item {item_id})."` Deleted-cloud notes: `"'{title}' no longer exists in OneDrive; the embedded copy from {embedded_at} UTC is the last available version."`

**Rationale**: the identifier lets the follow-up update command resolve even if the path was renamed; both timestamps make the staleness verifiable by the user; the message never claims staleness without evidence (Constitution IV).

**Alternatives considered**: vague "may be outdated" without timestamps — rejected (unfalsifiable, low trust).

## D6: Watcher — onedrive branch deleted, not skipped

**Decision**: delete the `onedrive` handling from `Watcher.sync_once()` entirely. The watcher iterates `local_folder` and `sqlite` sources only; a registered onedrive source produces zero Graph traffic from the watcher. `sources_sync(source_id)` on a onedrive source returns `{source_id: {"status": "on_demand", "message": "OneDrive sources are on-demand; use onedrive_embed_files to embed chosen files."}}` — the honest notice FR-004 requires.

**Rationale**: a "skip with a flag" branch is dead code waiting to be re-enabled by accident (Constitution V). Integration test pins zero Graph calls during watcher cycles with a registered onedrive source.

**Alternatives considered**: keep sync-on-demand behind `sources_sync` — rejected: it is the superseded behavior in disguise.

## D7: Migration — snapshot-absence defines the pending set; idempotent by construction

**Decision**: at server startup (`build_server`, before the watcher starts), `migrate_onedrive_sources()` queries `onedrive_origins_without_snapshot()`; each pending origin is resolved by its stored locator (the Graph item id) and re-embedded through `embed_onedrive_files()` — refreshing content and recording the snapshot. Success removes the origin from the pending set automatically; per-file failures (deleted in cloud, throttled, auth expired) are logged honestly and retried on the next startup because the origin still lacks a snapshot. No migration flag is stored.

**Rationale**: user decision 2026-10-11 (Option C). Defining the pending set by absence of a snapshot makes the migration idempotent, crash-safe, and self-healing after re-auth — with zero stateful "migration done" bookkeeping. The migration only touches documents already in the KB (FR-016's boundary).

**Alternatives considered**: (a) no migration (treat legacy as unverifiable) — rejected by user decision; (b) one-shot flag + fixed migration table — rejected: extra state, extra failure mode; (c) migrate lazily on first citation — rejected: reminder latency and surprise mid-conversation downloads of *multiple* files violate the one-time-per-command feel.

## D8: `sources_auth` — keep non-blocking device flow, drop the sync trigger

**Decision**: the existing pattern stays — initiate the device flow, return URL+code immediately, complete on a background thread, mark healthy on success — but the thread no longer calls `pipeline.sync_onedrive()` (deleted). After sign-in the user is authenticated and nothing has been ingested (FR-002).

**Rationale**: the flow's ergonomics are proven; only the post-auth sync violates the new invariant. Removing one call is the shortest working diff.

**Alternatives considered**: blocking sign-in — rejected (D3 research from spec 006 still applies).

## D9: Error handling — one honest per-file outcome model everywhere

**Decision**: every multi-file operation (embed, migration) returns per-file outcomes from a single outcome enum — `embedded | updated | skipped | not_found | failed` — each with a machine-checkable `reason` string. The mapping from the existing error taxonomy:

| Failure | Raised as | Surfaced as |
|---|---|---|
| No/invalid token at list/embed/probe | `SourceAuthError` | Tool error "Microsoft sign-in required" + source → `degraded` (existing pattern) |
| Graph 429 mid-batch | `ProviderError` | Per-file `failed`, reason `cloud rate-limited — re-run embed for this file`; batch continues (user decision 2026-10-11) |
| Graph 5xx/network mid-batch | `ProviderError` | Per-file `failed`, reason with the underlying error; batch continues |
| Resolution 404 | not found | Per-file `not_found`, reason `no file at this path/id` |
| Unsupported extension | — | Per-file `skipped`, reason `unsupported format: {ext}` (cap: existing `SUPPORTED_EXTENSIONS`) |
| Over `max_file_size_mb` | — | Per-file `skipped`, reason with sizes (existing cap default 50 MB) |
| Probe timeout/budget exceeded | — | No reminder; answer unaffected (log line only) |
| Probe 404 by id | — | `last available version` note (genuinely deleted — id identity, D4) |
| Probe auth failure | `SourceAuthError` | Source → `degraded`; reminder suppressed; `degraded_sources` reports it |

**Rationale**: reuses the existing `RagError` family — no new exception types; per-file outcomes generalize the honest-skip pattern local_folder already proves; batching policy follows the user's continue-on-failure decision.

**Alternatives considered**: aborting on first error — rejected (user decision); silent continue — rejected (Constitution IV).

## D10: Test strategy — supersede in place, pin the invariants

**Decision**: three layers, Graph mocked at the httpx boundary (no network in CI, per constitution quality gates):

1. **Unit** — `test_onedrive.py` (rewritten): listing (recursion, pagination, filter, empty-honest, auth error), resolve (path vs id, 404), embed outcomes (per-file statuses, reasons, no-cap sequential, dedup idempotent, changed-content eviction with orphan cleanup); `test_onedrive_freshness.py`: snapshot round-trip, stale/unchanged/deleted/timeout/auth-fail/rename cases; `test_migration.py`: embeds only pending set, idempotence, deleted-at-migration, auth-expired retry, no-op.
2. **Contract** — pin response shapes: `onedrive_list_files`, `onedrive_embed_files`, `ask` (all existing fields + additive `freshness_warnings`), `sources_add` onedrive, `sources_auth` (no-sync semantics), `sources_sync` onedrive notice. Superseded shape tests from 006 are deleted in the same change set.
3. **Integration** — `test_onedrive_on_demand.py`: SC-001 connect → 0 docs; SC-002 embed 3 of 50 → exactly 3 searchable; SC-003 reminder on ask after cloud edit; SC-004 explicit update → new content only, reminder gone; watcher-isolation: registered onedrive source + full watcher cycle → zero Graph requests; SC-005 local_folder regression.

**Rationale**: each acceptance scenario in the spec maps to at least one named test; invariants that make this feature what it is (zero auto-ingestion, watcher isolation, probe honesty) get dedicated tests rather than being implied.

**Alternatives considered**: live-Graph smoke tests — rejected for CI (network, credentials); kept as quickstart.md manual verification instead.
