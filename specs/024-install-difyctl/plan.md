# Implementation Plan: Install difyctl

**Branch**: `024-install-difyctl` | **Date**: 2026-10-26 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/024-install-difyctl/spec.md` (with the double-clarify round-trip-script adoption).

## Summary

Install the difyctl v1.18.0 CLI (binary + checksum gate + PATH), its agent
skill, complete the OAuth device-flow sign-in against the local console
(operator approves in browser), describe the AGI Assistant app read-only,
and adopt the operator's round-trip script into the repo with its three
defects fixed. Nothing in the Dify stack, the app, or the deploy
automation changes (FR-006).

## Technical Context

- **Language/Version**: host tooling — bash + curl + sha256sum + python3
  (all present); the adopted script is bash
- **Primary Dependencies**: none added — difyctl binary is a self-contained
  release artifact (85 MB), skill files are docs
- **Verified facts** (GitHub API, session-verified):
  binary URL `releases/download/1.18.0/difyctl-v1.18.0-linux-x64`;
  checksums file `difyctl-v1.18.0-checksums.txt`; workspace id
  `af91d497-36b4-4940-9045-3d7415546381` ("administrator's Workspace",
  DB-looked-up this session)
- **Touch points**: `~/.local/bin/difyctl` (new), `~/.bashrc` (one line,
  idempotent), `~/.config/kilo/skills/difyctl/` (new, CLI-generated),
  `dify/difyctl-export-reimport-publish.sh` (new repo copy of the
  operator's `~/Desktop` script, defects fixed)
- **Constraints**: checksum gate before the binary is ever executed;
  exact difyctl subcommand syntax verified via `difyctl help` before the
  script's first run (1.18.0's surface is server-discovered); the OAuth
  approval is a human browser step
- **Testing**: no pytest/vitest additions (no product code changes) — the
  runnable checks are `bash -n` for the script + the live V1–V7 battery
  (contracts/difyctl-install.md) against the real stack

## Constitution Check

- **I. Contract Preservation**: PASS — no MCP/tool/response changes; the
  round-trip script uses Dify's own console surface only.
- **II. Tests-First**: PASS — V1 (checksum) gates before the binary
  executes; the script gets `bash -n` before its supervised first run;
  the V-battery is defined before implementation.
- **III. Minimal Dependencies**: PASS — zero package installs; the
  binary and skill are upstream release artifacts.
- **IV. Honest Answers**: PASS — abort-on-mismatch checksum, named-step
  failure reporting in the adopted script, and the corrected
  "complementary-not-redundant" assessment recorded in the spec.
- **V. Spec-Driven Replacement**: PASS — additive only; no existing
  automation replaced; `deploy chatflow` remains the repo→server path.

No violations; Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/024-install-difyctl/
├── plan.md              # This file
├── research.md          # R1–R6 decisions + error handling
├── data-model.md        # Installed entities + script parameters
├── contracts/
│   └── difyctl-install.md  # V1–V7 check battery + error handling
├── quickstart.md        # Operator validation guide
├── checklists/
│   └── requirements.md  # (from /speckit.specify)
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Host + repo (repository root)

```text
~/.local/bin/difyctl                          # installed binary (checksum-verified)
~/.config/kilo/skills/difyctl/                 # CLI-generated skill
dify/difyctl-export-reimport-publish.sh        # adopted repo copy (3 defects fixed)
```

## Design

- **Install**: `curl -L` the verified URL → `sha256sum` against the
  official checksums file (abort on mismatch) → `chmod +x` → append
  `~/.local/bin` to PATH in `~/.bashrc` only if absent.
- **Skill**: `difyctl install skills ~/.config/kilo/skills` → verify
  SKILL.md + references/ exist.
- **Login**: `difyctl login --server http://localhost --no-browser
  --no-wait` → surface URL + device code → **operator approves in
  browser** → `difyctl login --resume` must print the account email.
- **Describe proof**: `difyctl help` first (confirm the describe verb),
  then describe `194e1edf-2eba-442c-b10b-231bebb79c37` → name
  "AGI Assistant".
- **Script adoption** (FR-007): copy `~/Desktop/difyctl-export-reimport-publish.sh`
  → `dify/difyctl-export-reimport-publish.sh` with: APP_ID default
  `194e1edf…`, WORKSPACE_ID default `af91d497-36b4-4940-9045-3d7415546381`,
  export prefix `agi_assistant_export_` (not clinic_chatbot), per-step
  reachable failure reporting (`|| { echo …; exit 1; }` style under
  `set -euo pipefail`), JSON shape-checks naming the failed step, the
  round-trip integrity check extended to name + webapp code, and
  `bash -n` clean.
- **Live syntax verification**: before the script's first run, confirm
  each verb (`export/import/publish/describe console_app`) exists in
  `difyctl help`; adjust call sites if the surface differs.

## Verification

1. `bash -n dify/difyctl-export-reimport-publish.sh` — syntax clean.
2. Live battery V1–V7 per `contracts/difyctl-install.md`: checksum
   match, version client+server 1.18.0, skill files present, resume
   prints email, describe shows AGI Assistant, supervised round-trip
   (id/name/code unchanged, fresh version id, export saved), stack
   unchanged before/after.
3. No pytest/vitest changes; the Python suite is untouched by design.
