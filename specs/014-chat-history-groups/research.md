# Research: Time-Grouped Chat History

## R1: Bucketing — pure module, injected clock

**Decision**: `ai-chat-landing/lib/history/buckets.ts` — a pure
`groupConversations(records, now?)` that maps conversation records + a clock
value into ordered bucket sections (Today / Yesterday / Previous 7 days /
Last month / Few months ago). Zero dependencies; the clock is injectable so
every boundary is testable with a frozen `now` (Constitution II, SC-004).

**Rationale**: FR-002 pins local calendar-day boundaries; the math is pure
date arithmetic (startOfDay + offset ranges), so no date library is needed
(Constitution III: stdlib first).

**Alternatives**: a date-fns bucket helper (rejected — new dependency for
arithmetic the platform already does); bucketing inside the React component
(rejected — untestable without a browser).

## R2: Backend plumbing — two additive Next.js route handlers

**Decision**: the Chat UI gains two server-side routes that proxy the Dify
service API with the existing `DIFY_API_KEY` (never exposed to the client —
same posture as `/api/chat`, which already sends `user: "ai-chat-ui-user"`):

- `GET /api/conversations?cursor=&limit=` → Dify `GET /conversations`
  (`limit`, `last_id`, `user`). Response mapped to the app's shape:
  `{ conversations: [{difyId, title, lastActivityAt}], hasMore, nextCursor }`.
- `GET /api/conversations/[id]/messages` → Dify
  `GET /conversations/{id}/messages` (`user`, limit 100 first page),
  mapped into the app's existing `Message` shape (query → user turn,
  answer → assistant turn, message id → id).

**Rationale**: FR-011 (backend-backed, survives reload) + FR-005 (resume)
both need server-side data; the app's only existing backend seam is the
route-handler proxy, so this is the reuse ladder (Constitution III), not a
new service (SC-004).

**Alternatives**: calling Dify from the browser (rejected — leaks the app
key); a dedicated history service (rejected — new runtime service,
Constitution III).

## R3: Last-activity timestamp

**Decision**: `lastActivityAt` = Dify conversation `updated_at` falling back
to `created_at` (unix seconds → ISO string at the route boundary). A record
whose timestamps are absent/unparsable degrades to the floor bucket
("Few months ago") with a `console.warn` — never dropped, never a bucket
guess beyond the oldest-safe one (spec edge case; Constitution IV).

## R4: Titles

**Decision**: title = Dify conversation `name`; when empty/missing, derive a
readable fallback from the conversation's first user question, capped at 60
chars, never "Untitled" (FR-012). Derived once at the route boundary so the
sidebar stays dumb.

## R5: Pagination — Load more state machine

**Decision**: first page renders instantly; `hasMore`/`nextCursor` come from
Dify's `has_more`/`last_id`. The sidebar shows a "Load more" control only
while `hasMore` is true; exhausting it removes the control (FR-013). The
fetch-more flow is a small state machine (idle → loading → idle/exhausted)
so re-clicks during a fetch are ignored — the same pattern as the PDF
export's busy guard.

## R6: Error taxonomy (user requirement: explicit error handling)

**Decision**: `HistoryError` with codes:
- `history_unavailable` — the list fetch failed (network/4xx/5xx): sidebar
  shows the honest notice (FR-008/FR-011), "New chat" stays usable.
- `messages_unavailable` — resume fetch failed for one conversation: the
  chat pane shows an honest inline error; the sidebar and other
  conversations stay functional (degradation is per-action, not global).
- `invalid_timestamp` — NOT user-facing: console.warn + floor bucket (R3).
Every fetch failure maps to a code; no raw exceptions cross the module
boundary (mirrors spec 013's ExportError pattern).

## R7: Draft lifecycle (FR-014)

**Decision**: "New chat" creates a session-only draft (current page
behavior); the draft enters the grouped list only when the first message's
`done` stream event returns a `conversationId` — at that moment it becomes a
persisted record under Today. Reload therefore never resurrects empty drafts
and Dify never sees them.

## R8: Test strategy (user requirement: tests-first, Constitution II)

**Decision**: all grouping/lifecycle logic in node-env vitest with frozen
clocks and stubbed fetch seams (no network, no browser — the pattern proven
in specs 013). The API routes are thin mappers tested through injected fetch
stubs; sidebar wiring is covered by the quickstart manual pass.
