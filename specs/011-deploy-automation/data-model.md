# Data Model — Deployment Automation (Phase 1)

The CLI is stateless between runs; entities describe a run and its configuration.

## Deployment Run

One execution of a subcommand.

| Field | Type | Rules |
|---|---|---|
| `command` | enum | `redeploy` \| `chatflow` \| `verify` \| `all` |
| `dry_run` | bool | when true: print the plan, touch nothing, exit 0 |
| `steps` | list[Step] | ordered; each completed or failed with evidence |
| `exit_code` | int | 0 success · N failed scenarios · 2 configuration error |

**Lifecycle**: `started` → each step `ok`/`failed` → `summary` (failures first). A failed non-battery step aborts the command honestly with remediation text.

## Step

| Field | Type | Rules |
|---|---|---|
| `name` | string | stable id (e.g. `build-image`, `register-mcp`, `import-dsl`) |
| `status` | enum | `ok` \| `failed` \| `skipped` (with honest reason, e.g. version gate) |
| `evidence` | string | redacted, human-readable (counts, codes, paths) |

## Verification Scenario

The battery's unit.

| Field | Type | Rules |
|---|---|---|
| `id` | string | stable (e.g. `health`, `tools-surface`, `deck-roundtrip`, `chat-journey`) |
| `check` | callable | headless; returns pass/fail + evidence |
| `cleanup` | callable? | registered alongside check (unique-name project teardown) |

**Lifecycle**: registered at startup (fixed order), executed per run, result recorded; failed scenarios never abort the battery early (the full picture is the value).

## Console Credential (config-resolved, never persisted by the CLI)

| Field | Type | Rules |
|---|---|---|
| `console_url` | URL | default `http://localhost` |
| `email` / `password` | strings | from `[dify]` config or `DIFY_CONSOLE_*` env; both required for console steps; absence → exit 2 with setup instructions |
| `api_key` | string | service API key for the chat-level scenario (`DIFY_API_KEY` env or config) |

**Redaction rule**: any occurrence of the password or API key in step evidence is masked (`***`).

## Tool Cache Snapshot

| Field | Type | Rules |
|---|---|---|
| `before` | list[str] | provider's cached tool names at start |
| `after` | list[str] | post-sync names — must equal the live `tools/list` names |
| `path` | enum | `console-create` (registration) \| `db-resync` \| `skipped` (honest reason) |

## Relationships

```text
Deployment Run 1 ──── * Step
Deployment Run (verify) 1 ──── * Verification Scenario (registry, fixed order)
Console Credential 1 ─ 1 deployment run (resolved at start, echoed redacted)
Tool Cache Snapshot 1 ─ 1 register/sync step
```

## Deliberately NOT modeled

Persistent run history/databases (a run is a terminal transcript), cross-host orchestration, browser-visual checks, Chat UI process management (liveness only).
