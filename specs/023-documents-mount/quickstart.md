# Quickstart: Dedicated Documents Mount

## Prerequisites

- The AgenticRAG sidecar running (current container is fine)
- The project venv for unit tests; docker for the live battery
- Nothing else — the tooling creates the host folder

## Validate

1. **Unit tests** (always first):
   ```sh
   .venv/bin/python -m pytest tests/unit/test_deploy_docker_ops.py tests/unit/test_deploy_cli.py tests/contract/test_deploy_cli.py -q
   ```
   Expect: all green including the new run-command mount assertions.

2. **Recreate with the mount** (brief downtime, ~1 min):
   ```sh
   /home/administrator/.local/share/pipx/venvs/agentic-rag-mcp/bin/python -m agentic_rag_mcp.deploy redeploy
   ```
   Expect: build (cached) → recreate with the documents `-v` → health 200
   → tool re-sync 23 tools.

3. **Mount round-trip**: write a probe file into `~/agentic-rag-docs/`,
   then `docker exec agentic-rag ls /data/rag-docs` shows it.

4. **Migration + source swap**: move `reset password.pdf` from
   `ppt-master/rag-docs/` to `~/agentic-rag-docs/`; remove the old source;
   `sources_add {"type":"local_folder","config":{"path":"/data/rag-docs"}}`
   → `added: 1`; `status` shows documents ≥ 1, chunks ≥ 1; the chat
   answers the password-reset question citing the PDF.

5. **Durability**: re-run the redeploy once more and repeat the
   round-trip — the mount survives because the tooling owns it.

6. **Operator sanity**: `ls ~/agentic-rag-docs/` — your documents folder,
   named for what it is, owned by you, mounted into the RAG.

## Failure triage

- The container didn't come back → `docker logs agentic-rag` — the CLI
  aborts on health failure; the config/state volumes keep everything.
- A document doesn't appear in answers → check the sync's `skipped`
  list (encrypted/scanned PDFs skip honestly) and the supported-types
  table in DEPLOY.md Step 6.
- The mount is missing after a manual `docker run` → someone bypassed
  the tooling; the fix is to recreate via `deploy redeploy`, which owns
  the spec.
