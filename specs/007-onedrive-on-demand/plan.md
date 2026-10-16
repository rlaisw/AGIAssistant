# Implementation Plan: OneDrive On-Demand Embedding with Staleness Reminder

**Branch**: `007-onedrive-on-demand` | **Date**: 2026-10-11 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/007-onedrive-on-demand/spec.md`

## Summary

Replace the superseded OneDrive auto-sync machinery (spec 006: post-auth full sync, 5-minute watcher polling, delta-link continuous sync) with on-demand operations: a metadata-only `onedrive_list_files` tool, an explicit `onedrive_embed_files` tool that embeds only the named files, an answer-time staleness reminder driven by bounded metadata-only freshness probes of cited files (5-second budget, cloud-stable item identifiers), a freshness snapshot recorded per embedded file, and a one-time idempotent migration that re-embeds legacy snapshot-less documents. Zero new dependencies; `local_folder`/`sqlite` auto-sync untouched. Test cases and error handling are first-class deliverables of this plan (see Project Structure → tests and [contracts/onedrive-on-demand.md](contracts/onedrive-on-demand.md)).

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: No new deps — existing `msal` (auth), `httpx` (HTTP), `mcp` SDK ≥1.12, `lancedb`, `sentence-transformers` (all installed)

**Existing foundation (verified in code)**:

- `sources/graph_auth.py` (81 lines) — `GraphAuth` (device flow, per-source token cache, silent refresh) + `ClientCredentialsAuth` — **UNCHANGED**
- `sources/onedrive.py` (169 lines) — `GraphBase._get()` with `@odata.nextLink` pagination, `download()`, and the delta-sync machinery (`delta()`, `_get_url()`, `sync()`) — delta machinery **REPLACED** by listing/resolution/probe methods
- `ingestion/pipeline.py` (156 lines) — `sync_local_folder()`, `sync_sqlite()` **UNCHANGED**; `sync_onedrive()` **REPLACED** by `embed_onedrive_files()` + one-time migration
- `ingestion/watchers.py` (66 lines) — `sync_once()` onedrive branch **DELETED** (watcher must make zero Graph requests; FR-003)
- `store/state.py` — `origins(source_id, locator UNIQUE)` table gains a nullable `snapshot` column; new accessor methods (see [data-model.md](data-model.md))
- Parsers (PDF/DOCX/XLSX/PPTX), content-hash dedup, chunking, embedding, `VectorStore`, eviction — **reused unchanged**
- `server.py` — `sources_add`/`sources_auth`/`sources_sync` onedrive wiring **revised**; `ask()` gains the freshness probe + additive `freshness_warnings` field

**Graph API endpoints used**:

| Purpose | Endpoint | Notes |
|---|---|---|
| List folder children | `GET /me/drive/root:{path}:/children` | recursive descent, `@odata.nextLink` pagination, `$select` metadata fields |
| Resolve embed path | `GET /me/drive/root:{path}` | one call → id, `@microsoft.graph.downloadUrl`, `lastModifiedDateTime`, size |
| Resolve embed item id | `GET /me/drive/items/{id}` | same fields; also the freshness probe call (`$select=id,lastModifiedDateTime,eTag,name`) |
| Download file | `GET {item.downloadUrl}` | pre-authenticated URL, existing `download()` reused |

**Storage**: freshness snapshot per origin — nullable `origins.snapshot` JSON column (`{item_id, last_modified, etag?, embedded_at}`); token cache unchanged at `~/.config/agentic-rag-mcp/tokens/{source_id}.json`

**Testing**: pytest — unit (Graph mocked at the httpx boundary), contract (tool response shapes pinned), integration (pipeline + state real, Graph mocked). Full error-path matrix in [contracts/onedrive-on-demand.md](contracts/onedrive-on-demand.md).

**Performance Goals**: freshness probe ≤5s total budget (parallel, per-request timeout, skip reminder on expiry); listing paginated with a default page bound

**Constraints**: tool response shapes frozen (Constitution I / FR-014); honest errors everywhere (FR-007/013); watcher makes zero Graph requests for onedrive sources (FR-003); no per-command file-count cap (sequential processing, FR-006)

**Scale/Scope**: single-user server; typical embed batches <10 files; probe limited to cited files (typically 1–3)

## Constitution Check

| Principle | Status | Evidence |
|---|---|---|
| I. Contract Preservation | PASS | FR-014: new tools and the `freshness_warnings` field are additive; `ask`/`sources_*` response shapes unchanged; only message *values* inside existing fields change (documented in Supersedes) |
| II. Tests-First | PASS | RED tests enumerated per FR below (unit/contract/integration); superseded spec-006 sync tests deleted, never weakened (SC-006) |
| III. Minimal Dependencies | PASS | Zero new deps — msal + httpx + stdlib `ThreadPoolExecutor` for the bounded parallel probe |
| IV. Honest Answers | PASS | Full error matrix (spec edge cases → FR-007/013): per-file skip reasons, probe timeout/auth/deleted semantics, migration honesty, no silent skips |
| V. Spec-Driven Replacement | PASS | This spec supersedes 006's sync design: `delta()`/`_get_url()`/`sync()`, post-auth sync trigger, watcher onedrive branch, and `sync_onedrive()` are deleted — no dead code |

## Project Structure

### Documentation (this feature)

```text
specs/007-onedrive-on-demand/
├── plan.md                       # This file
├── research.md                   # Phase 0 output — decisions D1–D10 incl. error handling + test strategy
├── data-model.md                 # Phase 1 output — snapshot column, StateStore methods, error taxonomy
├── contracts/onedrive-on-demand.md # Phase 1 output — tool schemas, error responses, per-tool test cases
├── quickstart.md                 # Phase 1 output — runnable validation incl. error-path scenarios
├── checklists/requirements.md
└── tasks.md                      # Phase 2 (/speckit.tasks) — NOT created by this command
```

### Source Code (repository root)

```text
src/agentic_rag_mcp/
├── server.py                     # REVISED: + onedrive_list_files, onedrive_embed_files tools;
│                                 #   ask() freshness probe + freshness_warnings; sources_add onedrive
│                                 #   returns on-demand notice (no sync); sources_auth drops post-sign-in
│                                 #   sync trigger; sources_sync onedrive honest notice; startup migration
├── sources/
│   ├── graph_auth.py             # UNCHANGED
│   ├── onedrive.py               # REPLACED: delete delta/_get_url/sync; add list_files(search, folder,
│                                 #   limit), resolve(path_or_id), get_metadata(item_id), keep download()
│   └── onedrive_freshness.py     # NEW: bounded parallel probe (5s budget) comparing snapshots for
│                                 #   cited docs; returns StalenessReminder list or honest empty
├── ingestion/
│   ├── pipeline.py               # REVISED: sync_onedrive() → embed_onedrive_files(source_id, source,
│                                 #   files) with per-file outcomes; + migrate_onedrive_sources() one-time
│                                 #   idempotent migration; local_folder/sqlite methods UNCHANGED
│   └── watchers.py               # REVISED: delete onedrive branch — zero Graph calls in watcher
└── store/
    └── state.py                  # EXTENDED: origins.snapshot nullable column + set_origin_snapshot(),
                                  #   get_origin_snapshot(), origins_for_document(doc_id),
                                  #   onedrive_origins_without_snapshot()

