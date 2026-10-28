# Contracts: Apply Selected LLM to the Chatflow

Phase 1 output. All contracts are additive — nothing existing changes shape
(constitution Principle I).

## 1. Chat UI HTTP — apply a cloud model

`POST /api/models/apply` (new, host-side route)

```json
// request
{ "model": "moonshotai/kimi-k3" }
// success
{ "applied": "moonshotai/kimi-k3", "durationMs": 42000 }
// failure (previous config keeps serving)
{ "error": "cycle failed at <step>: <detail>" }
```

Rules:

- `model` must be one of the cloud catalog ids; anything else → 400, no cycle.
- One in-flight cycle per server; concurrent requests → 409, no cycle.
- The route awaits the deploy CLI cycle (≤90 s budget) and returns its
  outcome; console credentials never appear in any payload.

## 2. Chat UI HTTP — current configured model

`GET /api/models/current` (new)

```json
{ "model": "moonshotai/kimi-k3" }
```

Rules:

- Resolved from the artifact's three main nodes (research D4); the
  Deepseek default when the artifact is unreadable.
- Cacheless; the answer is always the artifact's current truth.

## 3. Chatflow inputs (unchanged, simplified)

| Field | Value | Rule |
|-------|-------|------|
| `inputs.ai_model` | `"local"` or absent | `"local"` → local branch; anything else → the configured cloud model (else branch) |
| `inputs.cloud_model` | — | **Removed** (FR-005): the chat route no longer sends it; the DSL drops the variable and its router cases |

Battery requests remain byte-identical (no inputs → else branch → the
configured cloud model, whatever it currently is).

## 4. Deploy CLI — `apply-model`

```bash
python -m agentic_rag_mcp.deploy apply-model <openrouter-model-id>
```

Steps (each reported in the RunReport, aborts honestly):

1. **export**: console export of the AGI Assistant app → write
   `dify/AGIAssistant/AGI_Assistant.yml` (the FR-007 artifact).
2. **patch**: set the three main nodes' model to the target + idempotent
   removal of routing-era branches/inputs (research D2).
3. **overwrite**: update the app draft from the patched YAML (console-API
   equivalent of overwrite-import for chatflow apps; draft only — the
   published app is untouched).
4. **publish**: publish the app; only here does the change go live.

Exit 0 = applied; non-zero = failed with the failing step named
(FR-004: previous published config keeps serving).

## 5. Artifact contract

`dify/AGIAssistant/AGI_Assistant.yml` is the cycle-maintained mirror of
the published app: rewritten on every export step (FR-007), git-versioned
for recovery (re-import the previous export after a corrupted cycle).
