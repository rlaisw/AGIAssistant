# Contract: Logging Setup, Status Field & Error Handling

**Feature**: `specs/008-app-logging` | **Frozen by**: Constitution I (FR-010/FR-012)

## Tool: `status` (EXISTING — additive field)

All existing fields unchanged. New additive field on every response:

```json
{
  "...all existing status fields unchanged...": "",
  "logging": {
    "level": "INFO",                  // canonical active level (DEBUG|INFO|WARNING|ERROR)
    "log_file": "/root/.config/agentic-rag-mcp/logs/server.log",
    "writable": true                   // false ⇒ console-only fallback active (FR-008)
  }
}
```

## Configuration surface

```toml
[logging]
level = "INFO"                 # LOG_LEVEL env overrides; invalid → INFO + WARNING record
# log_file = ""                # default: <state_db dir>/logs/server.log
# rotation_size_mb = 10.0
# rotation_count = 5
```

## Error-response matrix (single source of truth)

| Scenario | Behavior | Where observed |
|---|---|---|
| `LOG_LEVEL=DEGUG` (typo) | Level INFO; `WARNING ... invalid log level 'DEGUG' — using INFO` | file + console + `status.logging.level=="INFO"` |
| log_file points at unwritable dir | Server starts; `ERROR log file not writable: …` on console; `status.logging.writable==false` | console + status |
| credential in a message | `[REDACTED:token|secret|download-url]` at every level | file + console |
| question text / file name at INFO+ | never emitted (call-site discipline); scan test pins it | tests only |
| disk fills mid-run | emit falls back to stderr; serving continues | console |
| rotation threshold crossed | `server.log.1 … server.log.5`, oldest dropped; usage ≤ size×count | filesystem |

## Test matrix (contract + unit + integration — every row is a named test)

| # | Level | Test case | Asserts |
|---|-------|-----------|---------|
| C1 | contract | `status` additive logging field | every existing status field present + `logging{level, log_file, writable}` (FR-012) |
| C2 | contract | config surface | `[logging] level` in toml resolves; `LOG_LEVEL` env overrides it (D4/D8) |
| U1 | unit | level resolution + invalid fallback | INFO default; DEBUG/ERROR honored; `INF0` → INFO + a WARNING record naming the value (FR-003) |
| U2 | unit | rotation bounds | tiny size_mb → write past threshold → `.1…` generations exist; total bytes ≤ size×count (FR-006) |
| U3 | unit | redaction filter | Bearer token / client_secret / api_key / pre-auth download URL → `[REDACTED:*]` at DEBUG and INFO alike (FR-005) |
| U4 | unit | unwritable start | unwritable path → no exception; `LoggingSetup.writable=False`; console handler still emits; server object builds (FR-008) |
| U5 | unit | console mirror parity | same records on stderr and file at the configured level (FR-007) |
| U6 | unit | disabled-level laziness | `logger.isEnabledFor(DEBUG)==False` at INFO; %-style call sites never format when disabled (FR-009) |
| U7 | unit | framework routing | root handlers receive `uvicorn.access`-style records when their propagate is on (FR-011 / D2 pin) |
| I1 | integration | SC-001 session records | startup + watcher cycle + ask + embed → INFO records for each in the file; counts and outcomes present, **no question text / file names at INFO** |
| I2 | integration | SC-002 failures logged | embed with a missing path + unknown source → ERROR/WARN records with reasons; zero silent failures |
| I3 | integration | SC-003 DEBUG trace | DEBUG on: one ask trace shows entry(question) → routing decision → hit counts → probe outcome → completion, in order, from the file alone |
| I4 | integration | SC-004 rotation cap | sustained writes keep total log disk ≤ size×count |
| X1 | unit | error-matrix rows | every row of the error-response matrix above |

**Gate**: 100% green before completion (Constitution II); no existing test is weakened — existing suites must stay green with zero edits (the D4 path rule is what makes that possible).
