# Research: Application Log File with Leveled Logging

**Feature**: `specs/008-app-logging` | **Date**: 2026-10-12

All decisions resolved against the spec (FR-001..FR-012, three 2026-10-12 user decisions) and the verified codebase. No NEEDS CLARIFICATION remained entering Phase 0.

## D1: Programmatic setup, not dictConfig

**Decision**: a single `configure_logging(cfg) -> LoggingSetup` function in a new `logging_setup.py`, called from `build_server` before anything serves. It attaches a `RotatingFileHandler` + a stderr `StreamHandler` to the **root** logger and sets the root level.

**Rationale**: all existing named loggers (`agentic_rag_mcp.*`) propagate to root, so one setup captures everything with zero per-logger edits (FR-011). Programmatic beats `dictConfig` here because FR-008 (unwritable path → console-only fallback) needs imperative try/except logic around the file handler.

**Alternatives considered**: `logging.config.dictConfig` — rejected: declarative error handling for the fallback is awkward; per-logger handler attach — rejected: 5+ modules to touch, drift-prone.

## D2: Framework logs via root propagation — uvicorn must not self-configure

**Decision**: the container wrapper (`dify/docker/mcp-server/server.py`) calls `uvicorn.run(app, ..., log_config=None)`. With uvicorn's default LOGGING_CONFIG suppressed, the `uvicorn`/`uvicorn.access`/`uvicorn.error` loggers keep their default `propagate=True` and flow to the root handlers → request lines land in the file (user decision 2026-10-12: one complete picture). FastMCP's own loggers (`mcp.server.*`) never self-configure and propagate already.

**Rationale**: attaching our handler onto uvicorn's loggers *after* `uvicorn.run` configures them requires post-start hooks; suppressing the duplicate config is one argument and structurally sound. `log_config=None` is uvicorn's documented "don't touch logging" mode.

**Alternatives considered**: lifespan-time handler patching (fragile, ordering-dependent); accepting uvicorn console-only (violates the ratified decision).

**Known ceiling**: the local `main()` → `mcp.run(transport="streamable-http")` path (used outside Docker) still lets FastMCP's internal uvicorn self-configure → framework logs stay console-only there; application records still reach the file. Documented, not worked around — the container is the deployment.

## D3: Prints convert to log records (no stdout capture hacks)

**Decision**: the two `print()` calls in `server.main()` become `log.info` records (config-init path keeps its functional print — it exits before logging config exists, edge case "bootstrap before configuration").

**Rationale**: FR-011 requires nothing bypass the log file. Redirecting `sys.stdout` into logging (Print-vs-logger capture) is a hack with stdio-protocol hazards; converting the two calls is a two-line diff.

**Alternatives considered**: `sys.stdout` tee wrapper — rejected as over-engineering with protocol risk on stdio transport.

## D4: Default log path derives from `state_db`'s directory — test isolation for free

**Decision**: `log_file` default = `<state_db.parent>/logs/server.log`. Live default (`~/.config/agentic-rag-mcp/logs/server.log`) sits on the mounted volume (container writes to host disk, restarts preserve history). `[logging] log_file` in config.toml overrides; every existing test that constructs `Config(state_db=tmp_path/…)` gets a tmp log file automatically — no test churn, no writes to the real home dir in CI.

**Rationale**: the alternative (absolute default independent of `state_db`) would funnel all `build_server` tests into the operator's real log file, breaking isolation and polluting live logs.

**Alternatives considered**: opt-in logging (default off) — rejected: FR-001 says the file is the default behavior; env-only override — rejected: config.toml is the house configuration surface.

## D5: Redaction filter + DEBUG-only discipline at call sites

**Decision**: two layers. (1) A `RedactionFilter` on **both** handlers applies credential patterns to every record before write: bearer tokens, `client_secret`/`api_key` values, and pre-authenticated Graph download URLs (which embed capability tokens) → `[REDACTED:<kind>]`. (2) The DEBUG-only user-input rule is enforced **by construction at call sites** and pinned by tests: the three INFO lines carrying names/paths re-level to DEBUG (`pipeline.py:68` local locators are file paths; `pipeline.py:159` carries the title) and each sync/embed call adds a count-based INFO summary (`"onedrive embed: 3 embedded, 1 skipped"`). Opaque correlation ids (Graph item ids) stay at INFO — they are not names. A scan test asserts INFO-and-above records contain no question text and no file names/titles.

**Rationale**: a filter can't reliably distinguish "user question text" from arbitrary message content — structural call-site discipline + tests is the honest enforcement; mechanical credential redaction IS filterable and belongs in one place.

**Alternatives considered**: filter-based question detection — rejected (unreliable, false positives); per-call `logger.isEnabledFor` guards at every site — rejected (the lazy %-style calls already avoid formatting cost).

## D6: Rotation + startup writability probe

**Decision**: `RotatingFileHandler(maxBytes=rotation_size_mb*1024*1024, backupCount=rotation_count, encoding="utf-8", delay=True)`. Before attaching, `configure_logging` creates the parent dir and probe-opens the file once in append mode: success → `writable=True`, file handler attaches; `OSError` → `writable=False`, no file handler, an ERROR record goes to the console handler, serving proceeds (FR-008). Mid-run write failures (disk filling) fall through to stdlib's `handleError` → stderr, server keeps serving (spec edge case). `rotation_size_mb` is a float so tests can set `0.001`.

