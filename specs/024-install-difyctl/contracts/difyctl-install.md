# Contract: difyctl Install Verification (spec 024)

## Check battery V1–V7

| # | Check | Method | Expected |
|---|---|---|---|
| V1 | Checksum gate | `sha256sum ~/.local/bin/difyctl` vs the official checksums file (linux-x64 line) | match; gate runs BEFORE `chmod +x` / first execution |
| V2 | Version handshake | `difyctl version` | client 1.18.0; server 1.18.0, edition COMMUNITY |
| V3 | Skill installed | `ls ~/.config/kilo/skills/difyctl/` | `SKILL.md` + `references/` present |
| V4 | Login state | `difyctl login --resume` (after operator browser approval) | prints the account email, exit 0 |
| V5 | Read-only describe | `difyctl describe` (verb confirmed via `difyctl help`) on `194e1edf-2eba-442c-b10b-231bebb79c37` | app name "AGI Assistant" |
| V6 | Round-trip script | `bash -n` clean, then one supervised run of `dify/difyctl-export-reimport-publish.sh` | export file saved (`agi_assistant_export_*.yml`), fresh published version id returned, app id/name/webapp code unchanged, no error output |
| V7 | Zero stack impact | container set+statuses before/after; app row in DB (id, name, sites.code) unchanged | identical |

## Error-handling expectations (from research R-table)

- Checksum mismatch / partial download → abort before the binary executes.
- Any battery step failing → name the step and abort; never continue a
  later step (the script fires real export/publish calls).
- Device-code expiry → re-run flow; operator denial → report, no retry.
- Unknown verb on the server-discovered surface → stop before the
  script's first run.
- Draft-hash conflict → abort (stale-overwrite guard).
- Round-trip changing id/name/code → FAILURE even if the script exits 0.

## Failure modes (verification)

Any V-check failing → report the failing step + captured output and
stop; the battery order is the safe order (V6 only after V4/V5 pass —
the script requires a signed-in client and a confirmed verb surface).