tests/
├── unit/
│   ├── test_onedrive.py          # REVISED (supersede delta tests): listing recursion/pagination/filter/
│                                 #   empty-honest; resolve path-vs-id; embed per-file outcomes
│                                 #   (embedded/updated/skipped-reasons/not-found); no-cap sequential;
│                                 #   dedup idempotent; changed-content eviction
│   └── test_onedrive_freshness.py # NEW: snapshot record/compare; stale → reminder; unchanged → none;
│                                 #   deleted-by-id → last-version note; timeout → no reminder, answer
│                                 #   unaffected; probe auth fail → source degraded, no fabricated
│                                 #   reminder; rename keeps identity (id probe)
├── unit/test_migration.py        # NEW (or fold into pipeline tests): migration embeds only snapshot-less
│                                 #   legacy docs; idempotent second run = no-op; deleted-at-migration keeps
│                                 #   copy + honest reason; expired token → honest, retried next startup;
│                                 #   no legacy docs → no-op
├── contract/
│   ├── test_onedrive_contract.py # REVISED: onedrive_list_files + onedrive_embed_files response shapes;
│                                 #   sources_add onedrive message; sources_sync onedrive notice;
│                                 #   ask response keeps all fields + additive freshness_warnings
│   └── test_edge_cases.py        # EXTENDED: embed with expired token → honest sign-in-required, source
│                                 #   degraded; other sources unaffected
└── integration/
    └── test_onedrive_on_demand.py # NEW: end-to-end with mocked Graph — connect→0 docs (SC-001);
                                   #   embed 3 of 50 → exactly 3 searchable (SC-002); staleness reminder
                                   #   on ask (SC-003); explicit update → new content only (SC-004);
                                   #   watcher cycle makes zero Graph requests with onedrive source
                                   #   registered; local_folder regression unchanged (SC-005)
```

### User-managed files (not committed)

```text
~/.config/agentic-rag-mcp/tokens/{source_id}.json   # per-source MSAL token cache (unchanged)
~/.config/agentic-rag-mcp/config.toml               # existing (no new section needed)
```

## Complexity Tracking

No constitution violations. Complexity hotspots:

1. **Answer-time freshness probe** — parallel, 5-second budget, non-blocking on transient failure, honest degraded marking on auth failure, identity by cloud-stable item id (research.md D4/D5). Bounded blast radius: probe touches only cited onedrive docs.
2. **One-time migration idempotency** — the migration set is defined by absence of a snapshot, so success is self-removing and failures retry naturally on next startup (research.md D7).
3. **Supersede completeness** — every spec-006 auto-sync code path and its tests must be deleted in the same change set (Constitution V), while the 006-era *contract* tests for unchanged tools stay green.
