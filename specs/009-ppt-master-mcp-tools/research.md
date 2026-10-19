# Research — PPT-Master MCP Tools (Phase 0)

Resolves the deferred decisions from the spec and plan. Each entry: Decision / Rationale / Alternatives considered.

## R1. How the sidecar executes ppt-master (runtime integration)

**Decision**: subprocess bridge. The MCP tools shell out to the ppt-master scripts (`project_manager.py`, `icon_sync.py`, `svg_quality_checker.py`, `svg_to_pptx.py`) using the container's Python, with the ppt-master clone mounted read-only into the container at a configured path.

**Rationale**: ppt-master is an installed external tool with its own update path (`update_repo.py` git pulls); wrapping its CLI keeps the clone authoritative and upgradeable with zero re-vendoring. Its scripts are already designed as stable CLI entry points (the skill drives them exactly this way). The sidecar image bakes only the pip dependencies the scripts need.

**Alternatives**:
- *Vendor the scripts into `src/`*: rejected — forks the tool, loses `update_repo.py` pulls, duplicates ~8k lines (Constitution III).
- *Reimplement the pipeline natively*: rejected — the checker/exporter are large and battle-tested; reimplementation is the biggest risk in the whole feature.
- *Mount the host venv*: rejected — venv shebangs and interpreter symlinks target host paths; python:3.12-slim in the container may not match the host interpreter. Installing the deps list into the image is deterministic.

## R2. File delivery (download URL)

**Decision**: extend the existing HTTP wrapper (`dify/docker/mcp-server/server.py`, the process that already serves `/healthz` and the MCP endpoint on 28080) with a static route `GET /exports/<project_dir>/<filename>.pptx` rooted at the configured exports root.

**Rationale**: one port, one process, no new service (Constitution III); the URL is returned by `ppt_export` as an absolute link the Dify agent embeds in its answer; markdown link rendering already works in both the Chat UI and the Dify webapp.

**Alternatives**:
- *Serve via Dify's nginx (port 80)*: rejected — couples file delivery to the Dify compose and adds a container-to-container volume share.
- *Separate file server (nginx/minio)*: rejected — a new runtime service for static files is the "last resort" Principle III warns about.
- *Dify native file-output variables*: rejected — heavier chatflow wiring (file variables through the agent node) and no benefit over a link the client can already render.

## R3. Tool granularity and the agent repair loop

**Decision**: five tools exactly as specified (`ppt_project_init`, `ppt_icon_sync`, `ppt_write_page`, `ppt_check`, `ppt_export`); write and check stay separate.

**Rationale**: separation is what lets the Dify agent converge: `ppt_check` returns structured, fixable violations and the agent rewrites the page via `ppt_write_page`. A merged write+check tool was considered to halve round trips, but it hides the repair loop and still needs a standalone check for re-exports after edits (FR-015). Iteration budget is handled by raising the agent node's max iterations (≥ 30), not by collapsing tools.

**Alternatives**: single opaque `generate_ppt` tool (Option B in the spec — rejected: no self-repair); merged write+check (rejected above).

## R4. Agent rulebook (distilled instructions)

**Decision**: a single distilled markdown rulebook (`dify/ppt-master-rulebook.md`, ~2–3k tokens) pasted into the PPT-Master agent node's instructions, covering: tool-call protocol (init → icons → write per page → check → fix loop → export), the quick-generate SVG contract subset (canvas 1280×720, grouping with `data-pptx-bounds`, text sizing + line-break tspans, forbidden constructs), the error-envelope handling rules, and honest-failure behavior.

**Rationale**: the full ppt-master skill is far too large for a Dify node prompt; the quick-generate profile needs only a stable subset. Keeping the rulebook as a repo file (not just pasted DSL text) makes it reviewable and diffable; the chatflow YAML embeds a copy.

**Alternatives**: full SKILL.md injection (rejected — context size); letting the agent improvise (rejected — quality gate convergence would collapse).

## R5. Concurrency and project isolation

**Decision**: no locks. Each `ppt_project_init` gets a unique directory (ppt-master already suffixes `_<YYYYMMDD>`; the bridge additionally disambiguates with a short random suffix on collision). Concurrent requests operate on disjoint directories; subprocesses are isolated OS processes.

**Rationale**: the failure modes of locks (stale locks, deadlock across containers) buy nothing when isolation is structural. SC-006 is satisfied by construction and verified by a contract test running two interleaved inits.

## R6. Error handling design (per user directive)

**Decision**: a single `PptError` hierarchy in `src/agentic_rag_mcp/ppt/errors.py` (InvalidProject, ScriptFailure, CheckFailed, ExportBlocked, MissingIcon, WorkspaceError), each mapping to the shared error envelope `{error: {code, message, hint}}` returned by every tool. Script stderr is captured, truncated (≤ 2k chars), and included verbatim in `message`; `hint` carries the remediation the agent can act on (e.g., "re-pick the icon from tabler-outline and retry").

**Rationale**: FR-010 requires machine-readable honesty; the Dify agent needs `hint` text it can follow without human help. Capturing stderr verbatim preserves ppt-master's own detailed diagnostics (the checker's issue lines are the agent's repair instructions).

**Alternatives**: raising raw exceptions to FastMCP (rejected — unstructured, agent can't act); swallowing errors into empty results (rejected — Constitution IV).

## R7. Test strategy (per user directive)

**Decision**: three tiers mirroring the repo convention —
- **unit** (`test_ppt_bridge.py`): path traversal rejection, SVG sanitization, subprocess timeout handling, error mapping table (every PptError → envelope).
- **integration** (`test_ppt_pipeline.py`): real script round-trips on temp projects — init creates the workspace, a fixture SVG passes check, export produces a real `.pptx` (opened with python-pptx to assert native text frames), failing SVG produces blocking errors, export refuses.
- **contract** (`test_ppt_contract.py`): the full matrix in `contracts/ppt-tools.md` — schema shapes for all five tools, every error path returns the envelope, tools/list grows 16 → 21 with existing entries unchanged, concurrent init isolation, same-conversation revision flow (rewrite page → re-export).

Docker-level and Dify-level flows are validated by `quickstart.md` manually (no network in CI paths, per constitution).

**Alternatives**: mocking the scripts everywhere (rejected — the bridge's whole job is invoking them; mocks would test the mock).

## R8. Config surface

**Decision**: new `[ppt]` section in config.toml: `scripts_root` (default `/opt/ppt-master/skills/ppt-master`), `projects_root` (default `/opt/ppt-master/projects`), `exports_url_base` (default `http://localhost:28080/exports`), `max_pages` (default 5), `script_timeout_s` (default 120), `retention_days` (default 0 = keep forever).

**Rationale**: all deployment paths stay operator-tunable without rebuilds; defaults match the sidecar mount plan; retention default "keep" honors the spec's minimum (exports survive the conversation) and defers cleanup policy to a later feature.
