# Quickstart: "AI LLM" Model Drop-Down Menu

Phase 1 output — runnable validation scenarios proving the feature
end-to-end. Implementation details live in tasks.md.

## Prerequisites

1. Ollama up and bound wide:
   `OLLAMA_HOST=0.0.0.0 nohup ollama serve > ~/ollama/serve.log 2>&1 &`
2. Models present: `ollama list` shows `qwen3:8b` and the derived
   `qwen3-8b-nothink` (created during implementation per research D3;
   verify `ollama show --modelfile qwen3-8b-nothink` carries the think-off
   parameter).
3. Dify stack up (1.18.0) and the chatflow published with the routed
   graph: `python -m agentic_rag_mcp.deploy chatflow` (project venv).
4. Chat UI dev server: `pnpm dev` in `ai-chat-landing/` — NEVER `pnpm
   build` while it runs.

## Automated validation (deterministic)

```bash
# in ai-chat-landing/
pnpm typecheck && pnpm lint
pnpm test        # new lib/models suites: selection, badge, availability,
                 # persistence, /api/models handler (error cases stubbed)
```

Expected: all suites green; no existing spec-013/014/015/018-021 tests
regress.

```bash
# regression: battery unchanged, cloud-only (SC-004)
python -m agentic_rag_mcp.deploy verify
```

Expected: 10/10 — identical to pre-feature, proving absent `ai_model`
defaults to cloud.

## Live throwaway checks (SC-001..SC-003, FR-009)

Use a throwaway conversation; delete it afterwards (its storage keys must
be gone — verify in devtools Application tab, error case 7/deletes).

1. **Switch + badge (SC-001)**: open "AI LLM" → select Local (hint text
   "slower, CPU-bound" visible) → ask "which model are you?" → reply
   identifies Qwen3 and its footer badge reads Local; select Cloud → next
   reply badges Cloud. ≤2 interactions per switch.
2. **Unavailable state (SC-002)**: stop Ollama (`pkill -f "ollama serve"`)
   → open drop-down → Local shows unavailable within 5 s and cannot be
   selected; send a message → Cloud answers and an inline note (persistent
   in history) states the reset.
3. **Reset semantics**: restart Ollama → conversation stays on Cloud until
   Local is re-selected (no auto-resume).
4. **Persistence (SC-003)**: with Local selected, reload the page, resume
   the conversation from the sidebar → Local still active.
5. **No reasoning (FR-009)**: every Local reply contains answer text only —
   no thinking block, visible or hidden (view page source / message data).
6. **Mid-stream failure (FR-007)**: with Local selected, `pkill` Ollama
   right after sending → message ends in the standard error state;
   selection shows Cloud afterwards.
7. **Mobile drawer sanity**: below md the drop-down is reachable in the
   overlay layout (spec 019 behavior preserved).

## Cleanup

Delete the throwaway conversation via the sidebar delete flow (spec 015);
confirm localStorage keys for it are purged.
