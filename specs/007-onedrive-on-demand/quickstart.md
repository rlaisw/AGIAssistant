# Quickstart: OneDrive On-Demand Embedding with Staleness Reminder

**Feature**: `specs/007-onedrive-on-demand`

Validates the feature end-to-end, including the error paths. Automated suite first (no Microsoft account needed), then a short live check for the real drive.

## Prerequisites

- Python 3.12 env with deps installed (`pip install -e ".[dev]"`)
- Azure AD app registration with delegated `Files.Read` + `offline_access` (only for the live check)
- Docker stack (Dify + agentic-rag sidecar) running — only for the chat-level check

## 1. Automated validation (CI-grade, no network)

```bash
pytest tests/unit/test_onedrive.py tests/unit/test_onedrive_freshness.py tests/unit/test_state_snapshot.py tests/unit/test_migration.py \
       tests/contract/test_onedrive_contract.py tests/integration/test_onedrive_on_demand.py -q
```

Expected: all green, covering the [contract test matrix](contracts/onedrive-on-demand.md) (C1–C6, U1–U8, I1–I6, X1) — including the error paths: not-found paths, unsupported/oversized skips, mid-batch throttling continuation, probe timeout honesty, deleted-cloud notes, watcher isolation (zero Graph requests), and local-source regression.

Full-suite gate (Constitution II — superseded 006 sync tests are gone, everything else unchanged):

```bash
pytest -q
```

## 2. Live on-demand flow (real OneDrive)

```bash
agentic-rag-mcp --transport streamable-http --port 28888
```

Then via any MCP client (or the Dify chat):

1. **Connect — nothing ingests (SC-001)**: `sources_add(type:"onedrive", config:{client_id:"<your-app-id>"})` → `needs_auth`; `sources_auth(source_id)` → visit URL, enter code → healthy. Verify `sources_list` shows the source and `status` reports 0 new documents — even after 5+ minutes (no watcher sync).
2. **Browse**: `onedrive_list_files(source_id, search:"report")` → metadata matches only; nothing downloaded.
3. **Embed chosen files (SC-002)**: `onedrive_embed_files(source_id, files:["/Documents/Q3 Report.docx"])` → per-file result `embedded`. A question about the file's content now cites it; a question about any *other* drive file finds nothing.
4. **Staleness reminder (SC-003)**: edit the file in OneDrive (or touch it) → `ask("what does the Q3 report say about revenue?")` → answer from the embedded copy + `freshness_warnings[0]` naming the file, both timestamps, and the update offer. The system must NOT re-download on its own.
5. **Explicit update (SC-004)**: `onedrive_embed_files(source_id, files:["/Documents/Q3 Report.docx"])` again → `updated`; re-ask → only new content, no reminder.
6. **Deleted-cloud note**: delete the file in OneDrive → re-ask → answer + "last available version" note; the embedded copy still answers.
7. **Error paths**: embed a nonexistent path (`/nope.pdf` → `not_found` + reason, others in the same call still process); run `sources_sync(source_id)` → on-demand notice, no sync; let the token expire → next list/embed returns "Microsoft sign-in required", source degrades, `sources_auth` restores it.
8. **Migration no-op (current deployment)**: restart the server — since this deployment has no legacy embedded OneDrive documents, startup logs record a no-op migration. (With legacy docs: they re-embed once, then never again.)

## 3. Chat-level check (Dify)

In the Dify chat: "add my Q3 report from OneDrive" → agent connects (device code relayed) → lists matches → asks confirmation → embeds → answers with citations; after a cloud edit, answers carry the reminder and the agent offers the one-command update. The agent never embeds more than the files you confirmed.

## Expected outcomes summary

| Step | Observable result |
|---|---|
| Connect + sign-in | Source healthy, knowledge base unchanged, zero background Graph traffic |
| Browse | Names/paths/sizes only; optional filter; empty result is honest |
| Embed | Only named files embedded; per-file outcomes with reasons |
| Ask after cloud edit | Answer + reminder with both timestamps; no auto-download |
| Explicit update | Old content evicted; reminder cleared |
| Any failure | Honest per-file reasons or explicit degraded-source notice — never silent, never fabricated |