**Alternatives considered**: timed rotation (daily) — rejected: size is what bounds disk; external logrotate — rejected: in-process rotation needs no ops hook.

## D7: `status` additive field from a module-level `LoggingSetup`

**Decision**: `configure_logging` stores a `LoggingSetup(level, level_name, path, writable, fallback_reason)` at module level; the `status` tool serializes it as `{"logging": {"level", "log_file", "writable"}}` (FR-012). Existing status fields untouched (Constitution I).

**Alternatives considered**: re-deriving config in `status` — rejected: the probe result (writable) is runtime state, not config; a separate tool — rejected: additive field is cheaper and discoverable.

## D8: Invalid level → WARN + default, never a crash

**Decision**: level resolution: `LOG_LEVEL` env → `[logging] level` → `"INFO"`. The value is matched case-insensitively against the canonical levels; on no match, the level becomes INFO and — after handlers attach — a `WARNING` record names the bad value (FR-003). The WARN therefore lands in the file and console, satisfying the "honest fallback" edge case.

**Alternatives considered**: crashing on bad config — rejected (logging must never prevent operation); silently ignoring — rejected (Constitution IV).

## D9: DEBUG trace points (FR-004 / US3)

**Decision**: minimal, high-signal `log.debug` additions: tool entry (tool name + arguments — question text/file names allowed here by the ratified DEBUG-only rule) on `ask`, `search`, `sources_*`, `onedrive_*`; routing decision + provenance in `ask`; per-source watcher cycle results; per-file probe outcomes in `onedrive_freshness` (stale/deleted/unchanged/skipped + budget expiry); hit counts before synthesis. Existing INFO lines keep their events; only the name-bearing ones re-level (D5).

**Rationale**: US3's acceptance list (entry → route → hits → probe → completion) is exactly covered; no speculative instrumentation beyond it.

## D10: Error handling — one binding matrix (first-class deliverable)

| Failure | Raised/observed at | Behavior |
|---|---|---|
| Invalid `[logging] level` / `LOG_LEVEL` | configure_logging | Level = INFO; WARNING record names the bad value; server starts (FR-003) |
| Log dir missing | configure_logging | Parent dir created (mkdir -p) |
| Log file unwritable at start (perms/path) | configure_logging | `writable=False`; console-only; ERROR record on console; `status.logging.writable=false`; server starts (FR-008) |
| Disk fills mid-run / mid-run write failure | handler emit | stdlib `handleError` → stderr; serving continues; availability over logging |
| Credential in any message | RedactionFilter | Pattern redacted to `[REDACTED:<kind>]` before write (FR-005) |
| User input at INFO+ | call sites | Structurally absent; scan test fails if reintroduced |
| Rotation rollover error | handler emit | Same as mid-run failure — console fallback, serving continues |
| Unwritable *and* misconfigured level | configure_logging | Both fallbacks compose: INFO level, console-only, honest records for both |

**Rationale**: every row is a named test (X1); the live OneDrive rounds proved the cost of swallowed errors — this matrix is the feature's Constitution IV teeth.

## D11: Test strategy — RED first, tmp-isolated, no network

**Decision**: three layers:

1. **Unit** (`test_logging_setup.py`): level resolution + invalid-value WARN (U1/D8); rotation bounds with tiny `rotation_size_mb` (U2/D6); redaction patterns incl. a bearer token, a secret, a pre-auth URL (U3/D5); unwritable path → `LoggingSetup.writable=False`, console-only, no exception (U4/D6); console mirror parity (U5); disabled-level laziness — `logger.isEnabledFor(DEBUG)` guards and %-style args mean no formatting when off (U6/D5); bootstrap ordering (invalid-level WARN lands in the file too).
2. **Contract** (`test_logging_contract.py`): `status` keeps every existing field and gains exactly the additive `logging` block (C1/FR-012); config surface — toml `[logging]` and `LOG_LEVEL` env override resolve (C2/D4).
3. **Integration** (`test_logging_integration.py`): SC-001 session — startup + watcher cycle + ask + embed produce the expected INFO records in the file (I1); SC-002 — an induced failure (bad path embed / unknown source) yields WARN/ERROR with the reason (I2); SC-003 — DEBUG on: one `ask` traces entry → route → hits → completion readably from the file (I3); SC-004 — sustained writes past the threshold keep total usage ≤ size×count (I4); SC-005 — scan all levels for credential patterns (zero) and INFO+ for question text/names (zero) (folded into I1/I2 assertions + a dedicated scan test).

**Rationale**: each spec SC maps to ≥1 named test; every D10 row maps to the X1 matrix in [contracts/logging.md](contracts/logging.md); tmp isolation comes from the D4 path rule, so no existing test needs edits beyond the new files.

**Alternatives considered**: pytest logcap-only assertions — rejected: the feature IS file writing, so tests must read real files under tmp; logrotate/systemd-journal integration tests — rejected: out of scope.
