# Tasks: Application Log File with Leveled Logging

**Input**: Design documents from `specs/008-app-logging/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/logging.md, quickstart.md

**Tests**: REQUIRED — Constitution II (Tests-First) mandates a runnable RED check before every implementation task. Test matrix C1–C2, U1–U7, I1–I4, X1 in [contracts/logging.md](contracts/logging.md) is the source of truth; every RED task below names its matrix rows.

**Organization**: Tasks grouped by user story (spec.md US1–US3) plus foundational and polish phases. Every story is independently testable at its checkpoint.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (US1–US3)
- Exact file paths in every description

## Path Conventions

Single project: `src/agentic_rag_mcp/` and `tests/` at repository root (per plan.md). The container entry lives at `dify/docker/mcp-server/server.py`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish a known-green baseline before the logging change set.

- [X] T001 Run the full pytest suite (`pytest -q`) and confirm 100% green; record the count (Constitution II gate for the RED workflow)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The logging setup module + config surface shared by all three stories. MUST be complete before any user story implementation.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T002 [P] RED tests in `tests/unit/test_logging_setup.py` (NEW file), matrix U1–U6 + X1 rows (contracts/logging.md): level resolution order (env > toml > default) and `INF0` typo → INFO + a WARNING record naming the value (U1); rotation bounds with `rotation_size_mb=0.001` — write past threshold, `.1` generation exists, total bytes ≤ size×count (U2); RedactionFilter patterns — a Bearer token, `client_secret`, `api_key`, and a pre-auth `api.onedrive.com`/`tempauth` URL each become `[REDACTED:*]` at DEBUG and INFO alike (U3); unwritable log path → no exception, `LoggingSetup.writable=False`, console handler still emits (U4); console-mirror parity — same records on stderr and file (U5); disabled-level laziness — `logger.isEnabledFor(DEBUG)` is False at INFO and %-style call sites never format (U6); invalid-level WARN lands in the file after handlers attach (bootstrap ordering)
- [X] T003 Implement `src/agentic_rag_mcp/logging_setup.py` (NEW): `configure_logging(cfg) -> LoggingSetup` — root logger gets `RotatingFileHandler(maxBytes=rotation_size_mb*1024*1024, backupCount=rotation_count, encoding="utf-8", delay=True)` + a **stderr** StreamHandler (stdout carries the stdio MCP protocol — never use it); `RedactionFilter` with the four binding patterns from data-model.md applied to `record.getMessage()`; level resolution `LOG_LEVEL` env → `[logging] level` → `"INFO"`, case-insensitive, invalid → INFO + pending WARNING emitted after handlers attach (research.md D6/D8); parent-dir mkdir + append-mode probe-open — `OSError` → `writable=False`, no file handler, ERROR record on console (FR-008); module-level `LoggingSetup(level_name, level, path, writable, fallback_reason)` for status (depends on T002 failing first)
- [X] T004 Extend `src/agentic_rag_mcp/config.py`: `Config` gains `log_level: str = "INFO"`, `log_file: Path | None = None` (resolved default = `<state_db.parent>/logs/server.log` — research.md D4), `rotation_size_mb: float = 10.0`, `rotation_count: int = 5`; `load_config()` parses `[logging]` via `_get` and honors the `LOG_LEVEL` env override; `DEFAULT_CONFIG` gains a commented `[logging]` section documenting every key
- [X] T005 Wire logging into `src/agentic_rag_mcp/server.py`: `build_server` calls `configure_logging(cfg)` first (before migration/watcher start); `main()` drops `logging.basicConfig(level=logging.INFO)`; convert the endpoint-banner `print()` to `log.info` (the `--init` print stays — it exits before logging exists, spec bootstrap edge case); every existing tool response shape unchanged (FR-010)

**Checkpoint**: Foundation ready — records flow to file+console from all named loggers with redaction, rotation, and honest fallbacks.

---

## Phase 3: User Story 1 — Every event recorded with level semantics (Priority: P1) 🎯 MVP

**Goal**: The persistent log file records the whole application with correct INFO/WARN/ERROR semantics, zero silent failures, bounded disk, console mirror, and no output bypassing the file (FR-001/002/006/007/008/011).

**Independent Test**: startup + watcher cycle + ask + embed session → INFO records for each event in the file; an induced failure produces a WARN/ERROR record with the same reason; INFO records carry counts, not names (SC-001/SC-002, matrix I1/I2/I4/U7).

### Tests for User Story 1

- [X] T006 [P] [US1] RED integration tests in `tests/integration/test_logging_integration.py` (NEW file), matrix I1/I2/I4: SC-001 session — build server (tmp state dir → tmp log file per D4), startup + one watcher cycle (`sources_sync`) + one `ask` + one embed → assert INFO records for each event with counts/outcomes and **no question text or file names at INFO** (I1); induced failures — embed a missing path + unknown source → WARN/ERROR records with matching reasons, zero silent failures (I2); SC-004 rotation — tiny size, sustained writes, total usage ≤ size×count (I4)

### Implementation for User Story 1

- [X] T007 [US1] Re-level call sites in `src/agentic_rag_mcp/ingestion/pipeline.py` per research.md D5: `log.info("ingested %s …")` (line ~68 — local locators are file paths) and `log.info("embedded %s (%s) from onedrive", …)` (line ~159 — carries the title) become `log.debug(...)`; add one count-based INFO summary per sync/embed call (e.g. `"onedrive embed: 3 embedded, 1 skipped"`); opaque Graph item ids (migration lines) stay at INFO/WARNING — they are correlation ids, not names
- [X] T008 [US1] Framework log routing in `dify/docker/mcp-server/server.py`: pass `log_config=None` to `uvicorn.run(...)` so `uvicorn`/`uvicorn.access`/`uvicorn.error` keep `propagate=True` and flow to the root handlers → request lines land in the file (research.md D2; pin with a U7-style unit assertion that a simulated `uvicorn.access` logger record reaches the file)

**Checkpoint**: The log file is the complete, correctly-leveled record of the running application — this is the MVP.

---

## Phase 4: User Story 2 — Operator-configurable level + status exposure (Priority: P2)

**Goal**: The level is set via config/env without code changes; invalid values fall back with an honest WARN; `status` reports the logging state (FR-003/FR-012).

**Independent Test**: `status` response contains the additive `logging` block with the active level; `[logging] level` and `LOG_LEVEL` both take effect across restarts; a typo'd level yields the WARN + INFO (matrix C1/C2/U1).

### Tests for User Story 2

- [X] T009 [P] [US2] RED contract tests in `tests/contract/test_logging_contract.py` (NEW file), matrix C1/C2: `status` keeps every existing field AND gains exactly `logging{level, log_file, writable}` (C1/FR-012); `[logging] level` in a toml file resolves and `LOG_LEVEL` env overrides it (C2)

### Implementation for User Story 2

- [X] T010 [US2] Add the `logging` field to the `status` tool in `src/agentic_rag_mcp/server.py`: serialize the module-level `LoggingSetup` from `logging_setup` as `{"level": level_name, "log_file": str(path), "writable": writable}` — purely additive, all existing status fields byte-identical (Constitution I; depends on T003)

**Checkpoint**: An operator (or the Dify agent) can see and set the logging state without shell access.

---

## Phase 5: User Story 3 — DEBUG traces execution flow; user input stays DEBUG-only (Priority: P2)

**Goal**: With DEBUG on, one operation reads end-to-end from the file; question text and file names appear nowhere above DEBUG (FR-004/005/009).

**Independent Test**: DEBUG-level ask trace shows entry → routing decision → hit counts → probe outcome → completion in order (SC-003); scanning all INFO+ records for question text/names yields zero (SC-005, matrix I3).

### Tests for User Story 3

- [X] T011 [P] [US3] RED integration test additions in `tests/integration/test_logging_integration.py`, matrix I3 + SC-005 scans: DEBUG-enabled `ask` produces an ordered trace — tool entry with the question, routing decision/provenance, hit counts, freshness probe outcome, completion — readable from the file alone (SC-003); a scan test over a full session's INFO+ records finds zero question text and zero file names/titles (SC-005)

### Implementation for User Story 3

- [X] T012 [US3] DEBUG trace points per research.md D9: tool-entry `log.debug` on `ask`, `search`, `sources_add`, `sources_auth`, `sources_sync`, `sources_list`, `sources_remove`, `onedrive_list_files`, `onedrive_embed_files` in `src/agentic_rag_mcp/server.py`; routing decision + provenance and pre-synthesis hit counts in the `ask` flow (`src/agentic_rag_mcp/server.py`); per-source watcher cycle results in `src/agentic_rag_mcp/ingestion/watchers.py`; per-file probe outcomes (stale/deleted/unchanged/skipped + budget expiry) in `src/agentic_rag_mcp/sources/onedrive_freshness.py` — all %-style lazy calls (FR-009)

**Checkpoint**: A developer can find the source of any problem from one operation's slice of the log.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T013 [P] Documentation: add the `[logging]` section to the config examples in `README.md` and `DEPLOY.md` (mounted-volume note: `~/.config/agentic-rag-mcp/logs/server.log` persists across container recreation; `docker run … -e LOG_LEVEL=…` passthrough), and a "Reading the logs" subsection to `README.md`
- [X] T014 Constitution V sweep: `grep -rn "basicConfig\|print(" src/agentic_rag_mcp/ dify/docker/mcp-server/` — no logging bypasses remain (the `--init` print is the documented exception); confirm no dead config paths
- [X] T015 Full-suite gate: `pytest -q` → 100% green (existing suites untouched — the D4 path rule is what guarantees their isolation), then run quickstart.md §1 command and confirm the C/U/I/X matrix green
- [X] T016 [P] Live validation (manual, needs the Docker sidecar): execute quickstart.md §2 — default INFO records in `docker exec agentic-rag tail …/logs/server.log`, chat-asked "what is the log level?" answered from `status`, a DEBUG session trace, an unwritable-path fallback demo, and a rotation sanity check

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (T001)**: none — start immediately
- **Phase 2 (T002–T005)**: depends on Phase 1; BLOCKS all user stories (T002 RED first, then T003/T004 [P] in parallel, T005 last — it wires both)
- **US1 (Phase 3)**: depends on Phase 2; MVP
- **US2 (Phase 4)**: depends on Phase 2 (T010 reads LoggingSetup from T003); can run after or alongside US1
- **US3 (Phase 5)**: depends on Phase 2 + T007's re-leveling (the DEBUG-only discipline builds on it)
- **Polish (Phase 6)**: last

### User Story Independent Tests

- **US1**: default session → complete leveled file; failures → WARN/ERROR with reasons; rotation caps disk
- **US2**: `status.logging` present; toml/env level both resolve; typo → WARN + INFO
- **US3**: DEBUG trace readable end-to-end; INFO+ scan clean of user input

### Within Each User Story

- RED tests first, implementation after
- T005 touches `server.py`; T010/T012 also touch `server.py` — those are sequential (file-based coordination), while their RED test files parallelize

### Parallel Opportunities

- Phase 2: T002 ∥ nothing (RED first); then T003 ∥ T004 (different files)
- US1: T006 ∥ T007/T008's files (tests run first anyway)
- US2/US3 RED tests: T009 ∥ T011 (different files); T010 → T012 sequential (same file)
- Polish: T013 ∥ T016 (docs vs manual validation); T014 → T015 sequential

---

## Parallel Example: User Story 1

```text
# RED first:
Task: "I1/I2/I4 integration tests in tests/integration/test_logging_integration.py"   (T006)

