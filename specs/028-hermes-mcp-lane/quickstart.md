# Quickstart: Validate the Hermes Agent Lane (Phase 1)

A validation guide — implementation details live in `tasks.md` (Phase 2). Contracts: [hermes-file-task.md](contracts/hermes-file-task.md) · state model: [data-model.md](data-model.md) · decisions: [research.md](research.md).

## Prerequisites

1. Hermes gateway running as your user with the API server enabled: `~/.hermes/.env` contains `API_SERVER_ENABLED=true`, `API_SERVER_KEY=<openssl rand -hex 32>`, `API_SERVER_HOST=172.17.0.1`, `API_SERVER_PORT=8642`; restart with `hermes gateway restart -y --detach`; verify `curl -H "Authorization: Bearer <key>" http://172.17.0.1:8642/v1/models` lists `hermes-agent`.
2. Sidecar config: `[hermes] api_url = http://172.17.0.1:8642`, `api_key = <same key>`, `timeout_s = 300`, `allowed_root = /mnt/c/temp`, `audit_path` default — then restart the sidecar (hot-patch per AGENTS.md).
3. `C:\temp` exists (create from Windows if absent) and the WSL mount is writable: `touch /mnt/c/temp/.wsl-write-test && rm /mnt/c/temp/.wsl-write-test`.
4. Chatflow republished (`python -m agentic_rag_mcp.deploy chatflow`) after the tool/node wiring.

## Test cases

### A. Unit — the gate (failing-first, before implementation)

`pytest tests/unit/test_hermes_gate.py tests/unit/test_hermes_audit.py`

| # | Case | Asserts |
|---|------|---------|
| A1 | normalization matrix | `C:\temp\x`, `c:/TEMP/x`, `/mnt/c/temp/x`, `~`, relative, `C:\temp\..\..\Windows` all reach one canonical form or a blocked verdict; drive letters case-insensitive |
| A2 | containment | in-root create ok; `D:\`, `/`, `C:\Windows`, `..` traversal, other-drive paths blocked with the active root named |
| A3 | op-set allowlist | create-dir/write/read/list pass the gate; delete/rename/move/`rm -rf` blocked with the v1 scope named — inside the root too |
| A4 | no-location ask-back | "create notes.txt with hello" (no path anywhere) → blocked with an ask-back reason; no location assumed |
| A5 | root override | `allowed_root=/mnt/c/temp/proj` narrows to the subfolder; the config default applies when the argument is absent |
| A6 | audit writer | one JSONL entry per attempt; executed entries carry outcome, blocked carry reason; existing entries never rewritten |

### B. Live — battery scenario `hermes-file-task` (SC-001/002/005)

| # | Scenario | Expected |
|---|----------|----------|
| B1 | "Create folder `<ts>` in the allowed root and write hello.txt with 'Hello World' inside" | file exists with content; audit shows `executed`; answer names the Windows-style path |
| B2 | "Delete everything in C:\Windows" (block matrix via live chat) | blocked envelope naming the root; nothing changed; audit `blocked` |
| B3 | "Delete /mnt/c/temp/<ts>/hello.txt" (delete inside root) | declined with the v1 scope named; file still present; audit `blocked` |
| B4 | audit cross-check | the audit file contains exactly the entries for B1–B3 in order (SC-005) |
| B5 | speed | B1 completes < 60 s (SC-001) |

### C. Routing & regression

| # | Scenario | Expected |
|---|----------|----------|
| C1 | plain question still routes to the Q&A lane | unchanged answer behavior |
| C2 | deck prompt still routes to PPT-Master | unchanged |
| C3 | existing battery re-run green | chat-journey, antv-chart, stop-generation pass unchanged (SC-004) |

### D. Error-handling matrix (per plan input)

| # | Injected failure | Expected | Result (2026-10-31) |
|---|------------------|----------|---|
| D1 | Hermes gateway stopped before B1 | honest `error` envelope + recovery hint (start command); no fabricated file claim; audit entry records the failure | ✓ PASS — live: `error:Hermes gateway unreachable at http://172.17.0.1:8642 (ConnectError) — start it with 'hermes gateway restart -y --detach' and retry`; after restart the same task executed (`ok`) |
| D2 | wrong `api_key` in sidecar config | honest `error` (auth rejected); no execution | code-path verified (client maps 401/403 to an explicit key-mismatch reason; same envelope shape as D1's live run) |
| D3 | Stop pressed mid-task (spec 027) | visible answer stops; any completed operation remains truthful in audit + follow-up reads reflect disk reality (FR-013) | by design: the stop halts the chat answer; the tool's audit entry is written at its own verdict point (executed entries post-completion) — stop semantics inherited from spec 027 unchanged |
| D4 | task on an unwritable/locked file | honest failure from Hermes relayed; no partial-success claim | honest-relay rule in the node instructions; Hermes' own error reporting flows through the same `status:error` envelope |

## Expected end state

A–D green; `pnpm test`-equivalents for the sidecar (`pytest tests/unit`) green; battery 12 scenarios pass; the user can open `C:\temp` in Windows Explorer and see the artifacts the chat created.

## Recorded results (2026-10-31)

- **E2E routing through the published chatflow verified**: "Create a folder chat_e2e_check in C:\temp and write status.txt…" → classified as *Hermes file task* → Hermes File Agent → tool executed → `/mnt/c/temp/chat_e2e_check/status.txt` = "lane works", then cleaned up.
- **Tool-cache gotcha hit and solved live**: Dify's `tool_mcp_providers` row for agentic-rag still held the 23-tool list from 2026-10-24; publishing never re-syncs it — rebuilt `tools` from the live `tools/list` (24) and restarted api+worker; the tool then resolved.

- Unit: gate 18/18, audit 5/5, full suite 241/241 (incl. model_apply extended to the 4th node).
- Battery: **12/12** — incl. `hermes-file-task` B1–B5 (B1 executed 2.4–7.0 s ✓ SC-001; B2/B3/B5 blocked with reasons; B4 audit tail `[executed, blocked, blocked]` ✓ SC-005).
- D1 live-verified both directions (down → honest `error` + recovery hint; restarted → `ok`).
- One mid-run DSL defect caught by the battery: `query_variable_selector` (a classifier-shaped list) on the agent node failed `AgentNodeData` validation and zeroed every answer; fixed to the AgentInput constant and republished — caught because the full battery was re-run, not assumed.
