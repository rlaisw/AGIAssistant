# Contract — Deploy CLI (Phase 1)

Interface contract for `python -m agentic_rag_mcp.deploy`. **Constitution I: no runtime contract changes anywhere — this feature only wraps operations around the frozen stack.**

## Commands

| Command | Steps | Exit |
|---|---|---|
| `redeploy [--dry-run]` | build image → recreate container (documented mounts/networks/port) → health wait → ensure MCP registration (create if absent) → tool-cache re-sync (version-gated DB path; skip with notice when unavailable) | 0 / step-failure / 2 config |
| `chatflow [--dry-run]` | console login → find app by DSL name → **draft-update** existing (`POST /apps/<id>/workflows/draft` with the DSL workflow) or **import** absent (`POST /apps/imports`) → publish | 0 / step-failure / 2 config |
| `verify [--dry-run] [--skip-chat]` | run the battery registry in order; unique `verify_<ts>` project names; teardown sweep at start and end | 0 / N failed / 2 config |
| `all [--dry-run]` | redeploy → chatflow → verify (umbrella; aborts on step failure before the battery) | as above |

`--dry-run`: prints the resolved configuration (redacted) and the planned steps; touches nothing; exit 0. Every command echoes its effective (redacted) configuration at start — FR-007.

## Battery scenario registry (fixed order)

| id | Checks | Evidence |
|---|---|---|
| `health` | sidecar `/healthz` = ok | HTTP code |
| `tools-surface` | MCP `tools/list` count and `ppt_*` presence | tool count, ppt list |
| `deck-roundtrip` | init → write fixture page → check passing → export | project id, page_url |
| `completion-page` | page_url serves HTML with download + slide; slide asset `image/svg+xml`; `.pptx` download valid OOXML | codes, sizes |
| `honest-errors` | unknown deck 404; traversal 400/404; missing icon envelope | codes, error codes |
| `chat-ui-liveness` | `GET :3000` responds | HTTP code |
| `chat-journey` *(skipped with notice when no API key or `--skip-chat`)* | service-API streaming prompt "generate a one-page deck about …" → answer contains a deck link → page serves → file downloads | answer fragment, link, codes |

Cleanup: every `verify_<ts>` project created by the battery is removed at teardown; a start-sweep removes orphans from crashed runs and reports them (FR-011).

## Config contract (env overrides config file)

| Key | Env | Default |
|---|---|---|
| `[dify] console_url` | `DIFY_CONSOLE_URL` | `http://localhost` |
| `[dify] console_email` | `DIFY_CONSOLE_EMAIL` | — (required for redeploy/chatflow console steps) |
| `[dify] console_password` | `DIFY_CONSOLE_PASSWORD` | — (required as above) |
| `[dify] api_key` | `DIFY_API_KEY` | — (enables `chat-journey`) |
| `[deploy] sidecar_image` | — | `agentic-rag-mcp:latest` |
| `[deploy] container` | — | `agentic-rag` |
| `[deploy] db_container` | — | `docker-db_postgres-1` |

Missing credentials for a step that needs them → exit 2 with one-line setup instructions, before any stack mutation. All evidence strings pass redaction (passwords, API keys masked).

## Test-case matrix (Constitution II — defined before implementation)

Legend: U = unit, I = integration (fake console server), C = contract (CLI-level).

| # | Case | Tier | Expected |
|---|---|---|---|
| P01 | config: file values, env overrides, defaults | U | resolution order honored |
| P02 | redaction masks password/api_key in evidence | U | no secret in any formatted output |
| P03 | missing console credentials for console command | C | exit 2, setup instructions, no mutation |
| P04 | sync payload built from fixture tools/list | U | exact `{name, title, description, inputSchema}` list, count preserved |
| P05 | version gate: 1.17.x → db path; unknown → skipped-with-notice | U | correct path chosen / honest notice |
| P06 | login success/401 against fake console | I | token captured / honest failure text |
| P07 | provider absent → create called with documented name/URL | I | POST body asserted |
| P08 | provider present → no create, re-sync path selected | I | no duplicate registration |
| P09 | app exists → draft-update; app absent → import | I | correct endpoint per state |
| P10 | publish called after import/update | I | publish route hit |
| P11 | `--dry-run` prints plan, touches nothing, exit 0 | C | no docker/API side effects |
| P12 | battery registry contains every scenario id in this contract | C | registry == contract table |
| P13 | verify exit code equals failed-scenario count | C | 0/N semantics |
| P14 | teardown removes verify_<ts> projects (including pre-existing orphans) | C | no leftovers; orphans reported |
| P15 | chat-journey skipped honestly without api_key | C | notice, not failure |
| P16 | existing pytest suite unchanged (294 tests green) | C | Constitution I |

Fixtures: a small `tools/list` JSON and a minimal DSL YAML under `tests/fixtures/deploy/`.
