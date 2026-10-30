# Bug Verification: PPT generation fails — empty answers, no deck

- **Slug**: ppt-no-response
- **Tested**: 2026-10-29T03:57:00+08:00
- **Assessment**: ./assessment.md
- **Fix**: ./fix.md
- **Result**: verified

## Summary

The original symptom no longer reproduces: a fresh deck question runs the complete PPT-Master pipeline (56 tool-call logs, 3,657 answer chunks, 0 errors) and yields a downloadable `.pptx`. All fix tests and the full unit suite pass, and the battery's deck-roundtrip scenario passes on a fresh generation. No regressions found.

## Checks Performed

| Check | Command / Action | Result | Notes |
|-------|------------------|--------|-------|
| Reproduction (post-fix) | service-API deck probe (assessment's exact repro, fresh question "tide pools") | pass | 5 nodes succeeded, 56 `agent_log` + 3,657 `message` events, 0 `len(None)`/validation errors |
| Export artifact | `curl` the answer's export link | pass | `exports/tide_pools_20261029/tide_pools_20261029_035519.pptx` → HTTP 200, 14,707 B |
| New / updated tests | `pytest tests/unit/test_deploy_model_apply.py` | pass | 7 passed — incl. the 2 shape-pinning regressions (null variable selectors → absent; bare nulls → absent; real selectors preserved) |
| Regression suite | `pytest tests/unit` | pass | 218 passed, 26 warnings |
| Battery deck roundtrip | `scenario_chat_journey` (deploy battery) | pass | fresh deck `deploy_automation_477d_20261029_…` generated, links serve 200 |
| Python lint / type-check | — | not-run | no configured Python linter/type-checker in this repo; the pytest suite plus the model_apply round-trip tests are the established gates |

## Output Excerpts

```
== events ==      56 agent_log · 3657 message · 5 node_finished (succeeded) · 0 errors
== errors ==      0  ("has no len" / "validation errors": no matches)
export link: http://localhost:28080/exports/tide_pools_20261029/tide_pools_20261029_035519.pptx
serves: 200 14707B

tests/unit/test_deploy_model_apply.py   7 passed
tests/unit                              218 passed
chat-journey (deck roundtrip): link=http://localhost:28080/decks/deploy_automation_477d_20261029/… serves=200
```

## Residual Risks

- The **local** deck path (PPT-Master Local on qwen3-8b-nothink) received the same normalization but was not live-tested in this verification — the cloud path is proven; test the local route on a quiet day.
- The transient OpenRouter 403 ("model not available in your region", observed once during assessment) is a separate environmental issue that can independently fail any cloud turn; it is not covered by this fix.
- The normalization runs inside `patch_dsl`, but a future **manual console edit** in the Dify UI could reintroduce null variable selectors outside an apply cycle — the symptom would return as the 59 ms node failure.

## Recommendation

Close the bug — verified end-to-end: the symptom is gone on a fresh reproduction, the fix's regression tests pin the runnable DSL shape, the full suite is green, and the deploy battery's deck scenario passes. Commit the fix set (model_apply.py, DSL artifact, tests); the `v1` tag remains the pre-fix rollback point.
