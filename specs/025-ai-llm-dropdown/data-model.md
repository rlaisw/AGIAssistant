# Data Model: "AI LLM" Model Drop-Down Menu

Phase 1 output. Entities from the spec (Key Entities) plus the client-side
state they require. No new server-side storage (research D4).

## Entities

### ModelOption

The catalog behind the drop-down — fixed, two rows.

| Field | Type | Rule |
|-------|------|------|
| id | `"cloud" \| "local"` | Stable ids; exactly two options (spec FR-001) |
| displayName | string | Cloud: "DeepSeek"; Local: "Qwen3 8B" |
| origin | `"cloud" \| "local"` | Drives the FR-006 hint (local: slower, CPU-bound) |
| isDefault | boolean | Cloud = default; Local = false |
| available | boolean | Cloud always true (local-only status); Local from probe |

### Selection

The conversation's single active model.

| Field | Type | Rule |
|-------|------|------|
| conversationId | string | Dify conversation id; drafts (no id yet) → implicit cloud |
| modelId | `"cloud" \| "local"` | Exactly one active at any time (FR-001) |

**State machine**:

```text
new conversation ───────────────────────────► cloud
cloud ──user selects local──► local
local ──user selects cloud──► cloud
local ──probe fails at send──► cloud  (+ inline persistent note)   FR-004
local ──stream error────────► cloud  (+ message error state)       FR-007
local ──server recovers─────► (stays cloud until user re-selects)  Reset
```

**Validation**: `modelId ∈ {cloud, local}`; any other stored value →
treated as "cloud". Switching never rewrites past messages (FR-005).

### MessageBadgeMap

Per-conversation record of which model produced each assistant message.

| Field | Type | Rule |
|-------|------|------|
| conversationId | string | One map per conversation |
| entries | `Record<ordinal, "cloud" \| "local" \| "cloud-fallback">` | Written at stream completion; never mutated afterwards |

Ordinals are message indexes in the Dify message order (stable across
reload/resume). `"cloud-fallback"` = the FR-004 reset variant: served by the
cloud model after Local was requested but unavailable; badges as cloud with
the persistent inline note.

**Backfill rule** (FR-008): messageId absent from the map → badge shows
"cloud". Correct for all pre-feature messages; post-feature messages always
have an entry because the map is written in the same code path that
finishes the stream.

### AvailabilityReport

The `/api/models` response payload (see contracts/model-selection.md).

| Field | Type | Rule |
|-------|------|------|
| models | `ModelOption[]` (id + available) | Local = reachable && model present; any probe failure → `available: false` — never guessed |

## Storage

- `agi-model:selection:<conversationId>` → `"cloud" | "local"` (string)
- `agi-model:badge:<conversationId>` → JSON `Record<messageId, "cloud"|"local">`
- Both purged on conversation delete (hooks into the spec-015 delete flow).
- Absent/unreadable storage resolves to cloud everywhere (error case 7).

## Relationships

```text
Conversation 1─1 Selection (per conversation, persisted client-side)
Conversation 1─1 MessageBadgeMap (per conversation, persisted client-side)
MessageBadgeMap *─1 messageId (Dify message id, server-owned)
ModelOption 1─* referenced by Selection.entries' values and badge values
```

## Validation rules summary

- Exactly two ModelOptions; ids immutable strings.
- Single-active invariant enforced by the selection reducer (unit-tested).
- Badge values restricted to the two model ids; unknown → cloud.
- Probe result is boolean only — no partial/unknown availability states.
