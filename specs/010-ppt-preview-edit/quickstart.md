# Quickstart — PPT Completion Experience Validation Guide

Runnable end-to-end validation for spec 010. Prereq: spec 009 fully deployed (DEPLOY.md Steps 0–4 + 9: Dify + sidecar with the ppt-master mount + chatflow v2 published).

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
# + docker network connect <SSRF_NETWORK> agentic-rag (if your Dify uses the SSRF proxy)
curl -s localhost:28080/healthz   # {"status": "ok"}
```

## 2. Run the automated battery

```bash
cd /kilocode/AGIAssistant
/home/administrator/.local/share/pipx/venvs/agentic-rag-mcp/bin/python -m pytest \
  tests/unit/test_ppt_completion.py \
  tests/integration/test_ppt_completion_pipeline.py \
  tests/contract/test_ppt_completion_contract.py -v
/home/administrator/.local/share/pipx/venvs/agentic-rag-mcp/bin/python -m pytest   # full suite incl. spec 009 (D11)

cd ai-chat-landing && pnpm install && pnpm test   # vitest: deck-url derivation (D13–D16)
pnpm typecheck && pnpm lint
```

## 3. Chat UI: run with the action bar

```bash
pnpm dev   # http://localhost:3000 (refresh the browser to load the new markdown interceptor)
```

## 4. End-to-end scenarios

| # | Do | Expect (maps to) |
|---|----|------------------|
| S1 | In the Chat UI: "generate a one-page deck about Dify software" | The final answer shows the **deck action bar** (⬇ Download / 👁 Preview-Edit icons); clicking Preview/Edit opens the completion page with the slide preview; Download yields the `.pptx` (Story 4, Story 1) |
| S2 | On the completion page, narrow the browser window to mobile width | Preview stays readable and proportioned (Story 2 / AC2) |
| S3 | Same chat: "make the title bigger" | Agent rewrites and re-exports; the new answer's action bar opens a NEW completion page; the OLD page (open in another tab) still shows the old artifact unchanged (FR-007) |
| S4 | Open `http://localhost:28080/decks/nonexistent/whatever/` | Honest 404 page (FR-005) |
| S5 | In the Dify webapp (not the Chat UI), ask for a deck | The answer shows the ordinary markdown link — degrades gracefully (Edge case) |
| S6 | Verify the direct URL from `ppt_export` (`…/exports/<p>/<f>.pptx`) in a fresh curl | Still downloads the file, unchanged (FR-003, SC-004) |
| S7 | Preview-failure path is covered automatically by D04/D05 in the battery (degraded page renders honestly, download works) | FR-008 |

## 5. Concurrency / isolation spot-check

Generate two decks in parallel; each completion page shows only its own deck's slides (snapshot isolation, D03).
