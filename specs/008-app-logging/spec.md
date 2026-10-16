# Feature Specification: Application Log File with Leveled Logging

**Feature Branch**: `008-app-logging`

**Created**: 2026-10-12

**Status**: Draft

**Input**: User description: "Setup AgenticRAG application log file. Log Level: INFO is used to record events that indicate the application is working as expected. WARN and ERROR provide something is broken, operation failed. DEBUG provides detailed information for developers to understand what's happening — allows developers to find the source of the problem quickly. DEBUG logs show exactly what the code is doing: you can trace variable values, function calls, and execution flow. This is invaluable when you're trying to find out why something isn't working."

## Clarifications

### Session 2026-10-12

- Q: What are the level semantics? → A: (User-provided, ratified verbatim) **INFO** records events that indicate the application is working as expected. **WARN and ERROR** record that something is broken or an operation failed. **DEBUG** provides detailed information for developers — exactly what the code is doing, including variable values, function calls, and execution flow — so a developer can find the source of a problem quickly.
- Q: Default level? → A: **INFO** — the description positions INFO as the working-as-expected baseline; DEBUG is opt-in for troubleshooting sessions.
- Q: Where do logs live? → A: A persistent log file on the mounted config volume so history survives container restarts; console (stdout) output is retained so container-level log capture keeps working.
- Q: May log records contain user questions and embedded file names, and at which level? → A: **DEBUG only** (user decision, 2026-10-12). Question text and file names appear in DEBUG records — that is where tracing needs them; INFO-and-above records identify the operation and outcome without quoting user input, keeping the steady-state log compact and content-free.
- Q: Should the log file capture framework request logs (uvicorn/MCP HTTP access lines) too? → A: **Yes — one complete picture** (user decision, 2026-10-12). Framework request records go to the file alongside application records, so the file correlates what the application did with what came in over the wire during an incident read-through.
- Q: Should the status tool report the current logging configuration? → A: **Yes** (user decision, 2026-10-12). `status` gains an additive `logging` field — active level, log file path, writable yes/no — so a chat operator (or the Dify agent) can see the logging state without shell access; existing status fields unchanged (Constitution I).
- Q: (double-clarify scan findings) What neglected matters were found and closed? → A: (scan defaults, 2026-10-12) Stray `print` output (e.g., startup banners) routes through the same setup so nothing bypasses the log file (FR-011 completion); a mid-run log write failure (disk filling while serving) falls back to console output and never blocks serving — availability over logging; the prose term WARN is normalized as shorthand for the canonical WARNING level.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Every event recorded to a persistent log file with level semantics (Priority: P1)

The application writes log records to a persistent file. A record shows the time, the severity, the component that emitted it, and the message. Routine successful operations (server start, watcher cycle completed, file embedded, question answered) appear at INFO. Failures and broken states appear at WARN or ERROR with the reason. Nothing fails silently: every operation failure a user can see also has a corresponding WARN/ERROR record in the log.

**Why this priority**: The log file is the product. Without complete, correctly-leveled records the other stories have nothing to stand on, and operations stay blind — exactly the pain the live OneDrive debugging rounds exposed (a swallowed MSAL error cost a full troubleshooting round-trip).

**Independent Test**: Start the server, run one local sync and one question → the log file contains an INFO record for the startup, one per sync result, and one for the answer; forcing a failing operation produces an ERROR/WARN record carrying the reason.

**Acceptance Scenarios**:

1. **Given** a fresh start, **When** the server starts, **Then** the log file exists and contains a startup record at INFO with the configured transport and log level.
2. **Given** normal operation, **When** a watcher cycle or an explicit embed completes, **Then** an INFO record names the source and the outcome (counts, durations).
3. **Given** any operation failure (missing file, unreachable provider, sign-in failure), **When** it is returned honestly to the caller, **Then** the log contains a WARN or ERROR record with the same reason — never only a silent swallow.
4. **Given** a source degrades or recovers, **When** the health transition happens, **Then** a record is written at the matching level (degrade → WARN, recover → INFO).
5. **Given** the server restarts, **When** a previously written log file is in place, **Then** new records append to it — history is preserved.

### User Story 2 - Operator-configurable level without code changes (Priority: P2)

The operator sets the log level through configuration (config file or environment). Default is INFO. Setting DEBUG turns on developer tracing for a troubleshooting session; setting WARN or above quiets the working-as-expected noise while keeping failures visible. An invalid level value falls back to the default with an honest WARN record — never a crash.

