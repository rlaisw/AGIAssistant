# Bug Fix: PPT generation fails — empty answers, no deck

- **Slug**: ppt-no-response
- **Fixed**: 2026-10-29T03:05:00+08:00
- **Assessment**: ./assessment.md
- **Status**: applied

## Summary

Removed null variable selectors (`{"type": "variable", "value": null}`) from the chatflow's agent nodes — Dify 1.18's `variable_pool.get(None)` crashed with `len(None)` on them, killing PPT-Master in 59 ms before any LLM or tool call. The normalization now runs inside every `model_apply` cycle so the DSL can never regress to the crashing shape. Deck generation verified end-to-end live.

## Changes

| File | Change | Notes |
|------|--------|-------|
| `src/agentic_rag_mcp/deploy/model_apply.py` | modified | added `strip_null_variable_params()` (null variable selectors and bare-null `allowed_tools`/`context`/`files` → key absent) + call in `patch_dsl` so every apply cycle re-normalizes |
| `dify/AGIAssistant/AGI_Assistant.yml` | modified | 12 params removed (4 agent nodes × allowed_tools/context/files); republished via `deploy chatflow` |
| `tests/unit/test_deploy_model_apply.py` | added tests | pins the runnable shape: wrappers → absent, real selectors pass through, bare nulls → absent |

## Diff Highlights (optional)

```python
for key in [k for k, v in params.items()
            if isinstance(v, dict) and v.get("type") == "variable"
            and not v.get("value")]:
    del params[key]
for key in ("allowed_tools", "context", "files"):
    if key in params and params[key] is None:
        del params[key]
```

## Tests Added or Updated

- `test_deploy_model_apply.py::test_strips_null_variable_selectors_from_agent_params` — null variable selectors must become absent; real selectors (e.g. `["sys", "files"]`) survive; the model block still applies
- `test_deploy_model_apply.py::test_strips_bare_null_agent_params_to_absent` — bare nulls are equally invalid (AgentNodeData validation) and must also normalize to absent

## Local Verification

- `pytest tests/unit -q` → **218 passed** (7 in test_deploy_model_apply, incl. the 2 new)
- Deck probe (service API): PPT-Master ran the full pipeline — 64 `agent_log` tool events, 402 answer chunks, **zero errors**; answer contains deck preview + export links
- Export link `http://localhost:28080/exports/lighthouse_keeping_20261029/...pptx` → **HTTP 200, 14.7 KB** (real .pptx served)
- Battery `chat-journey` (deck roundtrip) → **PASS**: `link=http://localhost:28080/decks/deploy_automation_20261029/... serves=200`
- General Q&A probe → 5 message events, no errors (no regression to the working path)

## Deviations from Assessment

The assessment's root-cause hypothesis (empty `completion_params: {}` defeating Dify's default fill) was **wrong** — disproven by the fact that `Agentic Strategy` runs the same model with the same `{}` shape successfully, and the full traceback (captured from `docker-worker-1`, which the earlier log sweep missed — the workflow executes there, not in `api`) pinned the crash to:

```
runtime_support.py:58   variable = variable_pool.get(agent_input.value)
variable_pool.py:211    if len(selector) < SELECTORS_LENGTH → TypeError
```

The spec-026 apply cycle's export round-trip materialized `{"type": "variable", "value": null}` wrappers on the ppt nodes (`allowed_tools`/`context`/`files`) — absent in the pre-026 export (`75b0c19`), present from `fa754d3` onward. The model change (glm→deepseek) was coincidental; the bug was model-independent and dated from the wrappers' introduction.

Process note: the first normalization attempt wrote bare `null`s — which fails `AgentNodeData` pydantic validation at graph build time and briefly broke *all* questions (two publishes, ~10 minutes, within this fix run). The working shape — proven by the pre-026 export and confirmed live — is the keys **absent entirely**; that shape is now applied, published, and verified on both question paths.

The assessment's preferred remediation files (`model_apply.py` + tests + artifact) were still exactly right; only the mechanism differed.

## Follow-ups

- The **local** deck path (PPT-Master Local on qwen3-8b-nothink) received the same normalization but was not live-tested — the cloud path is verified; test the local route on a quiet day.
- The transient OpenRouter 403 ("model not available in your region", observed once) deserves a DEPLOY.md troubleshooting row distinct from this bug.
- Commit the fix set (model_apply.py, DSL artifact, tests) — `v1` tag remains the pre-fix rollback point.
