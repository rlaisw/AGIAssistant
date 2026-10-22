# Data Model: Delete Conversation

All logic extends spec 014's `ai-chat-landing/lib/history/` modules; one new
route handler under `ai-chat-landing/app/api/conversations/[id]/`.

## Entities

### Delete action state machine (per-row, drives the dropdown)

```text
idle ──"…"click──► menu ──Delete──► confirming ──confirm──► in-flight ──ok──► done (row removed)
                     │ └──Cancel/outside-click──► closed (no change)   └─fail──► menu + inline error
                     └── confirm disabled while in-flight (FR-006)
```

- The dropdown itself is stateless UI; this machine lives in the row component.
- `confirming` and `in-flight` are the only states that block other row
  interactions (single delete at a time in v1).

### HistoryError extension (R6, spec 014's class)

```ts
type HistoryErrorCode = "history_unavailable" | "messages_unavailable" | "delete_failed"
```

### Store seam (extends createHistoryState)

```ts
remove(difyId: string): void   // drops the record; re-render regroups buckets
```

Call order is fixed: **backend delete first, remove() on success only** (FR-005).

## Route contract shape (detail in contracts/conversation-delete.md)

`DELETE /api/conversations/[id]` → `200 {}` | `404` unknown id | `502`
upstream failure (client maps to `HistoryError("delete_failed")`).

## Test matrix (Constitution II — failing tests before implementation)

| Test (vitest, node env) | Asserts |
|--------------------------|---------|
| store `remove`: drops the record by difyId; other records untouched; missing id is a no-op | FR-003 |
| store `remove`: bucket regroup after removal (empty bucket disappears — 014 FR-003 holds) | SC-003 |
| route mapper: upstream 204/200 → `{ok: true}`; 404 → not-found; 4xx/5xx/network → `delete_failed` | FR-005, R6 |
| delete state machine: idle→menu→confirm→in-flight→ok closes menu; double-confirm ignored while in-flight | FR-001/002/006 |
| delete state machine: failure → menu reopens with inline error, row still present | FR-005 |
| cancel path: menu→confirm→cancel → zero state change, zero backend calls | FR-002 |
| ordering: remove() called only after backend success (fail first → row kept) | FR-003/005 |
| active-conversation deletion: pane switches to fresh draft; stream abort invoked before removal | US2/AC1, edge |
| drafts never show "…" (delete affordance gated on difyId present) | FR-008 |

## Storage

No new storage — deletion removes the conversation from Dify and from the
session's in-memory records; nothing is persisted locally.
