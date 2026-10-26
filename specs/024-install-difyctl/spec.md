# Feature Specification: Install difyctl (Dify CLI + Skill + Login)

**Feature Branch**: `024-install-difyctl`

**Created**: 2026-10-26

**Status**: Draft

**Input**: User description: "i want to install difyctl, refer to the above chat conversation" — install the difyctl v1.18.0 command-line client on this host (WSL2, linux-x64), install its agent skill, complete the OAuth device-flow sign-in against the local Dify 1.18.0 console, verify read-only access to the AGI Assistant app, and adopt the operator's export→re-import→publish round-trip script (`~/Desktop/difyctl-export-reimport-publish.sh`) into the repo after fixing its defects. Verified in the preceding conversation against the official 1.18.0 release (GitHub API): the reference guide's download URL was wrong (tag is `1.18.0`, asset is `difyctl-v1.18.0-linux-x64`) and its login order was inverted; the round-trip script's initial "does not exist / redundant" assessment was corrected at double-clarify when the operator placed the script at `~/Desktop` (it is complementary to the deploy CLI — a server-side draft round-trip — and needs its foreign defaults, unverified command syntax, and dead error diagnostics fixed before adoption).

## Clarifications

### Session 2026-10-26

- Q (double-clarify): Does the reference guide's `difyctl-export-reimport-publish.sh` exist after all? → A: yes — the operator placed it at `~/Desktop/difyctl-export-reimport-publish.sh` (read and reviewed). It is a coherent server-side round-trip: export the app's current draft → re-import it unchanged (overwrite mode, draft-hash guarded) → publish → verify the app id survived. It is **complementary to, not redundant with** the deploy CLI (`deploy chatflow` pushes the repo's DSL to the server; the script re-publishes the server's own draft) — the earlier "redundant" assessment is corrected here.
- Q: Can the script run as-is? → A: no — three defects must be fixed first: (1) its default APP_ID/WORKSPACE_ID point at a foreign deployment ("clinic_chatbot" `cfee23fa-…` / `40c927ad-…`) — the AGI Assistant id `194e1edf…` and our workspace id (looked up at implementation time) must be passed or baked in; (2) every difyctl subcommand and JSON shape it parses (`data['data']`, `draft_hash`) must be confirmed via `difyctl help` against the 1.18.0 server-discovered surface; (3) under `set -euo pipefail` the `if [[ $? -ne 0 ]]` diagnostics are unreachable (the script aborts at the failed `VAR=$(…)` assignment) — reachable error reporting needs restructuring.
- Q (placement): where does the reviewed script live? → A: `~/Desktop` is not a durable operational location — a reviewed copy with corrected defaults is adopted into the repo (so it survives with the project), runnable from there.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Operator installs the Dify CLI and signs in (Priority: P1)

