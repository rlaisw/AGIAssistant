# Contract: Chat History (UI-internal + two additive route handlers)

No MCP tool schemas change (Constitution I untouched). The contracts are the
two new same-origin routes (key stays server-side, identical posture to
`/api/chat`, which already sends `user: "ai-chat-ui-user"`) and the pure
module seams the UI consumes.

## 1. `GET /api/conversations` (list, paged)

Request: `?cursor=<dify last_id, optional>&limit=<1..100, default 20>`

Proxy of Dify `GET /conversations` with `user: "ai-chat-ui-user"`.

Response `200`:
```json
{
  "conversations": [
    { "difyId": "…", "title": "…", "lastActivityAt": 1760000000000 }
  ],
  "hasMore": true,
  "nextCursor": "…"
}
```
- `lastActivityAt` = epoch **ms** (route converts Dify unix seconds,
  `updated_at ?? created_at`); `null` when both are absent.
- `title` = Dify `name`; empty → first-question fallback (≤60 chars, never
  "Untitled"). The route never invents titles.
- `hasMore`/`nextCursor` = Dify `has_more`/`last_id`; `nextCursor` null when
  `hasMore` is false.

Errors: `502 { "error": "Dify error (<status>): …" }` (upstream failure),
`503 { "error": "DIFY_API_KEY is not configured" }` — mapped client-side to
`HistoryError("history_unavailable")`. No key, upstream payload, or
`user` value ever appears in the response.

## 2. `GET /api/conversations/[id]/messages` (resume load)

Request: `?cursor=<optional>&limit=<default 100>`

Proxy of Dify `GET /conversations/{id}/messages` with the same `user`.

Response `200`:
```json
{ "messages": [ { "id": 1, "role": "user", "text": "…" },
                 { "id": 2, "role": "assistant", "text": "…", "reasoning": "…", "sources": ["…"] } ],
  "hasMore": false }
```
- Mapping: Dify record → a user turn (its `query`) followed by an assistant
  turn (its `answer`); `metadata.retriever_resources` → deduped `sources`
  (same rule as the chat stream's `message_end` handler); message ids map to
  sequential app `Message.id`s (Dify ids are per-record and re-sequenced).
- Errors: `502` as above (client-side `HistoryError("messages_unavailable")`),
  `404` when the conversation id is unknown upstream.
- Reasoning text: included only when the record carries it (the export
  feature drops it at export time — unchanged).

## 3. Pure module seams (`lib/history/`, node-testable)

```ts
bucketOf(lastActivityAt: number | null, now: Date): BucketId          // FR-001/002
groupConversations(records: ConversationRecord[], now?: Date): BucketedConversations  // FR-003/004 + dedupe
titleFor(difyName: string | null | undefined, firstQuestion?: string): string  // FR-012
createHistoryState(fetchPage): { …loading/ready/error, loadMore(), records }     // FR-006/013 seam
fetchPage: (cursor?: string) => Promise<{ conversations, hasMore, nextCursor }>  // injected: real route in prod, stub in tests
```

**Invariants**:
- `groupConversations` never mutates its input and never throws on
  null/NaN timestamps (floor bucket + console.warn).
- `createHistoryState` exposes no raw exceptions: every fetch failure is a
  `HistoryError` with a code from §Error taxonomy (data-model.md).
- Draft promotion happens outside these seams (page-level, FR-014): a
  session record with a `difyId` from the first message's `done` event
  enters `records`; before that it is not in `records` at all.

## 4. Dify upstream assumptions (versioned)

- Dify 1.17 service API: `GET /conversations` returns
  `{ data: [{ id, name, created_at, updated_at, … }], has_more, limit }`;
  `GET /conversations/{id}/messages` returns
  `{ data: [{ id, query, answer, created_at, metadata, … }], has_more }`.
- Both require the `user` query/body param; both accept `last_id`/`cursor`
  style continuation. If a future Dify drops `updated_at`, the route falls
  back to `created_at` (R3) — behavior degrades, never breaks.
- No new dependencies are introduced (reuse ladder: fetch + date stdlib).
