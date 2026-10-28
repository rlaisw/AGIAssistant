# Data Model: Apply Selected LLM to the Chatflow

Phase 1 output. Entities from the spec (Key Entities) plus the client/ops
state they require.

## Entities

### GlobalModelSelection

The model currently configured in the published app (server truth).

| Field | Type | Rule |
|-------|------|------|
| modelId | one of the cloud catalog ids | Read from the artifact's three main nodes (research D4); Deepseek default when unreadable |
| source | `"artifact"` | The published app's mirror — never browser-mutated |

**Validation**: must be one of the registered cloud models
(`deepseek/deepseek-v4.1-flash`, `moonshotai/kimi-k3`,
`z-ai/glm-5.3-flash`, `qwen/qwen3.8-flash`); unknown ids are rejected
before the cycle starts.

### ReconfigureCycle

One export → patch → overwrite → publish run.

| Field | Type | Rule |
|-------|------|------|
| targetModelId | cloud catalog id | Validated before starting |
| steps | `export → patch → overwrite → publish` | Each step must succeed or the cycle aborts |
| outcome | `"applied" \| "failed"` | Failure leaves the published config untouched (FR-004) |
| inFlight | boolean | Single in-flight cycle — further selections queue/disable |

**State machine**:

```text
idle ──select cloud model──► applying ──all steps ok──► applied (selection = target)
                    │                                └─► dropdown/store updated
                    └──any step fails───────────────► failed (previous config serves,
                                                      selection reverts, honest error)
```

### Selection (per conversation, spec 025 — amended semantics)

| Field | Type | Rule |
|-------|------|------|
| conversationId | string | Unchanged |
| modelId | `"local"` or a cloud id | `"local"` stays per-conversation/routed; a cloud id means "the global config" — on load it is superseded by the configured model (display-only provenance) |

### BadgeValue (amended)

| Form | Meaning | Rendering |
|------|---------|-----------|
| `<model-id>` | reply served by that model | badge = displayName |
| `<model-id>\|fallback` | FR-004 fallback reply (Local requested, cloud served) | badge = displayName + persistent note |
| `"cloud-fallback"` (legacy) | same, from the Deepseek-default era | badge = Deepseek + note |

**Backfill rule** (unchanged): absent map entry → cloud default.

## Relationships

```text
GlobalModelSelection 1─1 published app (server truth, artifact-mirrored)
ReconfigureCycle *─1 GlobalModelSelection (each apply replaces it)
Selection (per conversation) ──► GlobalModelSelection when its modelId is cloud
BadgeValue *─1 Assistant Message (per-message provenance, spec 025)
```

## Validation rules summary

- Exactly one in-flight cycle; sends disabled while it runs (FR-003).
- Patch touches exactly the three main node ids; anything else in the
  artifact is preserved byte-for-byte except the FR-005 removals.
- Cleanup (extra branches + `cloud_model` input) is idempotent.
- Badge values restricted to catalog ids + `|fallback` suffix + legacy
  `"cloud-fallback"`; unknown → cloud default.