**Why this priority**: The level knob is what makes the log useful across contexts — quiet in steady state, loud when debugging. A bad value must not take the server down.

**Independent Test**: Start with default → only INFO+ records present; restart with DEBUG → trace records appear; restart with an invalid level → server starts, records the fallback WARN, and logs at the default.

**Acceptance Scenarios**:

1. **Given** default configuration, **When** the server runs, **Then** only INFO and above are recorded.
2. **Given** the level is set to DEBUG, **When** the server restarts, **Then** DEBUG records appear, including the additive `logging` field on `status` reporting the active level.
3. **Given** the level is set to ERROR, **When** normal operations succeed, **Then** no records appear; **When** an operation fails, **Then** the ERROR record does.
4. **Given** the level is misspelled (e.g. `INF0`), **When** the server starts, **Then** it logs at the default level and records an honest WARN about the invalid value.

### User Story 3 - DEBUG traces execution flow to the problem's source (Priority: P2)

With DEBUG on, a developer can follow one operation end to end: entry with arguments, the decisions taken along the way (routing, tool selection, provider fallbacks), the external calls made and their statuses, key variable values, and the exit with the result. This is the "why isn't this working" instrument: read one operation's slice of the log and locate the failing step without a debugger attached.

**Why this priority**: The user's stated purpose for DEBUG — find the source of a problem quickly. It completes the logging story but is not needed for basic operational visibility (US1).

**Independent Test**: With DEBUG on, run one `ask` whose answer cites an embedded OneDrive file → the log slice for that question shows, in order: question received, routing decision, search hit counts, freshness probe outcome, answer completed — a readable end-to-end trace.

**Acceptance Scenarios**:

1. **Given** DEBUG is enabled, **When** any MCP tool is called, **Then** a record shows the tool name and its arguments at entry and the outcome at exit.
2. **Given** DEBUG is enabled, **When** an answer routes through the decision layer, **Then** the chosen route and the reason are recorded.
3. **Given** DEBUG is enabled, **When** a freshness probe runs, **Then** each probed file, the comparison result, and the budget outcome are recorded.
4. **Given** DEBUG is enabled, **When** external requests (web, cloud drive) are made, **Then** the target and status are recorded (no credentials — see FR-005).
5. **Given** DEBUG is disabled (INFO), **When** the same operations run, **Then** DEBUG record content is never evaluated — no measurable cost from being off.

### Edge Cases

- What if the log directory does not exist or the file cannot be written? → The server still starts: fall back to console-only output and record an ERROR/WARN about the fallback (in the console) — logging must never prevent the application from running.
- What if the log file grows unboundedly? → Size-based rotation keeps a bounded number of generations; total disk usage is capped. (This host lost 89 GB to unbounded artifacts once already — logs must not repeat that.)
- What if several threads write at once (request handlers + watcher)? → Records are appended atomically per line; no interleaved/corrupted records.
- What if a record message would contain a secret? → Redaction happens before write: tokens, client secrets, device codes, and file contents never appear at any level; a placeholder records the fact instead.
- What if the disk fills while the server is running? → Failed file writes surface on the console and never block serving — availability over logging; the server keeps operating normally and the fallback is recorded honestly.
- What if the level value is invalid? → Fall back to the default level with an honest WARN (US2 scenario 4) — never crash, never silently ignore the bad value.
- What if the clock changes? → Timestamps are UTC and monotonic per process; a skew is observable but never fabricates ordering within a record.
- What if rotation happens mid-operation? → The active file is switched transparently; records continue without loss.
- What if a component logs before configuration loads? → A bootstrap record goes to console; file logging attaches once configuration is resolved.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The application MUST write log records to a persistent log file on the mounted configuration volume, each record carrying a UTC timestamp, severity level, originating component name, and message.
- **FR-002**: Level semantics MUST hold as ratified: INFO = working-as-expected events (startup, watcher cycles, embeds, health transitions, answers); WARN = degraded or retryable failures; ERROR = failed operations requiring attention. Every user-visible operation failure MUST have a corresponding WARN/ERROR record with the same reason — no silent failures (Constitution IV).
- **FR-003**: The level MUST be operator-configurable without code changes (configuration file and environment override), defaulting to INFO; an invalid value MUST fall back to the default with an honest WARN record, never a crash.
- **FR-004**: With DEBUG enabled, the log MUST allow one operation to be traced end to end: tool entry with arguments, routing/decision outcomes, external call targets and statuses, key variable values, and exit result. User input (question text, embedded file names) appears at DEBUG only.
- **FR-005**: Secrets MUST be redacted before writing at every level: access tokens, client secrets, device codes, and embedded file contents never appear; a placeholder records their presence. User question text and embedded file names appear in DEBUG records only — INFO-and-above records identify the operation and outcome without quoting user input.
- **FR-006**: The log file MUST be size-rotated with a bounded number of generations so total log disk usage is capped.
- **FR-007**: Console (stdout) output MUST be retained at the same effective level so container log capture continues to work.
- **FR-008**: An unwritable log destination MUST NOT prevent server start — the server falls back to console-only output and records the failure honestly.
- **FR-009**: Disabled-level message content MUST NOT be evaluated (lazy formatting) — running with DEBUG off has no measurable overhead.
- **FR-010**: Existing tool behavior and response shapes MUST be unchanged; logging is purely additive (Constitution I).
- **FR-011**: All loggers MUST route through the single configured file+console setup — the application's named component loggers (pipeline, watcher, freshness, server) AND the framework/server request loggers (uvicorn, MCP library) AND any stray print-style output (e.g., startup banners) — one file carries the complete picture, application semantics and wire traffic together; nothing bypasses the log file.
- **FR-012**: The `status` tool MUST include an additive `logging` field — active level, log file path, and whether the file is writable — while all existing status fields remain unchanged (Constitution I).

