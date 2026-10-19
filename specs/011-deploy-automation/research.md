# Research — Deployment Automation (Phase 0)

Decisions with rationale and rejected alternatives.

## R1. CLI shape

**Decision**: `python -m agentic_rag_mcp.deploy <subcommand>` with `redeploy`, `chatflow`, `verify`, `all`, and a global `--dry-run`. Run with the same venv/pipx environment as the server.

**Rationale**: reuses the installed package, its config loader, and httpx; zero new entry points to install; `--dry-run` makes every step inspectable before it touches the stack (supports the honesty and idempotency FRs).

**Alternatives**: a standalone shell script (no testability, secrets in process lists); a Makefile target per step (same, worse quoting); a new MCP tool that deploys the server that hosts it (circular and dangerous).

## R2. Chatflow update strategy (in-place vs import)

**Decision**: if an app with the DSL's name exists, push the DSL's workflow as the app's **draft** (`POST /console/api/apps/<id>/workflows/draft` — the same endpoint the browser editor uses) and publish; otherwise `POST /console/api/apps/imports` the full DSL and publish.

**Rationale**: Dify's import always creates a new app; draft-update preserves the existing app id, its API key, and its published history — matching the spec's "update in place; never delete other apps" default. The draft payload is the DSL's `workflow` section (`graph`, `features`, `conversation_variables`, `environment_variables`).

**Alternatives**: import + delete-old (destructive to conversations and the service API key); DB-level workflow row surgery (fragile, bypasses validation).

## R3. Console authentication and credential storage

**Decision**: `POST /console/api/login` with email+password → access token, used for provider/register/draft/publish calls. Credentials resolve from `[dify]` in the existing config file (`console_url`, `console_email`, `console_password`) with environment overrides (`DIFY_CONSOLE_EMAIL`, `DIFY_CONSOLE_PASSWORD`, `DIFY_CONSOLE_URL`); the service API key for chat-level checks from `[dify] api_key` or `DIFY_API_KEY`. All output passes a redaction helper that masks these values (SC-005).

**Rationale**: the config file lives outside the repo (already the pattern); env overrides suit CI/one-shot runs; one login per command execution keeps tokens short-lived.

**Alternatives**: long-lived console tokens (Dify rotates them); storing credentials in the repo (violates FR-006).

## R4. MCP registration + tool-cache re-sync

**Decision**: `GET /console/api/workspaces/current/tool-provider/mcp` lists providers. If `agentic-rag` is absent → `POST` create with the documented name/URL (the create path fetches tools itself — verified in the controller source). If present → re-sync via the **DB path validated during spec 009 deployment**: fetch the live `tools/list` from the sidecar, build the exact cached-blob shape (`{name, title, description, inputSchema}`), and update `tool_mcp_providers` through `docker exec docker-db_postgres-1 psql`. The path is gated on the detected Dify version (from the api container) and the availability of the docker CLI; either being absent is reported honestly and the step is skipped with an explicit notice (FR-010).

**Rationale**: the console "Update" flow is known-broken for tool re-sync in Dify 1.17 (source-verified: tools only refresh when the URL changes); the DB path is the validated workaround. Creation via console API is clean and populates the cache correctly.

**Alternatives**: console-API update only (broken in 1.17); always-DB (works, but skips validation the create path provides); direct TCP to postgres (breaks if Dify changes the network layout; docker exec is stable).

## R5. Verification battery

**Decision**: a registry of named scenarios executed in order, each returning pass/fail + evidence (HTTP codes, counts, paths, answer fragments): health, tools surface (count + ppt_* presence), deck round trip (init → write → check → export via MCP), completion page + slide asset + download, honest 404/400 probes, Chat-UI liveness (`GET :3000`), and the chat-level journey (service-API streaming prompt → parse answer → extract deck link → page serves → file downloads). Chat prompts use `verify_<timestamp>` project names; teardown removes the created projects (sweep on start and end — FR-011). Exit code = number of failed scenarios.

**Rationale**: the scenarios are exactly the ones run manually during specs 009/010 validation; SSE parsing of the service API is already proven in the Chat UI proxy (`ai-chat-landing/app/api/chat/route.ts` is the reference behavior); unique names + sweeps make reruns safe (FR-008/FR-011).

**Alternatives**: browser automation (heavy, contradicts headless goal); reusing the pytest suites as the battery (they need the repo's test env and don't cover the Dify layer).

## R6. Redeploy mechanics

**Decision**: `docker_ops` shells out to the docker CLI with the exact DEPLOY.md-documented invocation (build from repo root, `docker rm -f` + `docker run` with the three mounts + both networks + port + restart policy, bounded health-wait loop on `/healthz`). Version detection reads `DIFY_VERSION` from the api container for R4's gate.

**Rationale**: one source of truth — the runbook command; no docker SDK dependency; health-wait covers the restart edge case from the spec.

**Alternatives**: docker SDK for Python (new dependency, no benefit); compose files (the sidecar isn't compose-managed).

## R7. Test strategy (Constitution II)

**Decision**:
- **unit**: config/env resolution + redaction (every secret shape masked), version-gate logic, sync-payload building from a fixture `tools/list` (correct `{name, title, description, inputSchema}` shape and count).
- **integration**: the console client against a fake HTTP server (stdlib `http.server`, the existing conftest pattern) — login flow, provider list/create, draft-update vs import decision, publish, and the honest failures (401 → setup instructions).
- **contract**: CLI dispatch (`--dry-run` prints the plan and exits 0 without touching the stack), battery registry completeness (every spec scenario id present), exit codes (0 all-pass; N failures; 2 config error), and the full existing pytest suite staying green (Constitution I).

**Alternatives**: testing only against the live stack (unreliable, order-dependent); mocking docker exec (would not prove the psql invocation).

## R8. Config surface

**Decision**: `[dify]` section in the existing config file: `console_url` (default `http://localhost`), `console_email`, `console_password`, `api_key` (chat-level verification), `app_name` (default: the DSL's app name), plus `[deploy]`: `sidecar_image` (default `agentic-rag-mcp:latest`), `container` (default `agentic-rag`), `db_container` (default `docker-db_postgres-1`). Environment variables override all. Defaults for everything — FR-007.

**Rationale**: mirrors the existing config conventions; nothing new to install; every default matches DEPLOY.md so the fresh-host path works with an empty section.
