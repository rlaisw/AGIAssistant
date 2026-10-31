# Research: Hermes Agent Lane (Phase 0)

**Date**: 2026-10-31 · All stack facts verified live from the installed Hermes checkout (`~/.hermes/hermes-agent/`) and this host unless noted.

## R1 — Hermes API server surface (verified)

- **Decision**: call `POST /v1/responses` on the gateway's API server with `input` (the gated task), `instructions` (containment system prompt), `store=false`, no `conversation`/`previous_response_id` chaining; optional `model="hermes-agent"`.
- **Evidence**: `gateway/platforms/api_server.py` registers `("POST", "/v1/responses", ...)`, `GET /v1/models`, `POST /v1/chat/completions`, `/api/sessions/*`; the responses handler accepts `input, instructions, previous_response_id, conversation, conversation_history, model, store, session_id` (`gateway/platforms/api_server_openai_routes.py:93`). Auth is the `API_SERVER_KEY` bearer (config key strength-checked at `gateway/config.py:545`). Default port 8642 (`hermes_cli/config_defaults.py:3115`); default bind 127.0.0.1, settable via `API_SERVER_HOST` (3117); model advertised on `/v1/models` defaults to the profile name or `"hermes-agent"` (api_server.py:1387). Concurrency-capped across agent-serving endpoints.
- **Alternatives considered**: `/api/sessions/{id}/chat` (session-oriented — more state than needed); `/v1/chat/completions` (OpenAI-completions shape; Responses shape carries `instructions` cleanly for the containment prompt).

## R2 — Architecture: sidecar MCP tool vs. the tutorial's Dify code-node gate

