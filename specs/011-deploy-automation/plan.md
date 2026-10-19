# Implementation Plan: Deployment Automation — One-Command Stack Deploy & Verify

**Branch**: `011-deploy-automation` | **Date**: 2026-10-19 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/011-deploy-automation/spec.md`

## Summary

A non-interactive CLI inside the existing Python package — `python -m agentic_rag_mcp.deploy` — with four subcommands: `redeploy` (build + recreate the sidecar, ensure MCP registration, re-sync Dify's tool cache), `chatflow` (import or in-place update the chatflow from the repo DSL + publish, via the Dify console API), `verify` (headless battery: health, tools, deck round trip, pages/downloads, honest errors, Chat-UI liveness, real chat-level prompt through the service API — with self-cleanup), and `all` (umbrella). Console credentials live in the gitignored config or environment; every step reports honestly and never prompts.

## Technical Context

**Language/Version**: Python 3.12, reusing the installed `agentic_rag_mcp` package and its venv; no new runtime dependencies (`httpx` already present for console/service API calls; `subprocess`/`docker` CLI for stack ops).

**Primary Dependencies**: Dify console API (`POST /console/api/login`, `GET/POST/PUT /console/api/workspaces/current/tool-provider/mcp`, `POST /console/api/apps/imports`, `POST /console/api/apps/<id>/workflows/draft`, publish route); Dify service API (`POST /v1/chat-messages`, streaming — same contract the Chat UI proxy consumes); docker CLI (build/run/exec); postgres via `docker exec docker-db_postgres-1 psql` for the tool-cache re-sync (the validated spec 009 workaround).

**Storage**: none new — state is the running stack plus the existing config file.

**Testing**: pytest three-tier + a fake console HTTP server (the repo already ships this pattern in `tests/integration/conftest.py`); the live battery doubles as the deploy verification. Matrix in [contracts/deploy-cli.md](contracts/deploy-cli.md) (Constitution II).

**Target Platform**: the deployment host (Linux, docker, the running Dify compose stack).

**Project Type**: CLI module inside the existing library.

**Performance Goals**: `verify` completes a full battery (excluding the chat prompt) in < 60 s; the chat-level scenario is bounded by the agent (minutes, honest timeout).

**Constraints**: zero interactive prompts (FR-007); no secrets in repo or logs (FR-006, SC-005); idempotent (FR-008); version-detected workarounds (FR-010); no new runtime services (Constitution III).

**Scale/Scope**: single operator, single host, single Dify workspace.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Justification |
|-----------|--------|---------------|
| I. Contract Preservation | PASS | Wraps deployment operations around frozen runtime contracts; changes no tool schema, route, or app behavior; existing 294-test suite must stay green (matrix V-item) |
| II. Tests-First | PASS | CLI/battery contract matrix defined in `contracts/deploy-cli.md` before implementation; fake-console integration tests precede the console client |
| III. Minimal Dependencies | PASS | No new packages or services; reuses httpx, docker CLI, the existing venv, and the existing config file |
| IV. Honest Answers | PASS | Per-scenario pass/fail with evidence, honest degradation on version drift, nonzero exit on any failure (FR-009), no fabricated success |
| V. Spec-Driven Replacement | N/A | New feature |

## Project Structure

### Documentation (this feature)

```text
specs/011-deploy-automation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── deploy-cli.md   # CLI contract, config keys, battery scenarios, test matrix
└── tasks.md            # (/speckit.tasks output)
```

### Source Code (repository root)

```text
src/agentic_rag_mcp/deploy/
├── __init__.py
├── __main__.py        # CLI: python -m agentic_rag_mcp.deploy {redeploy|chatflow|verify|all} [--dry-run]
├── config.py          # [dify] config section + env overrides; redaction helpers
├── docker_ops.py      # image build, container recreate with documented mounts/networks, health wait, version detect
├── dify_console.py    # login, provider list/register, app find, DSL import, workflow draft update, publish
├── tool_sync.py       # live tools/list → cache payload; DB re-sync path + console-API fallback
├── battery.py         # scenario registry + runner + unique-name cleanup + exit code
└── report.py          # step/scenario output formatting, secret redaction, summary

tests/
├── unit/test_deploy_config.py        # env/config resolution, redaction, version gate
├── unit/test_deploy_sync_payload.py  # tools/list → DB payload; before/after counts
├── integration/test_deploy_console.py # console client against a fake HTTP server
└── contract/test_deploy_cli.py       # subcommand dispatch, dry-run, battery registry, exit codes
```

**Structure Decision**: extends the existing package with one new module (`deploy/`) — the CLI imports the package's config loader and reuses its venv; the battery reuses the MCP call helper pattern proven in the test suites.

## Complexity Tracking

No violations to justify.
