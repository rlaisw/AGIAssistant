# Tasks: OneDrive On-Demand Embedding with Staleness Reminder

**Input**: Design documents from `specs/007-onedrive-on-demand/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/onedrive-on-demand.md, quickstart.md

**Tests**: REQUIRED — Constitution II (Tests-First) mandates a runnable RED check before every implementation task. Test matrix C1–C6/U1–U8/I1–I6/X1 in [contracts/onedrive-on-demand.md](contracts/onedrive-on-demand.md) is the source of truth; every RED task below names its matrix rows.

**Organization**: Tasks grouped by user story (spec.md US1–US5) plus foundational and cross-cutting phases. Every story is independently testable at its checkpoint.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1–US5)
- Exact file paths in every description

## Path Conventions

Single project: `src/agentic_rag_mcp/` and `tests/` at repository root (per plan.md).

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish a known-green baseline before the supersede change set.

- [X] T001 Run the full pytest suite (`pytest -q`) and confirm 100% green baseline; record the count before any change (Constitution II gate for the RED workflow that follows)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Snapshot storage + OneDrive connector rewrite shared by US2/US3/US4. MUST be complete before any user story implementation.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T002 [P] RED tests in `tests/unit/test_onedrive.py` (REWRITE — delete superseded delta-sync tests in the same edit, never weaken): U1 listing (nested-folder recursion, `@odata.nextLink` pagination, case-insensitive name-substring filter, honest empty `[]`), U2 resolve (path via `/me/drive/root:{path}`, id via `/me/drive/items/{id}`, one Graph call per file, 404 → per-file `not_found`), U5 snapshot round-trip with invariant `snapshot.item_id == origin.locator` (matrix U1/U2/U5; Graph mocked at the httpx boundary per research.md D10)
- [X] T003 [P] RED tests in `tests/unit/test_state_snapshot.py` (NEW file): the four StateStore additions — `set_origin_snapshot`, `get_origin_snapshot`, `origins_for_document`, `onedrive_origins_without_snapshot` — including the binding validation from data-model.md: `snapshot` is written only for successfully embedded OneDrive files and `item_id` MUST equal the row's `locator`; `onedrive_origins_without_snapshot` returns only snapshot-less origins of onedrive sources
- [X] T004 Implement snapshot storage in `src/agentic_rag_mcp/store/state.py`: add nullable `origins.snapshot` column (JSON `FreshnessSnapshot`: `{item_id, last_modified, etag?, embedded_at}` — data-model.md, quote verbatim) to `SCHEMA` with a non-destructive `ALTER TABLE ... ADD COLUMN` for existing DBs, plus the four methods from T003 (depends on T002/T003 failing first)
- [X] T005 Rewrite `src/agentic_rag_mcp/sources/onedrive.py`: DELETE `delta()`, `_get_url()`, `sync()` (superseded, Constitution V); ADD `list_files(search, folder, limit)` — recursive `children` traversal from `folder_path` scope root with `$select` metadata fields, `@odata.nextLink` pagination via `GraphBase._get()`, `embeddable` flag (extension ∈ `{pdf, docx, xlsx, pptx}` AND size ≤ `max_file_size_mb`, default 50), result bound default 100 with `truncated` signal; ADD `resolve(path_or_id)` — single Graph call returning `{id, name, size, last_modified, download_url}`; ADD `get_metadata(item_id)` — freshness probe call `$select=id,lastModifiedDateTime,eTag,name`; KEEP `download()` and the `GraphBase` error mapping (401/403 → `SourceAuthError`, 429 → `ProviderError`) (research.md D1/D2, depends on T002)

**Checkpoint**: Foundation ready — snapshot storage + connector primitives exist; superseded delta machinery is gone from the connector.

---

## Phase 3: User Story 1 — Connect OneDrive with zero automatic ingestion (Priority: P1) 🎯 MVP

**Goal**: `sources_add` + `sources_auth` connect a OneDrive source and ingest nothing, ever; watcher and `sources_sync` never touch the drive (FR-001..FR-004).

**Independent Test**: Connect a source with files in the drive → source healthy → knowledge base gains 0 documents across multiple watcher cycles; `sources_sync` returns the honest on-demand notice; watcher issues zero Graph requests (SC-001, contract matrix C4–C6, I1, I5).

### Tests for User Story 1

- [X] T006 [P] [US1] RED contract tests in `tests/contract/test_onedrive_contract.py` (REVISE — supersede 006's sync-era expectations in the same edit): C4 `sources_add` onedrive frozen shape with on-demand notice values (no "initial sync on watcher cycle" text), C5 `sources_auth` shape with no document-count change after sign-in completion, C6 `sources_sync` onedrive → `{source_id: {status: "on_demand", message: "OneDrive sources are on-demand; use onedrive_embed_files to embed chosen files."}}`
- [X] T007 [P] [US1] RED integration tests in `tests/integration/test_onedrive_on_demand.py` (NEW file): I1 connect + sign-in → 0 embedded documents after simulated watcher cycles, SC-001; I5 registered onedrive source + full watcher cycle → zero Graph requests (mock counts calls)

### Implementation for User Story 1

- [X] T008 [US1] Revise `sources_add` onedrive branch in `src/agentic_rag_mcp/server.py`: valid-token path returns the on-demand notice `"registered; on-demand source — use onedrive_list_files and onedrive_embed_files"` (shape `{source_id, status, sync|message}` unchanged); `needs_auth` path unchanged
- [X] T009 [US1] Revise `sources_auth` in `src/agentic_rag_mcp/server.py`: DELETE the post-sign-in `pipeline.sync_onedrive()` trigger inside `_complete_sign_in` — sign-in completes, source marked healthy, zero ingestion (FR-002, research.md D8)
- [X] T010 [P] [US1] Delete the onedrive branch from `Watcher.sync_once()` in `src/agentic_rag_mcp/ingestion/watchers.py` — watcher handles `local_folder` and `sqlite` only; zero Graph requests for onedrive sources (FR-003, research.md D6)
- [X] T011 [US1] Delete `sync_onedrive()` from `src/agentic_rag_mcp/ingestion/pipeline.py` (superseded, Constitution V) and special-case onedrive in the `sources_sync` tool in `src/agentic_rag_mcp/server.py` to return the T006 honest notice without any sync attempt (FR-004)

**Checkpoint**: A OneDrive source can be added, authenticated, listed by `sources_list` as healthy — and ingests nothing, with the watcher and `sources_sync` provably silent (US1 independently testable).

---

## Phase 4: User Story 2 — Browse files and embed only what the user picks, one-time (Priority: P1)

**Goal**: `onedrive_list_files` (metadata-only) and `onedrive_embed_files` (explicit, sequential, per-file honest outcomes, no count cap) (FR-005..FR-008).

**Independent Test**: List matches by name filter → embed 3 named files of 50 in the drive → exactly those 3 are searchable; every skip has an explicit per-file reason (SC-002, matrix C1/C2, U2–U4, X1, I2).

### Tests for User Story 2

- [X] T012 [P] [US2] RED contract tests in `tests/contract/test_onedrive_contract.py`: C1 `onedrive_list_files` response shape `{source_id, folder, files[], truncated}` with `FileListingEntry` fields per data-model.md; C2 `onedrive_embed_files` response shape `{source_id, results[], embedded, updated, skipped, not_found, failed}` with counters agreeing with `results[]`
- [X] T013 [P] [US2] RED unit tests in `tests/unit/test_onedrive.py`: U3 60-file list processed sequentially in request order with one outcome per file (no cap), U4 re-embed identical content → no duplicate, changed content → old chunks evicted (orphan vector deletion) and snapshot refreshed, X1 error-taxonomy rows — 404 → `not_found` + reason `no file at this path/id`, unsupported `.png` → `skipped` + `unsupported format: .png`, oversize → `skipped` + size reason, Graph 429 on file 2 of 5 → file 2 `failed: "cloud rate-limited — re-run embed for this file"`, files 3–5 still processed
- [X] T014 [P] [US2] RED integration test in `tests/integration/test_onedrive_on_demand.py`: I2 embed 3 of 50 drive files → exactly 3 searchable with citations; the other 47 never return from this source (SC-002)

### Implementation for User Story 2

- [X] T015 [US2] Implement `embed_onedrive_files(source_id, source, files)` in `src/agentic_rag_mcp/ingestion/pipeline.py`: sequential per-file loop — `source.resolve()` → size/format guards → `source.download()` → existing parse/dedup/upsert path (content-hash dedup, orphan eviction) → write `FreshnessSnapshot` via `set_origin_snapshot` on success → append `EmbedOutcome` (`embedded|updated|skipped|not_found|failed`, mandatory `reason` for non-success) — mid-batch failures continue the batch (FR-006/007/009, research.md D2/D9)
- [X] T016 [US2] Wire `onedrive_list_files(source_id, search, folder, limit)` MCP tool in `src/agentic_rag_mcp/server.py`: unknown source → `NotFoundError("source not found")`; non-onedrive → `NotFoundError("source is not a onedrive source")`; expired token → `SourceAuthError` surfaced as "Microsoft sign-in required" + source → `degraded`; empty listing returns honest `files: []`
- [X] T017 [US2] Wire `onedrive_embed_files(source_id, files)` MCP tool in `src/agentic_rag_mcp/server.py`: same source/auth guards, then call `pipeline.embed_onedrive_files`; return the T012 shape (depends on T015, T016)

**Checkpoint**: US1 + US2 together form the MVP — a user can connect, browse, and embed chosen files one-time; exactly the named files become searchable.

---

## Phase 5: User Story 3 — Staleness reminder when cited files changed in the cloud (Priority: P1)

**Goal**: `ask()` probes cited OneDrive files' cloud metadata within a 5-second budget and appends an honest reminder (answer text + additive `freshness_warnings` field); never auto-downloads (FR-009..FR-013).

**Independent Test**: Embed a file → modify it in the cloud → `ask()` returns the answer from the embedded copy plus a reminder naming the file and both timestamps on the same turn; no re-download occurs (SC-003, matrix C3, U6/U7, I3).

### Tests for User Story 3

- [X] T018 [P] [US3] RED unit tests in `tests/unit/test_onedrive_freshness.py` (NEW file): U6 probe outcomes — cloud `lastModifiedDateTime` > snapshot → stale reminder with `embedded_at`/`modified_at`; unchanged → no reminder; item-id 404 → `kind: "deleted"` "last available version" note; timeout/budget exhaustion → no reminder, answer unaffected; probe auth failure → source → `degraded`, no reminder fabricated; U7 rename — id probe still resolves after path change (research.md D4/D5, D9 matrix)
- [X] T019 [P] [US3] RED contract test in `tests/contract/test_onedrive_contract.py`: C3 `ask` response keeps the complete existing frozen field set and gains additive `freshness_warnings: []` (empty list when no reminders) — Constitution I / FR-014
- [X] T020 [P] [US3] RED integration test in `tests/integration/test_onedrive_on_demand.py`: I3 cloud edit → reminder on the answer the same conversation turn, both timestamps present, `freshness_warnings[0].kind == "stale"`, document content NOT re-downloaded (mock counts downloads) (SC-003)

### Implementation for User Story 3

- [X] T021 [US3] Create `src/agentic_rag_mcp/sources/onedrive_freshness.py` (NEW): `probe_cited(cited_docs, state, sources) -> list[StalenessReminder]` — `ThreadPoolExecutor(max_workers=4)`, 4-second per-request timeout, 5-second total budget (user decision 2026-10-11), identity by `origins.snapshot.item_id` via `source.get_metadata()`, reminder templates per research.md D5 (stale + deleted variants), honest outcomes per D9 (transient → silent skip; auth → mark source degraded and suppress)
- [X] T022 [US3] Wire the probe into `ask()` in `src/agentic_rag_mcp/server.py`: after synthesis, map citation `document_id`s via `state.origins_for_document()`, probe only origins of onedrive sources, append reminder suffix to the answer text and set the additive `freshness_warnings` field; local-file citations are never probed; the reminder NEVER triggers a download (FR-010/011) (depends on T021)

**Checkpoint**: Answers citing OneDrive files are freshness-aware — stale/deleted states surface honestly with timestamps, and the no-auto-download invariant holds.

---

## Phase 6: User Story 4 — One-command explicit refresh (Priority: P2)

**Goal**: Re-embedding a named file replaces old chunks and refreshes the snapshot; identical content reports an honest no-change outcome (FR-008 refresh loop).

**Independent Test**: Stale file → explicit re-embed → same question answers from new content only and the reminder is gone; re-embed of unchanged content reports no change without duplicating (SC-004, matrix I4 + U4 refresh rows).

### Tests for User Story 4

- [X] T023 [P] [US4] RED unit tests in `tests/unit/test_onedrive.py`: re-embed changed content → outcome `updated`, snapshot refreshed to the new cloud `last_modified`, orphan vectors deleted; re-embed identical content → honest no-change outcome, no duplicate document, no snapshot timestamp drift
- [X] T024 [P] [US4] RED integration test in `tests/integration/test_onedrive_on_demand.py`: I4 full loop — embed → cloud edit → ask (reminder) → explicit re-embed → ask again → only new content, `freshness_warnings` empty (SC-004)

### Implementation for User Story 4

- [X] T025 [US4] Verify refresh semantics in `src/agentic_rag_mcp/ingestion/pipeline.py` + `src/agentic_rag_mcp/server.py`: `embed_onedrive_files` reports `updated` with refreshed snapshot on changed content and an honest "already current" result for identical content; the update command accepts both path and item id (the reminder carries `locator` for exactly this) (depends on T015)

**Checkpoint**: The reminder loop closes — prompt → explicit command → refreshed content, one command, no automation.

---

## Phase 7: User Story 5 — Local sources keep automatic updates, untouched (Priority: P2)

**Goal**: Zero regression: `local_folder`/`sqlite` auto-sync and health transitions unchanged; watcher never touches onedrive (FR-003, spec US5).

**Independent Test**: With a local folder source AND a registered onedrive source, a new local file embeds within one watcher cycle while the OneDrive source produces zero Graph traffic and no health changes (SC-005, matrix I5/I6).

### Tests for User Story 5

- [X] T026 [P] [US5] RED integration regression tests in `tests/integration/test_onedrive_on_demand.py`: I6 local_folder + sqlite auto-sync cycle behavior unchanged (new local file embedded, changed re-embedded, deleted evicted) with a onedrive source registered; I5 watcher cycle → zero Graph requests; onedrive source health never transitions from watcher cycles (SC-005)
- [X] T027 [US5] Pin the structural guarantee in `tests/integration/test_onedrive_on_demand.py` (or a dedicated grep-gate unit test): assert `src/agentic_rag_mcp/ingestion/watchers.py` contains no onedrive/delta/Graph references and that only user-initiated tools/probes transition onedrive health (Constitution V — nothing dead left to re-enable)

**Checkpoint**: The two coexisting policies are pinned by tests — automatic for local, on-demand for OneDrive.

---

## Phase 8: Cross-Cutting — One-Time Migration (FR-016)

**Purpose**: Upgrade path for legacy (pre-007) embedded OneDrive documents: re-embed once, establish snapshots, then pure on-demand (user decision 2026-10-11 Option C; research.md D7; SC-008).

- [X] T028 [P] RED unit tests in `tests/unit/test_migration.py` (NEW file): U8 — migration re-embeds ONLY snapshot-less onedrive origins (already-snapshotted files untouched, non-onedrive origins untouched); second startup run = no-op (idempotent); file deleted in cloud at migration → existing copy kept + honest per-file reason + origin still pending; expired token → honest sign-in-required log, retried next startup; zero legacy docs → no-op (SC-008)
- [X] T029 Implement `migrate_onedrive_sources()` in `src/agentic_rag_mcp/ingestion/pipeline.py`: pending set = `state.onedrive_origins_without_snapshot(source_id)` for each onedrive source; re-embed each via the `embed_onedrive_files` machinery; per-file honest outcomes logged; success writes the snapshot which removes the origin from the pending set — idempotent by construction, no migration flag stored (depends on T015)
- [X] T030 Call `migrate_onedrive_sources()` at startup in `build_server()` in `src/agentic_rag_mcp/server.py` BEFORE `watcher.start()`, wrapped so a migration failure never blocks server start (honest log, retried next startup) (depends on T029)

**Checkpoint**: Upgrade is safe — legacy files gain snapshots once and never again; this deployment (no onedrive sources registered) is a logged no-op.

---

## Phase 9: Polish & Cross-Cutting Concerns

- [X] T031 [P] Update `"dify/Chatflow Basic (AgenticRAG Agent).yml"`: register `onedrive_list_files` and `onedrive_embed_files` in the agent tool list; extend the system prompt with the on-demand flow (list → confirm → embed chosen files), staleness-reminder relay guidance (relay verbatim, offer the one-command update), and the invariant "never embed the whole drive"
- [X] T032 [P] Update `README.md` tool table (add both tools, `sources_sync` onedrive notice, `ask` freshness_warnings) and sweep `DEPLOY.md`/`docs/` for superseded OneDrive auto-sync mentions; remove them (Constitution V)
- [X] T033 Constitution V sweep: `grep -rn "delta_link\|sync_onedrive\|_get_url\|delta(" src/ tests/` — delete any leftover superseded code or tests; confirm no dead sync paths remain
- [X] T034 Full-suite gate: `pytest -q` → 100% green (Constitution II); then run quickstart.md §1 automated validation command and confirm the expected green set covering the full error-path matrix
- [ ] T035 [P] Live validation (manual, needs Azure app + Dify stack): execute quickstart.md §2–§3 (connect → 0 ingest, browse, embed, reminder, explicit update, deleted-cloud note, error paths, migration no-op) and record outcomes

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (T001)**: none — start immediately
- **Phase 2 (T002–T005)**: depends on Phase 1; BLOCKS all user stories
- **US1 (Phase 3)**: depends on Phase 2 (T004 not strictly, but T005 shares the connector file — complete Phase 2 first)
- **US2 (Phase 4)**: depends on US1's server wiring (T008–T011) and Phase 2
- **US3 (Phase 5)**: depends on Phase 2 (T004 snapshots, T005 `get_metadata`) and US2 (embedded files to cite)
- **US4 (Phase 6)**: depends on US2 (embed tool) and US3 (reminder to clear)
- **US5 (Phase 7)**: depends on US1 (watcher deletion) — can run in parallel with US3/US4
- **Migration (Phase 8)**: depends on US2 implementation (embed machinery) — can run in parallel with US5/US4
- **Polish (Phase 9)**: last — depends on all story phases

### User Story Independent Tests

- **US1**: connect → healthy, 0 documents after watcher cycles, `sources_sync` notice, zero Graph requests from watcher
- **US2**: embed 3 named of 50 → exactly 3 searchable; per-file reasons for every skip
- **US3**: cloud edit → same-turn reminder with both timestamps; no download triggered
- **US4**: explicit update → new content only; reminder gone; identical-content honest no-change
- **US5**: local auto-sync regression green; watcher isolation pinned

### Parallel Opportunities

- Phase 2: T002 ∥ T003 (different test files); T004 then T005 sequential (implementation order)
- US1: T006 ∥ T007 (different test files); T010 ∥ T008/T009 (different source files, no cross-deps)
- US2: T012 ∥ T013 ∥ T014 (three different test files); implementation T015 → T016 → T017 sequential (server/pipeline dependency)
- US3: T018 ∥ T019 ∥ T020 (three test files); T021 → T022 sequential
- US4: T023 ∥ T024; US5: T026 ∥ T027 ∥ (US4 tests) ∥ T028 — all different test files
- Polish: T031 ∥ T032 ∥ T035 (different docs); T033 → T034 sequential

---

## Parallel Example: User Story 2

```text
# Launch all US2 RED tests together:
Task: "RED contract tests C1/C2 in tests/contract/test_onedrive_contract.py"        (T012)
Task: "RED unit tests U3/U4/X1 in tests/unit/test_onedrive.py"                      (T013)
Task: "RED integration test I2 in tests/integration/test_onedrive_on_demand.py"     (T014)

