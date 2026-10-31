# Implementation Plan: Hermes Agent Lane — Windows File Tasks via Local Agent

**Branch**: `028-hermes-mcp-lane` | **Date**: 2026-10-31 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/028-hermes-mcp-lane/spec.md` (+ two clarify passes, 5 locked decisions)

## Summary

Add Hermes as a third agent lane in the AGI Assistant chatflow: prompts classified as local file tasks route to a Hermes agent node whose tool — a new sidecar MCP tool `hermes_file_task` — gates every operation inside an allowed root on the Windows disk (`C:\temp` via `/mnt/c/temp`), executes via the Hermes gateway's Responses-API server, and writes an append-only audit log on the host. The gate lives in the sidecar (tested Python, one audit writer, the only path to the disk).

## Technical Context

**Language/Version**: sidecar Python 3.12 (existing `src/agentic_rag_mcp/`); chatflow DSL (Dify 1.18, agent nodes); no frontend changes.

**Primary Dependencies**: Hermes gateway API server (verified from the installed checkout, `gateway/platforms/api_server.py`): `POST /v1/responses` (OpenAI Responses-compatible: `input`, `instructions`, `store`, `session_id`, `conversation`, `previous_response_id`), `GET /v1/models` (advertises `hermes-agent` by default), bearer-key gated (`API_SERVER_KEY`), default port **8642**, default bind 127.0.0.1 (configurable via `API_SERVER_HOST`), concurrency-capped with per-run persistence in the response store. NO new pip packages; `httpx` already in use.

**Storage**: host filesystem — target root `/mnt/c/temp` (Windows `C:\temp`); audit log = append-only JSONL on the host (sidecar-writable path from config, default `~/.hermes-mcp/audit.jsonl` — under the config home, NOT a gitignored-hidden-dir source root; see R5).

**Testing**: pytest (pure gate module + audit writer, failing-first), deploy battery scenario (E2E create + block + audit), CDP regression for classifier routing, `deploy chatflow` publish flow.

**Target Platform**: sidecar container `agentic-rag` (port 28080, in the Dify MCP allowlist); Hermes gateway runs on the host as the user.

**Performance Goals**: E2E file task < 60 s (SC-001); Hermes call timeout 300 s; 100% block-matrix containment (SC-002).

**Constraints**: Constitution I — additive tool + new node; existing nodes/tools byte-identical in behavior. Constitution II — gate module tests-first. Constitution III — zero new packages. Constitution IV — honest envelopes (blocked/failed verdicts never fabricated). Constitution V — documented deviations only (gate architecture, see R2). Sidecar changes ship via `docker cp` hot-patch + source (image rebuild remains pending from earlier specs).

**Scale/Scope**: single-user; single in-flight generation (chatflow is single-flight per spec 027); Hermes concurrency cap respected.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Verdict | Notes |
|---|---|---|
| I. Contract Preservation | PASS | One additive MCP tool (`hermes_file_task`); existing 23 tools byte-identical; chatflow gains a third classifier class + one agent node — existing branches untouched; stream/stop contracts (specs 013/027) unaffected. |
| II. Tests-First | PASS | `src/agentic_rag_mcp/hermes_gate.py` is a pure module — failing-first pytest for normalization, verdicts, op-set, audit; battery scenario written with the tasks. |
| III. Minimal Dependencies | PASS | Zero new packages: `httpx` (present), Hermes' own API server (already installed and running on this host). No Dify marketplace plugin, no custom-tool registration, no compose edits. |
| IV. Honest Answers | PASS | Blocked verdicts returned in the established honest-envelope pattern with reason + active root; Hermes unreachable → honest failure + recovery hint (FR-010); audit log records truth (FR-012/013). |
| V. Spec-Driven Replacement | PASS | Deviation from the user's tutorial design (Dify code-node gate) is recorded here and in research R2: the gate moves into the sidecar tool — same security outcome, single tested implementation, one audit writer. No code is deleted; nothing else changes. |

Post-Phase-1 re-check: design adds one pure module, one tool, config fields, DSL additions — still PASS on all five.

## Project Structure

### Documentation (this feature)

```text
specs/028-hermes-mcp-lane/
├── plan.md                      # This file
├── research.md                  # Phase 0 output (R1-R8)
├── data-model.md                # Phase 1 output
├── quickstart.md                # Phase 1 output (validation guide + test matrix)
├── contracts/
│   └── hermes-file-task.md      # MCP tool contract + gate/audit invariants
└── tasks.md                     # Phase 2 (/speckit.tasks — NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/agentic_rag_mcp/
├── hermes_gate.py               # NEW: pure path-normalization + containment + op-set verdicts
├── hermes_client.py             # NEW: thin /v1/responses client (stateless, 300 s timeout)
├── hermes_audit.py              # NEW: append-only JSONL audit writer
├── config.py                    # MODIFIED: hermes_api_url/key/timeout, allowed_root default, audit_path
└── server.py                    # MODIFIED: hermes_file_task MCP tool (honest envelopes)

dify/AGIAssistant/AGI_Assistant.yml  # MODIFIED: 3rd classifier class, Hermes agent node, tool wiring
src/agentic_rag_mcp/deploy/battery.py # MODIFIED: hermes-file-task scenario
tests/unit/test_hermes_gate.py       # NEW: failing-first gate suite
tests/unit/test_hermes_audit.py      # NEW: audit writer suite
```

**Structure Decision**: single-project; the gate is one pure module consumed by the tool wrapper — no new packages, no Dify-side code (the tutorial's Dify code-node sanitizer is replaced by this module; see research R2).
