# Quickstart: Install difyctl

## Prerequisites

- Dify 1.18.0 running locally (console at http://localhost — verified this stack)
- The operator at the machine, ready to click an OAuth consent in the browser
- Nothing else — no repo code, no packages

## Validate

1. **Install + checksum gate** (V1):
   ```sh
   mkdir -p ~/.local/bin
   curl -L -o ~/.local/bin/difyctl \
     https://github.com/langgenius/dify/releases/download/1.18.0/difyctl-v1.18.0-linux-x64
   curl -L -o /tmp/difyctl-checksums.txt \
     https://github.com/langgenius/dify/releases/download/1.18.0/difyctl-v1.18.0-checksums.txt
   grep "linux-x64" /tmp/difyctl-checksums.txt   # note the expected sha256
   sha256sum ~/.local/bin/difyctl               # must match the line above
   chmod +x ~/.local/bin/difyctl
   ```
   Any mismatch → stop, delete the binary, re-download.

2. **PATH + version handshake** (V2):
   ```sh
   grep -q '.local/bin' ~/.bashrc || echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
   source ~/.bashrc
   difyctl version     # client 1.18.0, server 1.18.0 COMMUNITY
   ```

3. **Skill** (V3):
   ```sh
   difyctl install skills ~/.config/kilo/skills
   ls ~/.config/kilo/skills/difyctl/   # SKILL.md + references/
   ```

4. **Sign in** (V4 — human step):
   ```sh
   difyctl login --server http://localhost --no-browser --no-wait
   ```
   Open the printed URL in the browser, enter the code, approve.
   Then: `difyctl login --resume` must print the account email.

5. **Describe proof** (V5):
   ```sh
   difyctl help        # confirm the describe verb first
   difyctl describe console_app --app-id 194e1edf-2eba-442c-b10b-231bebb79c37 --json | python3 -m json.tool | head
   ```
   Expect name "AGI Assistant".

6. **Round-trip script** (V6): `bash -n dify/difyctl-export-reimport-publish.sh`,
   then one supervised run — ends with id/name/webapp code unchanged and a
   fresh published version id; export saved as
   `~/Downloads/agi_assistant_export_*.yml`.

7. **Zero stack impact** (V7): `docker ps` identical before/after; the
   app's row (id, name, sites code `GwEO6abLduqWHObS`) unchanged.

## Failure triage

- Checksum mismatch → re-download; if it persists, stop and investigate
  (never execute the binary).
- `version` shows no server → Dify console unreachable; check
  `docker ps` for the api container before touching difyctl.
- `--resume` silent after approval → wait a few seconds and retry once;
  device codes can take a moment to complete in the background.
- Describe verb unknown → the surface is server-discovered; run
  `difyctl help` and use the listed operations — do not trust older
  syntax from other guides.
- Script step fails → its named-step message says which of export /
  re-import / publish / verify broke and the captured output; fix that
  step only — the earlier steps completed idempotently.
