# Implementation Plan: Application Log File with Leveled Logging

**Branch**: `008-app-logging` | **Date**: 2026-10-12 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/008-app-logging/spec.md`

## Summary

Add a persistent, leveled log file to the existing stdlib `logging` usage: one new `logging_setup` module configures a rotating file handler + console (stderr) handler on the root logger from `[logging]` config (level default INFO, env-overridable), a redaction filter enforces the privacy rules (credentials never; question text / file names DEBUG-only), the two startup prints convert to log records, the three INFO lines that carry file names re-level to DEBUG with count-based INFO summaries, the container's uvicorn invocation stops self-configuring (`log_config=None`) so framework request logs flow into the same file, and `status` gains an additive `logging` field. Zero new dependencies. Test cases and error handling are first-class deliverables (see [contracts/logging.md](contracts/logging.md)).

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: No new deps — stdlib `logging` (+ `RotatingFileHandler`, `Filter`)

**Existing foundation (verified in code)**:

- Named loggers already in place: `agentic_rag_mcp` (server), `.pipeline`, `.freshness`, `.watchers`, `.errors` — all %-style lazy calls (FR-009 largely satisfied already)
- `server.main()`: `logging.basicConfig(level=logging.INFO)` — console-only, no file; two `print()` calls (config-init path + endpoint banner) bypass logging
- Container entry `dify/docker/mcp-server/server.py`: `build_server(...)` at import, then `uvicorn.run(app, ...)` — uvicorn's default `log_config` attaches handlers to `uvicorn`/`uvicorn.access`/`uvicorn.error` with `propagate=False`, which would bypass a root-level file handler
- `config.py`: `Config` dataclass + `load_config()` with `_get(raw, section, key)` parsing; `state_db` default `~/.config/agentic-rag-mcp/state.sqlite3`
- Call sites that violate the DEBUG-only rule today: `pipeline.py:68` (`ingested %s` — local locators are file paths), `pipeline.py:159` (`embedded %s ... from onedrive` — file title); opaque Graph item ids (migration lines) are correlation ids, not names — stay at INFO/WARNING

**Storage**: log file on the mounted config volume — default `<state_db dir>/logs/server.log` (live: `~/.config/agentic-rag-mcp/logs/server.log`; tests derive a tmp path automatically from their tmp `state_db`, zero churn). Rotation: 10 MB × 5 generations.

**Testing**: pytest — unit (handler/filter behavior, no I/O beyond tmp), contract (`status` additive field), integration (real records in files under tmp state dirs). Full error-path matrix in [contracts/logging.md](contracts/logging.md).

**Constraints**: `status` response fields frozen except additive `logging` (Constitution I / FR-012); console = **stderr** (stdout carries the MCP stdio protocol — never attach console logging to stdout); user question text and file names at DEBUG only (user decision 2026-10-12).

**Scale/Scope**: single-process server; rotation caps log disk at ~50 MB.

## Constitution Check

| Principle | Status | Evidence |
|---|---|---|
| I. Contract Preservation | PASS | FR-010/FR-012: `status` gains one additive `logging` field; all existing fields and tool response shapes unchanged; contract test pins it |
| II. Tests-First | PASS | RED tests enumerated per FR in the contract test matrix (C1–C2, U1–U6, I1–I4, X1) before implementation |
| III. Minimal Dependencies | PASS | stdlib `logging` only — no new packages |
| IV. Honest Answers | PASS | FR-002/FR-003: every operation failure gets a WARN/ERROR record; invalid config values fall back with an honest WARN instead of crashing |
| V. Spec-Driven Replacement | PASS | Additive feature; `basicConfig` call is replaced by the configured setup (no dead code); no superseded spec |

## Project Structure

### Documentation (this feature)

```text
specs/008-app-logging/
├── plan.md                    # This file
├── research.md                # Phase 0 output — decisions D1–D11 incl. error handling + test strategy
├── data-model.md              # Phase 1 output — LoggingConfig, LogRecord, RedactionRule, LoggingSetup
├── contracts/logging.md       # Phase 1 output — status field, error matrix, per-tool test cases
├── quickstart.md              # Phase 1 output — runnable validation incl. error-path scenarios
├── checklists/requirements.md
└── tasks.md                   # Phase 2 (/speckit.tasks) — NOT created by this command
```

### Source Code (repository root)

```text
src/agentic_rag_mcp/
├── logging_setup.py           # NEW: configure_logging(cfg) -> LoggingSetup; RedactionFilter;
│                              #   level parse + invalid fallback WARN; writability probe +
│                              #   console-only fallback (FR-003/FR-008); rotation attach (FR-006)
├── config.py                  # EXTENDED: [logging] section (level, log_file, rotation_size_mb,
│                              #   rotation_count) + LOG_LEVEL env override; defaults derived from
│                              #   state_db dir (D4 test-isolation rule)
├── server.py                  # REVISED: build_server calls configure_logging before serving;
│                              #   main() drops basicConfig; prints → log.info; status gains
│                              #   additive logging field; DEBUG trace points on tool entries,
│                              #   routing decisions, search outcomes
├── ingestion/pipeline.py      # REVISED: path/title-bearing lines → DEBUG; count-based INFO
│                              #   summaries per sync/embed call (DEBUG-only rule, D5)
├── ingestion/watchers.py      # EXTENDED: DEBUG cycle trace (sources processed, per-source results)
├── sources/onedrive_freshness.py  # EXTENDED: DEBUG per-file probe outcomes (stale/deleted/unchanged/skipped)
└── dify/docker/mcp-server/server.py  # REVISED: uvicorn.run(..., log_config=None) so framework
                                       #   request logs propagate to root → into the file (D2)

tests/
├── unit/test_logging_setup.py        # NEW: U1 level parse + invalid-value WARN; U2 rotation bounds;
│                                     #   U3 redaction patterns (bearer/secret/download-url); U4 unwritable
│                                     #   path → console-only + LoggingSetup.writable=False; U5 console mirror;
│                                     #   U6 disabled-level laziness; bootstrap record ordering
├── contract/test_logging_contract.py # NEW: C1 status +logging additive field, frozen fields intact;
│                                     #   C2 config surface (toml + LOG_LEVEL env)
└── integration/test_logging_integration.py  # NEW: I1/SC-001 session records (startup, watcher, ask, embed);
                                              #   I2/SC-002 failure → WARN/ERROR with reason; I3/SC-003 DEBUG
                                              #   end-to-end trace; I4/SC-004 rotation cap; SC-005 secret+INFO scans
```

### User-managed files (not committed)

```text
~/.config/agentic-rag-mcp/logs/server.log     # the log file (mounted into the container)
~/.config/agentic-rag-mcp/config.toml         # [logging] section added to DEFAULT_CONFIG
```

## Complexity Tracking

No constitution violations. Complexity hotspots:

1. **Framework logger routing (D2)** — uvicorn's default `log_config` would bypass the root file handler (`propagate=False` + own handlers); solved with `log_config=None` in the container wrapper. The local `mcp.run()` path keeps uvicorn logs console-only (documented ceiling — the container is the product).
2. **Test isolation (D4)** — default log path derives from `state_db`'s directory so every existing test (tmp `state_db`) gets tmp logs with zero churn; live default lands in the mounted config volume.
3. **DEBUG-only discipline (D5)** — mechanically enforced at call sites (re-leveling + count-based INFO) and pinned by an SC-005-style scan test that asserts INFO records contain no question text and no file names.