# Then implementation in order:
Task: "embed_onedrive_files in src/agentic_rag_mcp/ingestion/pipeline.py"            (T015)
Task: "onedrive_list_files tool in src/agentic_rag_mcp/server.py"                    (T016)
Task: "onedrive_embed_files tool in src/agentic_rag_mcp/server.py"                   (T017)
```

---

## Implementation Strategy

### MVP First (US1 + US2)

1. Complete Phase 1 (baseline) and Phase 2 (foundation)
2. Complete Phase 3 (US1: connect with zero ingestion — the structural guarantee)
3. Complete Phase 4 (US2: browse + embed chosen files — first user value)
4. **STOP and VALIDATE**: run the US1+US2 tests and quickstart.md §2 steps 1–3
5. Deploy/demo if ready — the core on-demand feature is complete

US1 alone is the spec's foundational guarantee, but delivers no user value without US2's embed — together they are the minimal valuable increment.

### Incremental Delivery

1. Foundation (snapshot + connector) → US1+US2 (MVP) → US3 (freshness-aware answers) → US4 (refresh loop) → US5 (regression pin) → Migration (upgrade safety) → Polish (docs/Dify/gates)
2. Each story adds value without breaking previous ones; the full pytest gate runs at every checkpoint (T034 is the final formal gate)

### Parallel Team Strategy

- Developer A: US1 → US5 (watcher/isolation concerns)
- Developer B: US2 → US4 (embed pipeline)
- Developer C: US3 → Migration (probe + snapshot lifecycles)
- Shared: Phase 2 foundation first; Phase 9 polish together

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- Every implementation task has its RED test(s) written and failing first (Constitution II)
- Superseded spec-006 tests are deleted in the same change set as their replacement tests — never weakened (SC-006, Constitution V)
- Error-path coverage is a first-class deliverable: matrix rows X1/U6/U8 are binding (research.md D9)
- Commit after each task or logical group; stop at any story checkpoint to validate independently

---

## Phase 10: Convergence

**Purpose**: Polish-level gaps found by /speckit.converge (2026-10-11) — the implementation satisfies all FRs/SCs/constitution principles; these four items close doc-string staleness, a validation-command omission, a data-model field-rule nuance, and one unpinned edge case.

- [X] T036 Update the two stale description strings ("all 8 AgenticRAG MCP tools") at lines 2 and 296 of `dify/Chatflow Basic (AgenticRAG Agent).yml` to reflect the 16 wired tools per plan.md T031 completeness (partial)
- [X] T037 Add `tests/unit/test_state_snapshot.py` to the §1 automated validation command in `specs/007-onedrive-on-demand/quickstart.md` so it runs the full feature suite per tasks T003/T034 (partial)
- [X] T038 Omit the `modified_at` key from the deleted-cloud StalenessReminder variant in `src/agentic_rag_mcp/sources/onedrive_freshness.py` (currently emitted as `None`) per data-model.md StalenessReminder field rule, and pin it in `tests/unit/test_onedrive_freshness.py` (partial)
- [X] T039 Add one unit or integration test pinning multi-source independence — two registered onedrive sources embed disjoint files with separate per-source token caches and configs — per spec edge case "multiple OneDrive sources are independent" (missing)
