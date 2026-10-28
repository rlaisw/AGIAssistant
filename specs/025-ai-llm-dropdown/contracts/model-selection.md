# Contracts: "AI LLM" Model Drop-Down Menu

Phase 1 output. All contracts are additive — nothing existing changes shape
(constitution Principle I).

## 1. Chat UI HTTP — availability probe

`GET /api/models` (new, host-side route; never called by the browser with
parameters; response cacheless)

```json
{
  "models": [
    { "id": "cloud", "available": true },
    { "id": "local", "available": true }
  ]
}
```

Rules:

- `cloud.available` is always `true` (local-only status — clarify decision);
  the route never probes the cloud provider.
- `local.available` = Ollama `/api/tags` reachable within 2 s AND contains
  the no-think model; any error/timeout/malformed body → `false`.
- Failure of the route itself → the drop-down treats Local as unavailable
  (client never guesses).

## 2. Dify chat inputs — `inputs.ai_model` + `inputs.cloud_model`

Sent by `app/api/chat/route.ts` on every `/v1/chat-messages` call:

| Field | Value | Rule |
|-------|-------|------|
| `inputs.ai_model` | `"cloud" \| "local"` | `"local"` → local branch; otherwise the else branch (cloud) |
| `inputs.cloud_model` | OpenRouter model id (e.g. `"moonshotai/kimi-k3"`) | Absent/unknown → the Deepseek default branch; sent only with cloud selections |

The router evaluates `ai_model == "local"` first, then each `cloud_model`
case (`kimi` / `glm` / `qwen38`), then the else (Deepseek default) —
backwards compatible with every existing caller, including the battery
(which sends neither input). Additive: no existing input is renamed or
removed; the `ask` response field set is untouched.

## 3. Chatflow DSL — routed graph

The published DSL (dify/AGIAssistant/AGI_Assistant.yml) gains:

- Start node: input variable `ai_model` (default `"cloud"`).
- New node `model_router` (IF/ELSE) on `{{#start.ai_model#}}`:
  - `"local"` → `intent_router_local`
  - else (default branch) → `intent_router`
- New local nodes, copies of their cloud counterparts with model
  `qwen3-8b-nothink` (Ollama provider, thinking disabled):
  - `intent_router_local` (question-classifier)
  - `agentic_strategy_local` (agent, full tool set)
  - `ppt_master_local` (agent, full tool set)
- Shared, unchanged answer nodes receive edges from BOTH branches:
  `answer` ← `agentic_strategy` | `agentic_strategy_local`;
  `ppt_answer` ← `ppt_master` | `ppt_master_local`.
- Cloud nodes keep their ids and configuration untouched
  (`intent_router`, `agentic_strategy`, `ppt_master`).
- The old `start → intent_router` edge is replaced by
  `start → model_router` fan-out — no dead edges remain (Principle V).

## 4. Browser storage keys

| Key | Value | Writer | Purge |
|-----|-------|--------|-------|
| `agi-model:selection:<conversationId>` | `"cloud" \| "local"` | selection reducer | conversation delete |
| `agi-model:badge:<conversationId>` | JSON `Record<ordinal, "cloud"\|"local"\|"cloud-fallback">` | stream completion | conversation delete |

Badge keys are message ordinals within the Dify message order (stable across
reload/resume; Dify message ids are not exposed to the client). Absence of a
key or entry resolves to `"cloud"` everywhere (backfill rule). The
`"cloud-fallback"` variant marks the FR-004 reset: that reply was actually
served by the cloud model after Local was requested but unavailable — it
badges as the cloud model and renders the persistent inline note.

## 5. Non-goals (contract stability)

- No per-message model attribution is exposed through the Dify API —
  badges are client-owned (storage contract above).
- The Ollama host/port is never present in any browser-visible payload;
  only the boolean `available` crosses the wire.
- The deploy verification battery's requests remain byte-identical
  (no `ai_model` input) — proving the absent-input = cloud default path.
