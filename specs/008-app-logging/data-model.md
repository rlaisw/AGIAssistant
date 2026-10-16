# Data Model: Application Log File with Leveled Logging

**Feature**: `specs/008-app-logging` | **Plan**: [plan.md](plan.md)

All shapes are config structures or runtime value objects — no new persistent stores; the log file is the artifact.

## Configuration (`[logging]` section in config.toml → Config fields)

| Field | Type | Default | Rule |
|-------|------|---------|------|
| `log_level` | str | `"INFO"` | One of DEBUG / INFO / WARNING / ERROR, case-insensitive (prose shorthand WARN = WARNING). Invalid → INFO + WARNING record naming the value (FR-003) |
| `log_file` | Path | `<state_db.parent>/logs/server.log` | On the mounted volume in deployment; state_db-derived default keeps test isolation (D4). Unwritable → console-only fallback (FR-008) |
| `rotation_size_mb` | float | `10.0` | `maxBytes = value × 1024 × 1024`; float so tests can shrink it |
| `rotation_count` | int | `5` | `backupCount`; total cap = size × count |

Resolution order: `LOG_LEVEL` env var → `[logging] level` → default. File/rotation: `[logging]` only (no env besides level — YAGNI).

## Runtime value objects

### LoggingSetup (module-level, set by configure_logging, read by status)

| Field | Type | Rule |
|-------|------|------|
| `level_name` | str | Canonical level in effect (e.g. `"INFO"`) |
| `level` | int | Numeric level for handler attachment |
| `path` | Path | Resolved log file path |
| `writable` | bool | Probe result at configure time; False ⇒ console-only fallback active |
| `fallback_reason` | str \| None | Set when writable=False or level fell back; surfaced in records |

### LogRecord semantics (format: `%(asctime)s %(levelname)s %(name)s %(message)s`, UTC)

| Field | Source | Rule |
|-------|--------|------|
| timestamp | asctime | UTC, ISO-like |
| level |levelname | Semantics per spec FR-002: INFO = working as expected; WARNING (prose: WARN) = degraded/retryable; ERROR = failed operation |
| component | name | The emitting logger — `agentic_rag_mcp.*`, `uvicorn.*`, `mcp.server.*` (FR-011) |
| message | msg % args | Redacted by the filter; user input only at DEBUG (FR-005) |

### RedactionRule (filter patterns — binding list)

| Pattern (compiled) | Replacement | Rationale |
|---|---|---|
| `(Bearer\s+)[A-Za-z0-9._\-]+` | `\1[REDACTED:token]` | Graph auth headers |
| `(client_secret["']?\s*[:=]\s*["'])[^"']+` | `\1[REDACTED:secret]` | Azure app secrets in any echoed config |
| `(api[_-]?key["']?\s*[:=]\s*["'])[^"']+` | `\1[REDACTED:secret]` | web provider keys |
| `https://\S*(?:tempauth|api\.onedrive\.com)\S*` | `[REDACTED:download-url]` | pre-authenticated Graph download URLs embed capability tokens |

Structural rule (not a pattern): question text, file names/titles, and path locators appear in DEBUG records only; INFO-and-above records carry counts, statuses, and opaque correlation ids.

## State transitions

```
configure_logging(cfg):
  resolve level (env > toml > default; invalid → INFO + pending WARN)
  ensure parent dir; probe-open file
    ├── writable  → attach file handler + console handler → emit pending WARN (if any) at file+console
    └── OSError   → attach console handler only → ERROR record "log file not writable: <reason>"
status: serialize LoggingSetup → {"logging": {level, log_file, writable}}
```

Mid-run: rotation at threshold (file → .1 … .5, oldest dropped); mid-run write failure → stdlib handleError → stderr; serving never blocks on logging.

## Error taxonomy (binding mapping)

| Condition | Detected | Result |
|-----------|----------|--------|
| Invalid level string | configure_logging | INFO + WARNING record; server starts |
| Log dir/file unwritable at start | configure_logging probe | console-only + ERROR record; `writable=false` in status; server starts |
| Disk full / mid-run emit failure | handler `handleError` | stderr note; serving continues |
| Credential in message | RedactionFilter | `[REDACTED:<kind>]` at every level |
| User input at INFO+ | call-site discipline + scan test | structurally absent; test fails if reintroduced |
