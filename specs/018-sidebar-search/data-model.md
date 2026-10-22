# Data Model: Sidebar Full-Text Search

No persistence, no new entities — one derived filter over existing types.

## Filter signature (pure, `lib/history/search.ts`)

```text
matchesQuery(text: string, query: string): boolean
  → text.toLowerCase().includes(query.toLowerCase())
  → query is trimmed first; empty/whitespace query ⇒ caller skips filtering

filterHistory(records, getContent, query): ConversationRecord[]
  records:    ConversationRecord[]  (backend rows — titles are always searched)
  getContent: (difyId) => string | undefined
              → concatenated message texts for rows whose conversation is
                currently loaded (open / previously-opened this session /
                active after first upsert); undefined for unopened rows
  query:      trimmed user query
  → keeps a record when matchesQuery(title) OR (content && matchesQuery(content))

Result feeds the existing groupConversations(records) — empty buckets
collapse by construction.
```

## Query state (session-local, `page.tsx`)

```text
query:        string   — raw input value (controlled Input)
debouncedQuery: string — 200 ms debounced mirror driving the memo
clear():      () => setQuery("")   — × control and Escape
```

## States (from research R5)

| history.status | query | Rendered |
|---|---|---|
| loading | any | skeleton (existing) |
| error | any | error + retry (existing) |
| ready | empty/whitespace | full grouped list |
| ready | non-empty, matches > 0 | filtered grouped list (empty buckets hidden) |
| ready | non-empty, matches = 0 | "No conversations match ‹query›" |
