# Tasks: Install difyctl

**Input**: Design documents from `/specs/024-install-difyctl/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/difyctl-install.md

**Tests**: No pytest/vitest additions (research R5 — no product code changes; a text-asserting test would be tautological). The acceptance instrument is the live battery V1–V7 from `contracts/difyctl-install.md`, run in order (battery order = safe order; V6 fires real export/publish calls, so it runs last, after V4/V5 pass).

**Organization**: Single user story (US1, P1) — install, sign in, describe, and adopt the round-trip script.

## Phase 1: Setup (Shared Infrastructure)

- [x] T001 Create spec artifacts per implementation plan (spec, plan, research, data-model, contracts/difyctl-install.md, quickstart, checklist)

## Phase 2: Foundational (Blocking Prerequisites)

None — host tooling install; the binary itself is the foundation and lands in Phase 3.

## Phase 3: User Story 1 - Install the Dify CLI, sign in, and adopt the round-trip script (Priority: P1) 🎯 MVP

**Goal**: difyctl v1.18.0 installed (checksum-gated), skill present, signed in, AGI Assistant described read-only, and the operator's round-trip script adopted into the repo with its three defects fixed — with zero stack/app impact.

**Independent Test**: battery V1–V7 green per `contracts/difyctl-install.md`.

### Implementation for User Story 1

- [x] T002 [US1] Download and verify the binary (V1): `curl -L` the binary from `https://github.com/langgenius/dify/releases/download/1.18.0/difyctl-v1.18.0-linux-x64` to `~/.local/bin/difyctl` plus the official `difyctl-v1.18.0-checksums.txt` to `/tmp/`; compare `sha256sum` against the checksums file's linux-x64 line — **abort (and delete the binary) on mismatch, before chmod**; then `chmod +x` and append `~/.local/bin` to PATH in `~/.bashrc` only if absent (idempotent)
- [x] T003 [US1] Version handshake (V2): run `difyctl version` — must report client 1.18.0 and server 1.18.0 edition COMMUNITY; any disagreement aborts the sequence before skill install
- [x] T004 [US1] Install the agent skill (V3): `difyctl install skills ~/.config/kilo/skills`, then verify `~/.config/kilo/skills/difyctl/SKILL.md` and `references/` exist
- [x] T005 [US1] OAuth device-flow login (V4) *(done: --insecure flag needed for http://localhost; OPENAPI_ENABLED=true env prerequisite discovered + applied; operator approved code 7UQV-HMXY; resume confirms administrator@tvb.com.hk)* — originally, surface the printed approval URL + device code to the operator, wait for the operator's browser approval, then verify `difyctl login --resume` prints the account email; code expiry → re-run the flow, denial → report without retry
- [x] T006 [US1] Read-only describe proof (V5): confirm the describe verb via `difyctl help`, then describe app `194e1edf-2eba-442c-b10b-231bebb79c37` and assert the name "AGI Assistant"
- [x] T007 [P] [US1] Adopt the round-trip script (FR-007) *(json_get eval-quote + stdout-swallow bugs found and fixed during T009): copy `~/Desktop/difyctl-export-reimport-publish.sh` to `dify/difyctl-export-reimport-publish.sh` in the repo with its three defects fixed — defaults corrected to APP_ID `194e1edf-2eba-442c-b10b-231bebb79c37` and WORKSPACE_ID `af91d497-36b4-4940-9045-3d7415546381`, export filename prefix changed from `clinic_chatbot_export_` to `agi_assistant_export_`, per-step failure reporting made reachable (`|| { echo …; exit 1; }` under `set -euo pipefail`), JSON shape-checks that name the failed step, and the round-trip integrity check extended from app-id-only to id + name + webapp code; `bash -n` must pass
- [x] T008 [US1] Live syntax verification (FR-007/R4): run `difyctl help` and the per-verb help to confirm `export/import/publish/describe console_app` and their flags exist on this server's discovered surface; adapt the script's call sites to the discovered syntax if any verb or JSON shape differs
- [x] T009 [US1] Supervised round-trip run (V6): one run of `dify/difyctl-export-reimport-publish.sh` against AGI Assistant — ends with an export file saved as `~/Downloads/agi_assistant_export_*.yml`, a fresh published version id, and app id / name "AGI Assistant" / webapp code `GwEO6abLduqWHObS` all unchanged, no error output

## Phase 4: Polish & Cross-Cutting Concerns

- [x] T010 Zero stack impact (V7/SC-005): compare `docker ps` container set and statuses before/after the whole feature, and the app row (id, name, sites code) in the Dify DB — must be identical; the published version id advancing (from T009) is the only permitted change
- [x] T011 Commit spec artifacts + the adopted script `dify/difyctl-export-reimport-publish.sh` together (binary, skill, and token are host-side, not repo artifacts) *(commit `8342d5d`, pushed)*

## Phase 5: Convergence

- [x] T012 Document the difyctl prerequisite in the runbook (done — DEPLOY.md Step 10 + deploy skill, in sync): `OPENAPI_ENABLED=true` (Dify 1.18.0 Community defaults it to false; without it the whole `/openapi/v1/*` group including the OAuth device flow 404s) — add to DEPLOY.md (Step 10 area / difyctl notes) and sync the deploy skill's Step 10, so a fresh-host operator doesn't hit the same silent 404 (FR-004, plan: Design) (missing)

## Dependencies & Execution Order

- T001 → all
- T002 → T003 → T004 → T005 → T006 (each step gates the next: binary → handshake → skill → login → describe)
- T007 is independent of T002–T006 (different file, no tooling dependency) — [P], can land any time after T001
- T008 after T003 (needs the binary; runs best after T005 in case help requires auth)
- T009 after T005 + T007 + T008 (login + corrected script + verified syntax)
- T010 after T009 → T011 last

### Parallel Opportunities

- T007 (script adoption) runs parallel to T002–T006
- The install sequence T002→T006 is strictly sequential (each gates the next)

### Parallel Example: User Story 1

```text
Task: "Adopt the round-trip script to dify/difyctl-export-reimport-publish.sh (T007)"
Task: "Install binary + checksum gate + PATH (T002)"
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. T001 → T002 (checksum-gated install) → T003 (handshake) → T004 (skill) → T005 (device-flow login, operator approves) → T006 (describe proof)
2. T007 (script adoption) parallel any time; T008 (syntax verify) then T009 (supervised run)
3. Polish: T010 zero-impact check, T011 commit

US1 is the entire feature; delivery = a signed-in difyctl with the adopted round-trip script, verified by V1–V7 with zero stack impact.
