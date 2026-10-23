# Implementation Plan: Dedicated Documents Mount

**Branch**: `023-documents-mount` | **Date**: 2026-10-23 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/023-documents-mount/spec.md`

## Summary

Add a dedicated documents volume to the deploy tooling's container spec:
host `~/agentic-rag-docs/` (created by the tooling if absent) ⇄ container
`/data/rag-docs`. Recreate the running sidecar with the new mount,
migrate `reset password.pdf` from the ppt-master tree, swap the source
registration, verify ingestion end-to-end, and document the folder in
the runbook (DEPLOY.md Step 6 + deploy skill, FR-006).

## Technical Context

- **Language/Version**: Python 3.12 (deploy CLI, editable pipx install — code changes take effect without reinstall)
- **Primary Dependencies**: none added — docker CLI via subprocess (existing)
- **Touch point (verified)**: `src/agentic_rag_mcp/deploy/docker_ops.py` —
  the `MOUNTS` list (lines 15–18) and `recreate_container()` (lines 40–54)
  are the single source of truth for the container's volumes. Adding one
  `(host, container)` pair to `MOUNTS` + one `-v` flag construction makes
  every future `redeploy`/`all` carry the mount (FR-004).
- **Testing**: deploy-CLI unit tests exist
  (`tests/unit/test_deploy_*.py`); the acceptance instrument is the live
  verification battery in `contracts/mount-checks.md`
- **Constraints**: brief downtime (~1 min) during recreate is accepted;
  the recreate must keep the SSRF network connect + health gate sequence
  unchanged (FR-005)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Contract Preservation**: PASS — the 23-tool MCP surface is
  untouched; the mount is additive deployment plumbing.
- **II. Tests-First**: PASS — the deploy-CLI unit tests are extended for
  the new mount (asserting the `-v` flag appears in the run command
  before the container is recreated), plus the live verification battery.
- **III. Minimal Dependencies**: PASS — zero (existing docker
  subprocess path).
- **IV. Honest Answers**: PASS — mount visibility verified in BOTH
  directions before declaring success; a failed recreate aborts (the
  deploy CLI's existing fail-fast), never half-applied.
- **V. Spec-Driven Replacement**: PASS — the misleading
  `ppt-master/rag-docs` source and folder are removed after migration
  (no dead source).

No violations; Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/023-documents-mount/
├── plan.md              # This file
├── research.md          # R1–R3 decisions + error handling
├── data-model.md        # The volume mapping entity
├── contracts/
│   └── mount-checks.md  # V1–V6 verification battery + error handling
├── quickstart.md        # Operator validation guide
├── checklists/
│   └── requirements.md  # (from /speckit.specify)
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
src/agentic_rag_mcp/deploy/docker_ops.py   # MOUNTS += documents pair; recreate -v flag; mkdir -p host folder
tests/unit/test_deploy_docker_ops.py       # (new) run-command includes the documents -v flag; folder created
DEPLOY.md                                   # Step 6: documents folder documented
~/.config/kilo/skills/agenticrag-deploy/SKILL.md  # Step 6 synced with DEPLOY.md
```

## Design

- **MOUNTS list** gains `("~/agentic-rag-docs", "/data/rag-docs")`;
  `recreate_container()` constructs the `-v` from the same list (extend
  the existing loop instead of a fourth hand-built `-v` — refactor the
  three existing hand-built flags into the MOUNTS-driven loop so there
  is exactly one list to keep in sync).
- **Host folder creation**: `recreate_container()` runs
  `mkdir -p ~/agentic-rag-docs` (expanduser) before `docker run` —
  Docker's auto-create would chown it root, which would still work but
  is wrong ownership for a user-managed folder.
- **Recreate sequence** (unchanged otherwise): rm -f → run → connect
  ssrf network → health gate (the CLI's existing flow).
- **Migration**: stop nothing; move the PDF host-side
  (`ppt-master/rag-docs/` → `~/agentic-rag-docs/`), `sources_remove`
  the old source, `sources_add` `/data/rag-docs` (auto-syncs), delete
  the old empty folder.

## Verification

1. Unit: `pnpm`-equivalent gates for Python — `pytest tests/unit/test_deploy_*.py` green with the new mount assertions.
2. Live battery V1–V6 per `contracts/mount-checks.md`: mount round-trip
   (host write → container read; container-registered source syncs),
   migration + index counts (documents ≥ 1, chunks ≥ 1, old source gone),
   mount present in a second CLI-driven recreate, health green
   throughout, runbook documents the folder.
