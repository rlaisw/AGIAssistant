# Quickstart — PPT-Master MCP Tools Validation Guide

Runnable end-to-end validation for the feature. Prerequisites assume the stack from DEPLOY.md Steps 0–4 is up (Dify + sidecar) and ppt-master is installed at `/kilocode/AGIAssistant/ppt-master`.

## 1. Deploy the updated sidecar

```bash
cd /kilocode/AGIAssistant
docker build -f dify/docker/mcp-server/Dockerfile -t agentic-rag-mcp:latest .
docker rm -f agentic-rag && docker run -d --name agentic-rag \
  --network <DIFY_NETWORK> \
  -v ~/.config/agentic-rag-mcp:/root/.config/agentic-rag-mcp \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  -v /kilocode/AGIAssistant/ppt-master:/opt/ppt-master \
  -p 28080:28080 --restart always agentic-rag-mcp:latest
curl -s localhost:28080/healthz        # {"status": "ok"}
```

The `[ppt]` defaults (scripts/projects under `/opt/ppt-master`, exports URL base `http://localhost:28080/exports`) match this mount.

## 2. Run the automated battery

```bash
cd /kilocode/AGIAssistant
pytest tests/unit/test_ppt_bridge.py tests/integration/test_ppt_pipeline.py tests/contract/test_ppt_contract.py -v
pytest                                   # full suite — existing 228 + new, all green
```

Covers the contract matrix (contracts/ppt-tools.md T01–T25) including every error path.

## 3. Verify tools surface in Dify

Dify UI → Tools → MCP → the sidecar server → **Update**. The tool list shows the 5 new `ppt_*` tools alongside the existing 16.

## 4. Import chatflow v2

Dify Studio → import `dify/Chatflow Basic (AgenticRAG Agent).yml` (v2 — contains the intent-classifier router and the PPT-Master agent node with the rulebook prompt; max iterations ≥ 30). Publish.

## 5. End-to-end scenarios

| # | Do | Expect (maps to) |
|---|----|------------------|
| S1 | In the Chat UI: "help to generate a powerpoint, introduce Dify software" | Progress narration while pages author; final answer contains a download link; file opens in PowerPoint as native editable text (Story 1, SC-001/003) |
| S2 | Same chat: "add one more page about Dify's marketplace" | Agent revises the active project and re-answers with a NEW link; old link still works (FR-015, Story 3) |
| S3 | New chat: "edit the deck I made earlier" | Agent honestly explains cross-conversation edits are v1-out-of-scope and offers regeneration (Edge case) |
| S4 | "generate a 10-page deck about X" | Agent proposes ≤5 pages for one run (bounded v1) or a continuation plan (Edge case) |
| S5 | Attach a file and ask for a deck | Agent explains v1 input limits, offers paste/research alternatives (Edge case) |
| S6 | Direct MCP probe: `ppt_export` on a project with a failing page (or just inspect T18 in the battery) | `PPT_EXPORT_BLOCKED` with fixable summary — no file, no fabricated link (FR-006/010) |

## 6. Concurrency spot-check

Open two Chat UI sessions and request two different one-page decks simultaneously: both return distinct working links; `projects/` contains two disjoint workspaces (SC-006, T21).
