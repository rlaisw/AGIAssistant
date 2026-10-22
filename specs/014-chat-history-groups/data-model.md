# Data Model: Time-Grouped Chat History

All new logic lives in `ai-chat-landing/lib/history/` (pure) plus two route
handlers under `ai-chat-landing/app/api/conversations/`.

## Entities

### ConversationRecord (route → UI shape)

```ts
type ConversationRecord = {
  difyId: string            // Dify conversation id (unique, never null)
  title: string             // Dify name, else first-question fallback ≤60 chars (FR-012)
  lastActivityAt: number | null  // epoch ms; updated_at ?? created_at (R3);
                            // null → floor bucket + console.warn
}
```

Built by the route from Dify's conversation object; `title` derivation is
route-side so the sidebar stays presentational.

### Bucket section (pure output)

```ts
type BucketId = "today" | "yesterday" | "previous-7-days" | "last-month" | "few-months-ago"
type BucketedConversations = { id: BucketId; label: string; items: ConversationRecord[] }[]
```

Order fixed as above; empty buckets omitted (FR-003); within-bucket order =
most recent `lastActivityAt` first (FR-004); null-timestamp records sort last
within the floor bucket.

### Bucket boundaries (FR-002, local time, pure date math)

| Bucket | Range (relative to local `now`) |
|--------|----------------------------------|
| today | `now ≥ startOfToday` |
| yesterday | `[startOfToday − 1d, startOfToday)` |
| previous-7-days | `[startOfToday − 8d, startOfToday − 1d)` |
| last-month | `[startOfToday − 38d, startOfToday − 8d)` |
| few-months-ago | `< startOfToday − 38d` (floor, FR-007) |

(38d = 1d + 7d + 30d; all boundaries are local calendar midnights.)

### HistoryState machine (sidebar data flow)

```text
idle ──open──► loading ──ok──► ready ──Load more──► loadingMore ──ok──► ready
                 │ └─fail──► error ──retry──► loading
                 └───────────────ready(hasMore=false)──► Load more hidden (FR-013)
```

- `groupConversations(records, now)` is called on every render of the
  records array (records carry last-activity updated by send/resume, FR-006).
- Duplicate difyIds are deduped by latest lastActivityAt (session record
  beats fetched record — the session always has the fresher timestamp).

### Error taxonomy (R6)

```ts
type HistoryErrorCode = "history_unavailable" | "messages_unavailable"
class HistoryError extends Error { code: HistoryErrorCode }
```
`invalid_timestamp` is console-only (never user-facing).

### Draft lifecycle (FR-014, R7)

Session-only draft → first message `done` event carries `conversationId` →
draft promoted to ConversationRecord under Today. Promoted drafts survive
reload via the backend list; unpromoted drafts vanish on reload (intended).

## Test matrix (Constitution II — failing tests before implementation)

| Test (vitest, node env) | Asserts |
|--------------------------|---------|
| bucketOf: fixed `now`, one record per bucket | FR-001/002, SC-001 |
| bucketOf: 00:01-vs-23:59 same-day and midnight-crossing cases | edge (local time) |
| bucketOf: null/NaN timestamp → floor bucket | R3, edge |
| bucketOf: exactly on each boundary (−1d, −8d, −38d midnight) | FR-002 boundaries |
| groupConversations: empty buckets omitted, order of sections | FR-003 |
| groupConversations: within-bucket most-recent-first; nulls last | FR-004 |
| groupConversations: dedupe by difyId keeps fresher | merge rule |
| titleFor: name passthrough, empty → first-question ≤60, never "Untitled" | FR-012 |
| route mapper list: Dify page → records + hasMore/nextCursor (limit, last_id) | FR-013, contracts §1 |
| route mapper messages: query/answer → Message[] pairing, id mapping | FR-005 |
| HistoryState: full transition table; Load more ignored while loadingMore; exhausted hides control | FR-006/013 |
| draft promotion: done(conversationId) → record under today; no promotion without id | FR-014 |
| error mapping: fetch 500/network → history_unavailable; messages fetch fail → messages_unavailable; nothing else thrown | R6, FR-008 |

## Storage & privacy

No new storage. Conversation data stays where it already lives (Dify); the
UI holds records in React state for the session only. Same single-tenant
posture as the existing chat (one app key, one `user` identifier) — this
feature adds no new data exposure.
