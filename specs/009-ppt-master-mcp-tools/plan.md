# Implementation Plan: PPT-Master MCP Tools

**Branch**: `009-ppt-master-mcp-tools` | **Date**: 2026-10-18 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/009-ppt-master-mcp-tools/spec.md`

**Note**: User directive for this plan: original architecture plus explicit **test-case creation** and **error handling** as first-class deliverables.

## Summary

Expose ppt-master's pipeline as five additive MCP tools (`ppt_project_init`, `ppt_icon_sync`, `ppt_write_page`, `ppt_check`, `ppt_export`) on the existing AgenticRAG sidecar via a subprocess bridge to the ppt-master scripts; serve generated `.pptx` files over the sidecar's existing HTTP surface; and wire a Dify chatflow v2 with an intent-classifier router sending deck requests to a dedicated "PPT-Master" agent node driven by a distilled authoring rulebook. v1 targets quick-generation, ≤5 pages, same-conversation edits, pasted-text + agent-research inputs. Error handling follows the honest machine-readable envelope required by the spec (FR-010) and the constitution (IV); the contract test matrix is defined before implementation (II).

## Technical Context

**Language/Version**: Python 3.12 (sidecar `src/agentic_rag_mcp`), Bash/Docker for deployment, YAML for the Dify chatflow DSL.

**Primary Dependencies**: existing `mcp` FastMCP server; `subprocess` bridge to ppt-master scripts (their deps — python-pptx, PyMuPDF, Pillow, PyYAML, edge-tts, flask, etc. — baked into the sidecar image); no new Python packages inside `src/`.

**Storage**: filesystem only — ppt-master project workspaces under a configurable projects root; export artifacts under each project's `exports/`.

**Testing**: pytest in the existing three-tier layout (`tests/unit`, `tests/integration`, `tests/contract`). Full contract matrix specified in [contracts/ppt-tools.md](contracts/ppt-tools.md) before implementation (Constitution II).

**Target Platform**: Linux Docker sidecar (python:3.12-slim) + host Dify 1.17 chatflow.

**Project Type**: MCP server extension (library) + Dify chatflow DSL + agent prompt artifact.

**Performance Goals**: one-page deck prompt→download-link ≤ 5 min end-to-end (SC-001); each tool call ≤ 30 s except export (≤ 60 s).

**Constraints**: additive tool contracts only (Constitution I); ≤ 5 pages per run v1; same-conversation edits only; Dify agent node iteration limit raised to ≥ 30; exports unauthenticated on the local-trust network (matches existing `/healthz` posture).

**Scale/Scope**: single-user local deployment; concurrency handled by unique project directories (no locks needed).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Justification |
|-----------|--------|---------------|
| I. Contract Preservation | PASS | Five new `ppt_*` tools only; all 16 existing tool schemas untouched; existing contract test files run unchanged; new `test_ppt_contract.py` added alongside |
| II. Tests-First | PASS | Contract test matrix (including every error path) defined in `contracts/ppt-tools.md` before any implementation; unit/integration tests enumerated per module |
| III. Minimal Dependencies | PASS | No reimplementation — subprocess bridge reuses the ppt-master clone as-is; its pip deps enter only the sidecar image where they are actually required; no new runtime service (exports served by the existing HTTP wrapper) |
| IV. Honest Answers | PASS | Every tool returns a structured error envelope (code, message, remediation hint); no silent empty successes; export refuses on failing pages |
| V. Spec-Driven Replacement | N/A | New feature, nothing superseded |

## Project Structure

### Documentation (this feature)

```text
specs/009-ppt-master-mcp-tools/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── ppt-tools.md     # Phase 1 output — tool schemas, error envelope, test matrix
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/agentic_rag_mcp/
├── server.py                      # + 5 @mcp.tool() registrations delegating to ppt.bridge
├── config.py                      # + [ppt] section (scripts_root, projects_root, max_pages, retention_days)
└── ppt/
    ├── __init__.py
    ├── bridge.py                  # subprocess wrappers: init, icons, write, check, export
    └── errors.py                  # PptError hierarchy → honest error envelope

dify/docker/mcp-server/
├── Dockerfile                     # + ppt-master runtime deps
└── server.py                      # + GET /exports/<project>/<file> static route (http or starlette static)

dify/
├── Chatflow Basic (AgenticRAG Agent).yml   # v2: intent classifier → PPT-Master node (parallel branch)
└── ppt-master-rulebook.md                    # distilled quick-generate authoring instructions for the agent

tests/
├── unit/test_ppt_bridge.py        # path validation, SVG sanitization, error mapping
├── integration/test_ppt_pipeline.py # real script round-trip on temp projects
└── contract/test_ppt_contract.py   # tool schema + error envelope + full test matrix
```

**Structure Decision**: single-project layout — the feature extends the existing `src/agentic_rag_mcp` package with one new module (`ppt/`), matching how specialty search (005) and OneDrive (006/007) were added.

## Complexity Tracking

No violations to justify.