- **Decision**: implement the lane as a **sidecar MCP tool** (`hermes_file_task`) + a third classifier class + a Hermes agent node in the chatflow. The gate (normalize → containment → op-set → audit) lives in the sidecar. **No Dify code node, no IF node, no marketplace plugin, no compose edits.**
- **Rationale**: this repo already has the exact plumbing — 23 MCP tools wired via `agentic-rag:28080` with the established `tool_description` → DSL sync → `deploy chatflow` pipeline. A sidecar gate gives: (a) the sanitizer as **tested pure Python** (Constitution II — a Dify code node is untestable by our pytest battery); (b) **one audit writer on the host** (FR-012 requires an append-only host log — a Dify code node cannot write host files); (c) defense that cannot be routed around — the tool is the **only** path to the disk, so the gate sees every attempted operation; (d) zero new moving parts in Dify.
- **Security-equivalence to the user's design**: the tutorial's code-node gate ran *before* the agent to save tokens and stop injection pre-reasoning. Here the gate runs at the tool boundary: a smuggled instruction can make the Dify agent *say* things, but no disk operation can occur outside the gate — the containment outcome is identical (FR-004's "before any agent processing" is satisfied at the local-agent boundary: nothing reaches Hermes ungated). Token cost: a blocked call costs one short agent turn — accepted. If pre-agent deflection is ever wanted, the same tested module can be embedded into a Dify code node later (the module is the single source of truth).
- **Alternatives considered**: Dify marketplace plugin "Hermes Agent Chat" (adds a Dify→Hermes hop outside our pipeline; audit/gate logic would live untested in plugin config; marketplace availability unverified from CLI); Dify custom tool with OpenAPI schema (same gaps); user's original code-node design (untestable gate, no host audit path for blocked ops).

## R3 — Networking: who talks to Hermes

- **Decision**: only the sidecar calls Hermes — `http://172.17.0.1:8642` (the proven docker0-gateway pattern this stack already uses for Ollama at `172.17.0.1:11434`). Hermes `API_SERVER_HOST` binds `172.17.0.1` (tighter than the tutorial's 0.0.0.0: reachable from any container network, NOT from the Windows host or LAN).
- **Rationale**: Dify never talks to Hermes directly (removing the need for `extra_hosts: host-gateway`, custom tools, and marketplace plugins entirely); the sidecar is the single trusted caller; binding to the bridge IP means Windows/WSL-side exposure is nil and the API key is the second boundary.
- **Alternatives considered**: `API_SERVER_HOST=0.0.0.0` + `host.docker.internal` (tutorial; works but exposes the port to the Windows host/LAN under WSL2's port-forwarding); binding 127.0.0.1 (containers can't reach).

## R4 — Per-conversation isolation (FR-007)

- **Decision**: stateless Hermes calls — `store=false`, no `conversation`/`previous_response_id`. Each tool call is a fresh execution; the Dify agent carries the conversational context in its own prompt and supplies the complete task each time.
- **Rationale**: statelessness trivially satisfies FR-007 (no cross-conversation state can leak because no state persists at all) and matches the tool-call model: the Dify agent's history is the conversation memory; Hermes is a stateless executor. Hermes' own `/api/sessions` continuity can be added later behind the same tool if ever needed.
- **Alternatives considered**: `session_id`/`conversation` chaining keyed per Dify conversation (adds state surface, needs the conversation id inside tool args, no v1 value).

## R5 — Audit log (FR-012/013)

- **Decision**: append-only JSONL on the host, written by the sidecar tool at the single verdict point — every attempt gets one entry: `{ts, decision: executed|blocked, reason?, normalized_path, operation, allowed_root, session_hint}`. Default path from config (`~/.hermes-mcp/audit.jsonl` — created on first write; the directory is the config home, not a source root, so the hidden-dir filter in `sources/local_folder.py` does not apply — but the audit file is user data, never ingested; if it ever lands inside a watched source root, it is excluded by gitignore rules). The lane never rewrites or prunes the log (FR-012).
- **Rationale**: one writer (the tool), one verdict per attempt, host-side persistence; executed outcomes recorded post-completion (FR-013's stop-truth); blocked attempts recorded with reason — the battery asserts both directions (SC-005).
- **Alternatives considered**: Hermes' built-in response store (covers executed calls only — blocked attempts never reach Hermes); Dify conversation records (not host-side, not append-only by contract).

## R6 — Operation set & gate rules (FR-011, FR-002/004)

- **Decision**: the gate (pure module) does, in order: (1) normalize every path in the task text — Windows drive style (`C:\temp\x`, `c:/TEMP/x`) → `/mnt/c/temp/x`, mixed separators, `~` expansion, relative→root-anchored, dedup `//`, strip trailing separators; (2) resolve `..` segments; (3) containment check against the active `allowed_root` (request arg → config default `/mnt/c/temp`); (4) operation-set check: create/mkdir, write, read, list allowed; delete/rename/move/bulk declined everywhere (FR-011); (5) no-location tasks are declined by the tool with an ask-back message (FR-014 — the agent relays the ask-back; the gate never assumes a location).
- **Rationale**: user-locked decisions (clarify passes 1 & 2) + the tutorial's sanitizer hardened; pure functions → full pytest matrix (normalization × verdicts × op-set).
- **Alternatives considered**: verb-blocklist instead of op-set allowlist (weaker — inverted security); regex-only strip of `..` without resolution (bypassable via encoded/interleaved variants — full normalization + resolution chosen).

## R7 — Chatflow routing (FR-001)

- **Decision**: `intent_router` (question-classifier) gains a third class — file/local-task; a new **Hermes Agent** node (function-calling strategy, existing cloud model, `hermes_file_task` tool) handles that branch; answers merge into the existing answer nodes. Tool `tool_description` sync + `deploy chatflow` via the established pipeline. Classifier prompt updated to name the new class with examples.
- **Rationale**: exactly how agentic_strategy/ppt_master lanes are wired today; no new node types.
- **Alternatives considered**: adding the tool to the existing agentic_strategy nodes (muddies the Q&A lane's tool list and routing tests); a separate app (breaks the single-assistant UX the user chose).

## R8 — Test strategy (per plan input "create test cases and add error handling")

- **Unit (failing-first)**: `tests/unit/test_hermes_gate.py` — normalization matrix (Windows/WSL/mixed/case/trailing/`~`/relative), containment matrix (in-root ok; other drives, `/`, `C:\Windows`, traversal → blocked), op-set matrix (create/write/read/list ok; delete/rename/bulk/`rm -rf` declined), no-location ask-back, reason strings. `tests/unit/test_hermes_audit.py` — append-only, blocked/executed shapes, never-pruned.
- **Live**: battery scenario `hermes-file-task`: (a) create `~/…/test_root/<ts>/hello.txt` with content → assert file exists + audit executed entry; (b) out-of-root prompt → blocked envelope + no side effects + audit blocked entry; (c) delete-in-root prompt → declined with scope named; (d) audit log has exactly the expected entries (SC-005).
- **Error handling (battery-visible)**: Hermes down → honest 503-style envelope + recovery hint (FR-010); key rejected → honest failure; timeout (300 s) → honest failure. Classifier regression: existing QA/deck routing unchanged (chat-journey + antv scenarios re-run green).