### Key Entities

- **LoggingConfig**: `log_file` (path on the persistent volume), `level` (DEBUG | INFO | WARNING | ERROR; default INFO; env-overridable), `rotation_size_mb` (default 10), `rotation_count` (default 5).
- **LogRecord semantics**: timestamp (UTC) · level (semantic per US1) · component (originating module name) · message (redacted, human-readable).
- **RedactionRule**: credential patterns (bearer tokens, client secrets, device codes) and document content are replaced with `[REDACTED:<kind>]` before any record is emitted; user question text and embedded file names are DEBUG-only and never appear in INFO-and-above records.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Under default settings, a session of startup + one local watcher cycle + one question + one explicit embed produces INFO records for every listed event — verified by reading the log file after the session.
- **SC-002**: 100% of induced operation failures (missing file, unreachable cloud, bad source id) produce a WARN/ERROR record with the failure reason — zero silent failures in tests.
- **SC-003**: With DEBUG on, a single cited-question trace shows at minimum: tool entry, routing decision, retrieval hit count, freshness outcome, completion — a developer can locate the failing step of a broken operation from the log alone.
- **SC-004**: Sustained operation beyond the rotation threshold keeps total log disk usage at or below `rotation_size_mb × rotation_count` — rotation is verifiable by disk inspection.
- **SC-005**: Scanning all emitted records at every level for credential-shaped content (bearer tokens, secrets, device codes) and for embedded file contents yields zero matches; scanning INFO-and-above records for user question text also yields zero matches.
- **SC-006**: Pointing `log_file` at an unwritable path still starts the server with console logging and an honest record of the fallback.
- **SC-007**: The full test suite stays green; logging changes are additive to behavior and contracts.

## Assumptions

- Implementation uses the Python standard-library logging stack with a rotating file handler (Constitution III — zero new dependencies).
- Configuration extends the existing `config.toml` with a `[logging]` section; a `LOG_LEVEL` environment variable overrides it for container deployments; changes apply from the next server start (no live reload — YAGNI).
- Default log location: the mounted configuration volume (`…/.config/agentic-rag-mcp/logs/`), so history survives container recreation; rotation defaults 10 MB × 5 generations (~50 MB cap).
- Console handler mirrors the file at the same level; container log capture (docker logs) continues to work unchanged.
- Component names in records use the existing named loggers (`agentic_rag_mcp.*`) so existing call sites gain file output without per-site changes.
- Document **sizes, counts, and outcome categories** are safe to log at any level; document titles/names, paths, and question text are DEBUG-only per the 2026-10-12 clarification; file contents are never logged.
- Out of scope: remote log shipping, structured/JSON log format, per-module level overrides, live level reload, and audit logging.