# Then implementation in parallel (different files):
Task: "re-level pipeline call sites in src/agentic_rag_mcp/ingestion/pipeline.py"      (T007)
Task: "uvicorn log_config=None in dify/docker/mcp-server/server.py"                    (T008)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 (baseline) and Phase 2 (foundation)
2. Complete Phase 3 (US1) → **STOP and VALIDATE**: run quickstart §1 + the live INFO check
3. The log file now carries the complete leveled picture — deployable

### Incremental Delivery

1. Foundation (setup + config) → US1 (leveled file, MVP) → US2 (knob + status) → US3 (DEBUG tracing) → Polish (docs, sweep, gates, live)
2. Full pytest gate at every checkpoint (T015 is the formal final gate)

### Parallel Team Strategy

- Developer A: US1 (pipeline re-leveling + framework routing)
- Developer B: US2 (status field + contract tests)
- Developer C: US3 (trace points + scan tests)
- Shared: Phase 2 foundation first; server.py tasks (T005/T010/T012) coordinate sequentially

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks
- Every implementation task has its RED test(s) first (Constitution II)
- Console is **stderr** everywhere — stdout belongs to the stdio MCP protocol
- Existing suites must stay green with zero edits: the default log path derives from `state_db`'s directory, so tmp-state tests write tmp logs (research.md D4)
- The container is the product deployment: T008's `log_config=None` is what puts framework request lines in the file; the local `mcp.run()` path keeps them console-only (documented ceiling)
- Commit after each task or logical group; stop at any checkpoint to validate a story independently

---

## Phase 7: Convergence

**Purpose**: Gaps found by /speckit.converge (2026-10-12) — health transitions and the sqlite sync record; the implementation otherwise satisfies all FRs/SCs/constitution principles (225-suite green).

- [X] T017 Log every source health transition inside `StateStore.set_health` in `src/agentic_rag_mcp/store/state.py` — degraded → `log.warning("source %s degraded: %s", …)`, healthy → `log.info("source %s healthy", …)` — one choke-point fix covering all 13 call sites (freshness probe auth failures, onedrive tool auth guards, sources_auth sign-in completion, migration), and pin it with a test asserting degrade/recover records per US1/AC4 (partial)
- [X] T018 Add the count-based INFO summary to `sync_sqlite` in `src/agentic_rag_mcp/ingestion/pipeline.py`, mirroring the local-sync record (`"sqlite sync %s: N rows, …"`) per US1/AC2 and SC-001 (partial)
