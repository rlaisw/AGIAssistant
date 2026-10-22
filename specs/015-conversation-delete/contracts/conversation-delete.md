# Contract: Delete Conversation (UI-internal + one additive route handler)

No MCP tool schemas change (Constitution I untouched). The contract is one new
same-origin route (key stays server-side, same posture as `/api/chat` and
spec 014's routes) plus the pure seams.

## 1. `DELETE /api/conversations/[id]`

Request: path `id` = Dify conversation id (`[A-Za-z0-9_-]+`, 400 otherwise);
no body.

Proxy of Dify `DELETE /conversations/{id}` with `user: "ai-chat-ui-user"`.

Responses:
- `200 {"ok": true}` — deleted upstream
- `400 {"error": "invalid conversation id"}` — malformed id
- `404 {"error": "conversation not found"}` — unknown upstream id
- `502 {"error": "Dify error (<status>): …"}` — upstream failure/network;
  client maps to `HistoryError("delete_failed")`
- `503 {"error": "DIFY_API_KEY is not configured"}`

Invariants: no key, upstream payload, or `user` value in any response; the
route is idempotent from the client's view (404 after a successful delete is
treated as not-found, not an error that resurrects the row).

## 2. Pure seams (`lib/history/`, node-testable)

```ts
// store (extends spec 014 createHistoryState)
remove(difyId: string): void  // drops record; success-only call site (FR-005)

// per-row delete machine (new, drives the dropdown UI)
createDeleteState(deleteRequest: (difyId: string) => Promise<void>) => {
  status: "idle" | "menu" | "confirming" | "in-flight" | "done" | "error"
  open() / chooseDelete() / confirm(difyId) / cancel()
  error?: HistoryError   // code "delete_failed" only
}
// injected: real route call in prod, stub in tests
```

Invariants:
- `confirm(difyId)` while `in-flight` is ignored (FR-006).
- `cancel()` (or outside-click closing the menu) leaves store + backend
  untouched (FR-002).
- The row's `remove()` fires **after** `deleteRequest` resolves; on
  rejection the row stays and `error` surfaces (FR-003/005).
- The "…" affordance renders only for records with a `difyId` — drafts
  never offer Delete (FR-008).

## 3. Error taxonomy

`HistoryError.code` gains `"delete_failed"`. User-facing copy: "Could not
delete this chat — please try again." Console carries the underlying reason.
No other codes; no raw exceptions cross the seam (R6).

## 4. Dify upstream assumption (versioned)

Dify 1.17 service API `DELETE /conversations/<uuid:conversation_id>`
(verified in `app/controllers/service_api/app/conversation.py`). Rename
(`POST /conversations/{id}/name`) exists but is explicitly **out of v1**;
the menu structure must not require redesign when it is added.
