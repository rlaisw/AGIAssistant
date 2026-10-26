# Data Model: Install difyctl

No persistence, no schema — host tooling + one adopted script.

## Installed entities

```text
~/.local/bin/difyctl              # v1.18.0 linux-x64 binary, sha256-verified
~/.config/kilo/skills/difyctl/   # SKILL.md + references/ (CLI-generated)
dify-token store                  # difyctl-managed OAuth token (client-side)
dify/difyctl-export-reimport-publish.sh   # repo copy, reviewed
```

## The adopted script's parameters (after correction)

| Parameter | Old (foreign) default | New default |
|---|---|---|
| `APP_ID` (arg 1) | `cfee23fa-9c5d-41fc-a633-3bced4389a76` | `194e1edf-2eba-442c-b10b-231bebb79c37` (AGI Assistant) |
| `WORKSPACE_ID` (arg 2) | `40c927ad-5b0c-41a6-a0b2-ccae8703c33c` | `af91d497-36b4-4940-9045-3d7415546381` (administrator's Workspace) |
| `EXPORT_DIR` | `$HOME/Downloads` | unchanged |
| Export filename prefix | `clinic_chatbot_export_` | `agi_assistant_export_` |

Integrity invariant: after any run, app id, name ("AGI Assistant"), and
webapp code (`GwEO6abLduqWHObS`) are unchanged; only the published
version id advances.
