# Quickstart: Apply Selected LLM to the Chatflow

Phase 1 output — runnable validation scenarios proving the feature
end-to-end. Implementation details live in tasks.md.

## Prerequisites

1. Dify stack up (1.18.0), AGI Assistant published with the single cloud
   path (the FR-005 cleanup applied by the first cycle).
2. Chat UI dev server: `pnpm dev` in `ai-chat-landing/` — NEVER `pnpm
   build` while it runs. Ollama up for the local-path checks.
3. Cloud models registered in the Dify OpenRouter provider
   (`deploy models` — already covers glm/qwen38; kimi-k3 is preset).

## Automated validation (deterministic)

```bash
# yml patch fn: model set on the three main nodes + idempotent cleanup
.venv/bin/python -m pytest tests/unit/test_deploy_model_apply.py -q
# Chat UI units (badge fallback variants, selection normalization)
pnpm -C ai-chat-landing test
pnpm -C ai-chat-landing typecheck && pnpm -C ai-chat-landing lint
# regression: battery unchanged on the default configuration
.venv/bin/python -m agentic_rag_mcp.deploy verify
```

Expected: patch tests green (three main nodes' model set; extra branches
and `cloud_model` removed; second run = no-op); 100+ vitest; battery
10/10.

## Live throwaway checks (SC-001..SC-003)

Use a throwaway conversation; delete it afterwards.

1. **Apply a cloud model (SC-001)**: open "AI LLM" → select Kimi-k3 →
   the composer shows "Applying Kimi-k3…" and sending is disabled until
   it completes (≤90 s) → send "Reply with exactly: PONG" → the reply
   badges Kimi-k3.
2. **Artifact truth (SC-003)**: after the apply, inspect
   `dify/AGIAssistant/AGI_Assistant.yml` — all three main nodes
   (`intent_router`, `agentic_strategy`, `ppt_master`) show
   `moonshotai/kimi-k3`, and no `*_kimi/_glm/_qwen38` nodes or
   `cloud_model` variable remain.
3. **Server truth on load (US3)**: reload the page → the dropdown shows
   Kimi-k3 without any stored selection; a brand-new chat answers on it.
4. **Failure honesty (SC-002)**: simulate a broken cycle (e.g. stop the
   console API or corrupt the artifact path mid-run) → the UI shows the
   error, the selection reverts, and the next message still answers on
   the previous model. Restore, re-verify.
5. **No-op**: re-select the already-configured model → no cycle starts.
6. **Local path unchanged**: select Local, send — routed as in spec 025;
   stop Ollama → instant fallback now targets the globally configured
   cloud model, badged accordingly with the note.
7. **Blocked sends**: during an apply, Enter and the send button do
   nothing (composer shows the applying indicator).

## Cleanup

Delete the throwaway conversation; re-apply `Deepseek-v4.1-flash` to
return the app to the default configuration.
