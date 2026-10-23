# Contract: Documents Mount Verification (spec 023)

## Check battery V1–V6

| # | Check | Method | Expected |
|---|---|---|---|
| V1 | Run-command unit test | pytest (mocked subprocess): `recreate_container` emits `-v <home>/agentic-rag-docs:/data/rag-docs` and `mkdir -p` runs first | assertions green; existing deploy unit tests unaffected |
| V2 | Mount round-trip (host→container) | recreate via the deploy tooling; `docker exec agentic-rag ls /data/rag-docs` after writing a probe file host-side | probe file visible in container |
| V3 | Migration + source swap | move `reset password.pdf` host-side; `sources_remove` old `rag-docs` source; `sources_add {"type":"local_folder","config":{"path":"/data/rag-docs"}}` | add response: `added: 1, skipped: []`; old source absent from `sources_list` |
| V4 | Index counts | `status` tool | documents ≥ 1, chunks ≥ 1; asking the chat about password reset cites the document |
| V5 | Durable mount (FR-004) | a second recreate driven by the tooling (redeploy), then V2 again | mount still present; source still syncs |
| V6 | Runbook docs (FR-006) | grep DEPLOY.md Step 6 + the deploy skill for the folder path and sync note | both document `~/agentic-rag-docs/`, supported types, ≤5-min sync, one-time registration |

## Error-handling expectations (from research)

- Failed recreate / health timeout → the CLI aborts loudly; config and
  state survive on their volumes; re-run heals.
- Migration is idempotent — both sources may coexist briefly; the empty
  old folder's next sync removes its stale doc automatically.
- Operator deletes the host folder mid-flight → next recreate re-creates
  it (`mkdir -p`); self-healing on the deploy path.
- Unsupported extensions unchanged (silently ignored; audio skipped with
  reason).

## Failure modes (verification)

Any V-check failing → report the failing step and abort the sequence;
never continue migration steps after a failed recreate (the battery runs
in the listed order for exactly that reason).
