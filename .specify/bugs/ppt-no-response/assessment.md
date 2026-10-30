# Bug Assessment: PPT generation fails — empty answers, no deck

- **Slug**: ppt-no-response
- **Created**: 2026-10-29T02:55:00+08:00
- **Source**: pasted text ("fail to generate powerpoint, no response") + live reproduction probes
- **Verdict**: valid
- **Severity**: high

## Report (verbatim or summarized)

User report: *"fail to generate powerpoint, no response"*. First observed 2026-10-28 ~17:20 HKT during spec-027 acceptance work (T026 had to substitute an infographic artifact for the canonical deck test); still failing 2026-10-29 02:39 HKT.

## Symptom

Deck-type questions ("Generate a one-page deck about X") route to the PPT-Master agent node, which fails within ~59 ms with `object of type 'NoneType' has no len()`; the workflow emits **zero** message/agent_message events, so the chat shows an empty assistant bubble with no error text — the user sees "no response". General (non-deck) questions answer normally.

## Reproduction

1. `curl -sN -X POST http://localhost/v1/chat-messages -H "Authorization: Bearer $DIFY_API_KEY" -d '{"inputs":{},"query":"generate a one-page deck about lighthouse keeping, keep it very short","response_mode":"streaming","conversation_id":"","user":"bug-assess-probe"}'`
2. Observe: 4 `node_started`/`node_finished` events, `PPT-Master` `node_type: agent` → `status: failed`, `error: "object of type 'NoneType' has no len()"`, `elapsed: 0.0589`
3. No `message`/`agent_message` events arrive; the answer stream is empty.

Reproduced 3× (2026-10-28 17:20 ×2, 2026-10-29 02:39 ×1) — deterministic.

## Suspected Code Paths

- `dify/AGIAssistant/AGI_Assistant.yml` — PPT-Master node `agent_parameters.model.value`: currently `deepseek/deepseek-v4.1-flash` with **`completion_params: {}`** (empty but present). Diff vs the last known-good DSL (git `fa754d3`, 2026-10-27, when deck battery `chat-journey` passed with `z-ai/glm-5.3-flash`): the model value is the only functional change to this node.
- Dify api container `core/workflow/nodes/agent/runtime_support.py:~209-214` — populates missing `completion_params` with model-schema defaults, **but only `if "completion_params" not in value`** — the spec-026 model_apply writes `completion_params: {}` into the DSL, so the fill is skipped and the plugin daemon receives empty params. The code comment itself documents the trap: *"some model providers raise KeyError('required') when completion_params is empty because their parameter_rules declare required fields with no default"*.
- `langgenius/agent` 0.0.51 plugin (plugin daemon, `strategies/function_calling.py`) — consumes the empty completion_params; the failing `len(None)` most plausibly originates in the plugin/SDK parameter-coercion path for deepseek's stricter parameter rules (glm's schema tolerates `{}`; the failure is model-dependent despite both nodes carrying the same `completion_params: {}`).
- Sidecar (`agentic-rag`) — **excluded**: no errors in its logs, and the node dies in 59 ms before any MCP tool call reaches it (api logs show no `/mcp` calls during the failure window).
- OpenRouter/upstream — **excluded as the persistent cause**: direct API probes with the configured credential at 2026-10-29 02:46 answered 200 for all four models (deepseek/deepseek-v4.1-flash, z-ai/glm-5.3-flash, moonshotai/kimi-k3, qwen/qwen3.8-flash). A transient 403 "model not available in your region" was observed once in the plugin daemon logs at 02:22:56 (user's run — OpenRouter geo-gating flaps per endpoint) — environmental noise, not the deterministic failure.

## Root Cause Hypothesis

The spec-026 model_apply rewrote the cloud agent nodes' model-selector values to `deepseek/deepseek-v4.1-flash` carrying `completion_params: {}`. Dify's api-side default-fill is skipped because the key exists (empty), so the agent plugin receives empty completion params, which deepseek's stricter parameter rules cannot coerce — raising `len(None)` (or an equivalent required-param error) inside the plugin strategy at prompt/model setup, ~59 ms into the node, before any LLM or tool call. With `glm-5.3-flash` (the last model applied before decks last worked) the empty params pass through benignly, which is why the bug appeared exactly when the serving model switched. **Confidence: medium-high** — the trigger correlation is exact and the code path is documented; the precise `len(None)` statement inside the plugin SDK is not yet pinned (no traceback is logged anywhere; the exception surfaces only as the node error string).

## Proposed Remediation

**Preferred**: make the model-selector values carry *real* completion params (or none at all) instead of `{}`: drop `completion_params: {}` from the cloud agent nodes' model values in `dify/AGIAssistant/AGI_Assistant.yml` (so Dify's api-side default-fill populates from each model's schema), republish via `python -m agentic_rag_mcp.deploy chatflow`, and harden `src/agentic_rag_mcp/deploy/model_apply.py` to stop writing empty `completion_params` into model-selector values (root-cause fix in our code, not Dify's).

**Alternatives**:
- Patch the `langgenius/agent` plugin to tolerate empty completion_params (upstream-fix territory; slower, and the plugin is vendor-managed).
- Keep glm-5.3-flash as the deck model (works around, but breaks the moment the user applies deepseek again via the dropdown).

**Files likely to change**:
- `dify/AGIAssistant/AGI_Assistant.yml` (drop `completion_params: {}` from agent model values)
- `src/agentic_rag_mcp/deploy/model_apply.py` (stop emitting empty completion_params)
- `tests/unit/test_deploy_model_apply.py` (regression: emitted model values must not carry `completion_params: {}`)

**Tests to add or update**:
- model_apply unit test asserting the applied model value contains either schema-derived defaults or no `completion_params` key
- live check after republish: deck question via the service API → PPT-Master succeeds, answer contains a `28080/decks|exports` link (the spec-027 T026 scenario re-run with the canonical deck artifact)

## Risks & Considerations

- Editing agent model values touches the published chatflow — must republish via the deploy CLI and re-run the battery to catch regressions (the `stop-generation` and `chat-ui-liveness` scenarios are the sensitive ones).
- If the real `len(None)` turns out to be elsewhere in the plugin SDK, dropping `completion_params: {}` may not fully fix it — the fix phase should start by re-running the deck probe after the DSL change and, if it still fails, capture the plugin-side traceback with `docker logs docker-plugin_daemon-1` around the exact failure second.
- The transient OpenRouter 403 (region gating) can independently break any cloud turn — worth a separate DEPLOY.md troubleshooting row, but do not conflate it with this bug.

## Open Questions

- [NEEDS CLARIFICATION: none blocking — the fix can proceed on the preferred path; the exact SDK statement raising len(None) can be pinned during fix-time verification.]

## Unverified

- The precise source line of `len(None)` inside the plugin/SDK (no traceback is logged; only the node error string is observable). Pin during `/speckit.bug.fix` verification if the DSL change does not eliminate it.