The operator (with a code agent) installs the difyctl v1.18.0 binary on
the host, verifies its checksum against the official checksums file,
makes it callable on PATH, installs the bundled difyctl agent skill, and
completes the OAuth device-flow sign-in against the local console
(http://localhost — the same nginx the browser uses). The operator
approves the consent in their browser (a human step the agent cannot
do). Afterwards, difyctl commands can manage Dify apps from the
terminal, and the agent gains the difyctl skill for future app-building
work. The AGI Assistant app is described read-only as the end-to-end
proof.

**Why this priority**: it is the entire feature — a working, signed-in
CLI plus its skill, touching nothing else.

**Independent Test**: `difyctl version` reports client 1.18.0 and server
1.18.0 (COMMUNITY); `difyctl login --resume` shows the account; the
skill files exist; describing app `194e1edf…` shows "AGI Assistant".

**Acceptance Scenarios**:

1. **Given** the host (linux-x64), **When** the binary is downloaded
   from the verified URL
   (`https://github.com/langgenius/dify/releases/download/1.18.0/difyctl-v1.18.0-linux-x64`),
   **Then** it is placed at `~/.local/bin/difyctl`, made executable, and
   its SHA-256 matches the official checksums file (abort on mismatch).
2. **Given** the installed binary on PATH, **When** `difyctl version`
   runs, **Then** it reports client version 1.18.0 and server version
   1.18.0, edition COMMUNITY.
3. **Given** the CLI, **When** `difyctl install skills ~/.config/kilo/skills`
   runs, **Then** the skill files (SKILL.md + references) appear at
   `~/.config/kilo/skills/difyctl/`.
4. **Given** no prior login (fresh v2 client), **When** the device flow
   starts (`difyctl login --server http://localhost --no-browser --no-wait`)
   and the operator approves the consent in their browser within the
   code's validity window, **Then** the token is stored and
   `difyctl login --resume` prints the signed-in account email.
5. **Given** a signed-in CLI, **When** the AGI Assistant app is
   described read-only (`difyctl describe` — exact command confirmed
   via `difyctl help`, since 1.18.0's surface is server-discovered),
   **Then** app `194e1edf-2eba-442c-b10b-231bebb79c37` shows name
   "AGI Assistant".

---

### Edge Cases

- **Checksum mismatch** → abort installation; never install an
  unverified binary (85 MB download).
- **Device code expiry**: the consent window (typically 15 minutes)
  closes before the operator approves → re-run the device flow; no
  partial state.
- **PATH**: `~/.local/bin` may not be on PATH → append to `~/.bashrc`
  only if absent (idempotent).
- **Login state**: the v2 client does not reuse v1 login state —
  irrelevant here (first install), noted for future reinstalls.
- **Command surface drift**: 1.18.0 replaces the old
  `/openapi/v1/apps/{app_id}:run` route with per-mode, server-discovered
  operations → exact subcommand names must be confirmed with
  `difyctl help` before use; do not hard-code the reference guide's
  syntax.
- **Human-in-the-loop**: the OAuth approval is a browser step the agent
  cannot perform — the agent surfaces the URL + code and waits; the
  operator approves.

### Error Handling (adopted round-trip script, FR-007)

- **Unreachable diagnostics**: under `set -euo pipefail` the script
  aborts at the failed `VAR=$(…)` assignment, so its `if [[ $? -ne 0 ]]`
  blocks never print — restructure so each failed step reports its name
  and captured output before exit.
- **JSON shape drift**: every parsed field (`data['data']`,
  `draft_hash`, `version_id`, `info.name`) is shape-checked; a missing
  key aborts naming the step, never a bare Python traceback.
- **Foreign defaults**: the script's baked-in "clinic_chatbot" app and
  workspace ids must be replaced before any run; a missing workspace id
  aborts before export.
- **Round-trip integrity**: a run that changes the app id, name, or
  webapp code is a failure (extend the existing id check to name+code).
- **Concurrent-edit guard**: a draft-hash mismatch on re-import aborts —
  never overwrite the app with stale exported content.
- **Export collision**: two exports in the same second → the timestamped
  filename collides; include a unique suffix or fail loudly.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The difyctl v1.18.0 linux-x64 binary MUST be installed
  at `~/.local/bin/difyctl`, executable, checksum-verified against the
  official `difyctl-v1.18.0-checksums.txt` (abort on mismatch), and
  `~/.local/bin` MUST be on PATH (appended to `~/.bashrc` only if
  absent).
- **FR-002**: `difyctl version` MUST report client version 1.18.0 and
  server version 1.18.0 (edition COMMUNITY).
- **FR-003**: The difyctl agent skill MUST be installed to
  `~/.config/kilo/skills/difyctl/` (SKILL.md plus reference files).
- **FR-004**: The OAuth device flow MUST be completed against the local
  console and the token stored, verified by `difyctl login --resume`
  printing the account email.
- **FR-005**: A read-only describe of app
  `194e1edf-2eba-442c-b10b-231bebb79c37` MUST show the app name
  "AGI Assistant" (exact subcommand confirmed via `difyctl help`).
- **FR-006**: The installation MUST NOT modify the Dify stack, the AGI
  Assistant app's content, the repo's deploy automation, or any existing
  skill. `python -m agentic_rag_mcp.deploy chatflow` remains the owner of
  repo-driven update/publish.
- **FR-007**: The operator's `difyctl-export-reimport-publish.sh` (server-side
  draft round-trip + force-republish) MUST be adopted into the repo as a
  reviewed copy with: the AGI Assistant app id `194e1edf…` and the
  looked-up workspace id as defaults; every difyctl subcommand/JSON shape
  verified against the live server-discovered surface before first run;
  reachable error reporting (the `set -e` dead-diagnostics defect fixed);
  and an export file name/label that does not say "clinic_chatbot".
  The round-trip MUST end with the app id, name ("AGI Assistant"), and
  webapp code unchanged.

### Key Entities

- A host-level CLI binary (`~/.local/bin/difyctl`) + a stored OAuth
  token (client-managed) + a skill directory
  (`~/.config/kilo/skills/difyctl/`). No repo artifacts, no schema, no
  app changes.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `difyctl version` output contains client version
  "1.18.0" and server version "1.18.0" with edition "COMMUNITY".
- **SC-002**: `ls ~/.config/kilo/skills/difyctl/` shows `SKILL.md` and
  its `references/` directory.
- **SC-003**: `difyctl login --resume` prints the signed-in account
  email (non-empty, no error).
- **SC-004**: A read-only difyctl describe of
  `194e1edf-2eba-442c-b10b-231bebb79c37` shows the name
  "AGI Assistant".
- **SC-005**: Zero changes to the Dify stack and the app: container set
  and statuses identical before/after; the app's published state,
  webapp URL (http://localhost/chat/GwEO6abLduqWHObS) and service API
  key unchanged.
- **SC-006**: The adopted round-trip script runs to completion against
  the AGI Assistant app and ends with app id, name ("AGI Assistant"),
  and webapp code all unchanged, an export file saved, a fresh published
  version id returned, and no error output.

## Assumptions

- Verified in the preceding conversation (GitHub API): download URL
  `https://github.com/langgenius/dify/releases/download/1.18.0/difyctl-v1.18.0-linux-x64`
  (85 MB, SHA-256 `2ab8eafb3c6870272fef0c9d1faea99181500905091a6c7b38e4e5c9822eb99b`)
  — the reference guide's URL (`v1.18.0/difyctl-linux-amd64`) would 404.
- Host: WSL2 Ubuntu, linux-x64.
- Login server: `http://localhost` (the LAN IP 10.161.92.34 reaches the
  same console nginx; either works — default localhost).
- The checksum comparison uses the official checksums file, not just the
  API-published digest (both available; the file is the canonical
  source).
- The OAuth approval happens in the operator's browser (Windows-side;
  WSL2 localhost forwarding reaches the console).
- The operator's round-trip script (placed at
  `~/Desktop/difyctl-export-reimport-publish.sh`, read and reviewed) is
  adopted into the repo as a reviewed copy with corrected defaults —
  `~/Desktop` is not a durable operational location. Its
  export→re-import→publish is a server-side draft round-trip,
  complementary to (not a replacement for) the deploy CLI's repo-driven
  update+publish.
- difyctl is an operator convenience parallel to the deploy CLI — it
  does not replace any part of the deployment automation.
