# Tasks: Dedicated Documents Mount

**Input**: Design documents from `/specs/023-documents-mount/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/mount-checks.md

**Tests**: Unit tests ARE required for the deploy-CLI change (constitution II — the run-command string is the FR-004 artifact; V1 asserts it before any live step). Live battery V1–V6 per `contracts/mount-checks.md`.

**Organization**: Single user story (US1, P1) — the documents mount, end to end.

## Phase 1: Setup (Shared Infrastructure)

- [x] T001 Create spec artifacts per implementation plan (spec, plan, research, data-model, contracts/mount-checks.md, quickstart, checklist)

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: the container-spec change + its unit tests — everything live depends on this.

- [x] T002 [US1] In `src/agentic_rag_mcp/deploy/docker_ops.py`: add `("~/agentic-rag-docs", "/data/rag-docs")` to `MOUNTS`, and refactor `recreate_container()` to build ALL `-v` flags from one list (move the ppt-master mount into the loop — today three flags are hand-built; end state: `MOUNTS` + the REPO_ROOT ppt-master pair drive the loop), plus `mkdir -p` (expanduser) on the documents host path before `docker run`
- [x] T003 [US1] Write `tests/unit/test_deploy_docker_ops.py`: with the subprocess runner mocked, assert (a) the run command contains the documents `-v <expanded home>/agentic-rag-docs:/data/rag-docs` flag, (b) the existing config/huggingface/ppt-master flags are still present, (c) `mkdir -p` runs before `docker run`. RED first against the unmodified `docker_ops.py`, then green after T002. Also run the existing deploy tests (`tests/unit/test_deploy_cli.py`, `tests/contract/test_deploy_cli.py`) — all green

## Phase 3: User Story 1 - The documents mount, live (Priority: P1) 🎯 MVP

**Goal**: the running sidecar carries the mount; the PDF lives in the honest folder; the source list points at `/data/rag-docs`; the index counts prove ingestion; the runbook documents it all.

**Independent Test**: battery V2–V6 green.

### Implementation for User Story 1

- [x] T004 [US1] Recreate the sidecar via the deploy tooling (brief downtime): `deploy redeploy` (build is cached; recreate → health → 23-tool re-sync), then V2 mount round-trip — write a probe file into `~/agentic-rag-docs/`, `docker exec agentic-rag ls /data/rag-docs` shows it
- [x] T005 [US1] Migrate the document: move `reset password.pdf` from `/kilocode/AGIAssistant/ppt-master/rag-docs/` to `~/agentic-rag-docs/`; `sources_remove` the old `rag-docs` source (`eb24d56c2270`); `sources_add {"type":"local_folder","config":{"path":"/data/rag-docs"}}` → expect `added: 1, skipped: []`; delete the old empty host folder; V3+V4: `sources_list` shows only the new source, `status` shows documents ≥ 1 chunks ≥ 1
- [x] T006 [US1] V5 durability: re-run `deploy redeploy` a second time and repeat the mount round-trip — the mount survives because the tooling owns it; `status` index counts unchanged
- [x] T007 [P] [US1] V6 runbook documentation: update `DEPLOY.md` Step 6 (Ingest sources) — the `~/agentic-rag-docs/` folder (host path, container path, supported types table, ≤5-min auto-sync, one-time registration) — and sync the identical section into the deploy skill at `~/.config/kilo/skills/agenticrag-deploy/SKILL.md`

## Phase 4: Polish & Cross-Cutting Concerns

- [x] T008 Run the Python suite: `.venv/bin/python -m pytest tests/ -q` — all green (including the new unit tests); frontend gates untouched by this feature
- [x] T009 Boundary check: `git diff --name-only` limited to `src/agentic_rag_mcp/deploy/docker_ops.py`, `tests/unit/test_deploy_docker_ops.py` (new), `DEPLOY.md`, and `specs/023-documents-mount/` — no other code touched
- [x] T010 Commit spec artifacts + diff together *(committed and pushed)*

## Phase 5: Convergence

- [x] T011 Add the documents mount to both manual-recreation examples (done — both Step 3 `docker run` blocks now carry `-v ~/agentic-rag-docs:/data/rag-docs`): DEPLOY.md Step 3 (~line 56) and the deploy skill's Step 3 `docker run` blocks list only the three pre-023 `-v` flags — add `-v ~/agentic-rag-docs:/data/rag-docs \` to both so the runbook's manual path no longer silently drops the mount (FR-006, spec Edge Cases) (partial)

## Dependencies & Execution Order

- T001 → all; T002 → T003 (RED first, then green) → T004 → T005 → T006 → T008 → T009 → T010
- T007 is independent of T004–T006 (docs only) — [P], lands any time after T002

### Parallel Opportunities

- T007 (runbook docs) runs parallel to the live tasks T004–T006
- T003's RED/GREEN must precede T004 — the unit test is the mount's regression guard

### Parallel Example: User Story 1

```text
Task: "Recreate the sidecar and verify the mount round-trip (V2)"
Task: "Document the documents folder in DEPLOY.md Step 6 + the deploy skill (V6)"
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. T001 → T002/T003 (code + RED→GREEN unit tests) → T004 (recreate + round-trip) → T005 (migration + swap) → T006 (durability) → T007 (docs)
2. Polish: full Python suite, boundary, commit

US1 is the entire feature; delivery = the tooling-owned mount with the migrated document, verified by V1–V6.
