# Research: Install difyctl

## R1 — Install to `~/.local/bin`, PATH via idempotent `.bashrc` append

- **Decision**: binary at `~/.local/bin/difyctl`; append
  `export PATH="$HOME/.local/bin:$PATH"` to `~/.bashrc` only if the dir
  is not already on PATH.
- **Rationale**: XDG user convention; no root required; the CLI survives
  WSL restarts alongside the user's other tools.
- **Alternatives considered**: `/usr/local/bin` (needs sudo, mixes
  user tooling with system), pip install (difyctl ships as a release
  binary, not a package).

## R2 — Checksum gate before the binary ever executes

- **Decision**: download binary + the official
  `difyctl-v1.18.0-checksums.txt`, compare `sha256sum` for the linux-x64
  entry; abort on mismatch or missing entry. Only then `chmod +x`.
- **Rationale**: an 85 MB self-contained binary from the internet is a
  trust boundary; the official checksums file is the canonical source
  (cross-checked against the API-published digest
  `2ab8eafb3c6870272fef0c9d1faea99181500905091a6c7b38e4e5c9822eb99b`).
- **Alternatives considered**: trust TLS alone — rejected (release-artifact
  tampering is exactly what checksums exist for).

## R3 — Repo adoption of the round-trip script at `dify/`

- **Decision**: reviewed copy at `dify/difyctl-export-reimport-publish.sh`
  with defaults `APP_ID=194e1edf-2eba-442c-b10b-231bebb79c37`,
  `WORKSPACE_ID=af91d497-36b4-4940-9045-3d7415546381` (DB-verified this
  session), export prefix `agi_assistant_export_`.
- **Rationale**: `dify/` is the repo's Dify-artifact home (DEPLOY.md
  references it); `~/Desktop` is volatile and outside version control;
  the foreign "clinic_chatbot" defaults would silently target a
  nonexistent app.
- **Alternatives considered**: run in place from Desktop (volatile,
  uncorrected, unreviewed); rewrite in Python (the script is fine once
  its three defects are fixed — don't rewrite working tooling).

## R4 — Live syntax verification before the script's first run

- **Decision**: run `difyctl help` (and per-verb help) to confirm
  `export/import/publish/describe console_app` and their flags exist
  on this server's discovered surface; adjust the script's call sites
  to the discovered syntax before running it.
- **Rationale**: 1.18.0 publishes a server operation catalog and
  replaced the old `/openapi/v1` route; the script's assumed syntax
  (from a foreign deployment) is a guess until verified.
- **Alternatives considered**: run the script and see — rejected (the
  first failing step would fire real export/publish requests against
  the production app).

## R5 — No unit tests; `bash -n` + supervised live run

- **Decision**: the adopted script gets `bash -n` (static) and a
  supervised first run (V6) against the real app; no pytest/vitest
  additions.
- **Rationale**: the feature adds no product code; the script's
  correctness is only observable against the real Dify server. A
  pytest asserting the script's text would test the diff, not the
  behavior (house convention: no tautological tests).
- **Alternatives considered**: bats test suite — rejected (new test
  framework for one script).

## R6 — Human-in-the-loop OAuth

- **Decision**: the agent starts the device flow and surfaces the
  approval URL + code; the operator approves in their browser; the
  agent then verifies with `difyctl login --resume`.
- **Rationale**: the consent is a browser step by design (Dify OAuth
  device flow); agents have no browser session with the operator's
  credentials — and should not.
- **Alternatives considered**: console credentials reuse (the deploy CLI
  has them) — rejected: difyctl's v2 token store is its own; the release
  notes require the fresh sign-in anyway.

## Error handling (user-requested)

| Condition | Behavior |
|---|---|
| Download interrupted / partial file | sha256 mismatch → abort before chmod; delete the partial binary |
| Checksums file fetch fails | abort before install — never skip the gate |
| Checksum mismatch | abort + remove binary; never execute unverified code |
| `~/.local/bin` already on PATH | skip the `.bashrc` append (idempotent) |
| `difyctl version` fails or server disagrees | abort the sequence before skill install (server unreachable = nothing works) |
| Skill install writes nothing | abort before login (missing SKILL.md = broken agent integration) |
| Device code expires (~15 min) before approval | re-run the device flow; no partial token state |
| Operator denies consent | `--resume` shows no account → report, do not retry automatically |
| `difyctl help` lacks an expected verb | stop before the script's first run; adapt call sites to the discovered surface |
| Script step fails | named-step abort with captured output (restructured `|| { …; exit 1; }` reporting) |
| JSON parse key missing | abort naming the step — never a bare traceback |
| Workspace id missing/unknown | abort before export |
| Draft-hash mismatch on re-import | abort — concurrent edit; never overwrite with stale content |
| Round-trip changes app id/name/code | treat as FAILURE (integrity check extended beyond the original id-only check) |
| Two exports same second | timestamped filename collides — unique suffix per run |
| Stack state changed during the feature | V7 diff of container set/status before/after must be empty |
