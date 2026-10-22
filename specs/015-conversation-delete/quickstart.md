# Quickstart: Validate Delete Conversation

Manual end-to-end validation; the unit matrix lives in data-model.md and
runs via `pnpm test` (node env, no network).

## Prerequisites

Stack running with a few conversations of different ages (spec 014 quickstart
S1 state). Create two throwaway chats to delete safely.

## S1 — Delete via "…" menu (US1)

1. Hover a throwaway conversation row; **Expect**: "…" icon appears.
2. Click "…" → menu opens with a destructive Delete item; **Expect**: only
   Delete in v1 (no Rename).
3. Click Delete → inline confirmation ("This cannot be undone.");
   **Expect**: cancel is the safe path.
4. Confirm → row disappears immediately from its bucket (and an emptied
   bucket heading vanishes).
5. Reload → the conversation is still gone (backend-real, SC-001).

## S2 — Safe state transitions (US2)

1. Open a throwaway conversation, send a message, then delete it while a
   reply is still streaming → the pane switches to a fresh empty draft; no
   stream text lands anywhere.
2. Delete another conversation and click Cancel → nothing changes; the
   conversation still opens on click.

## S3 — Error handling (FR-005, R6)

1. Stop Dify (`docker stop docker-nginx-1`), confirm a delete → the row
   STAYS and an inline "Could not delete" error appears.
2. Restart Dify (`docker start docker-nginx-1`) → retry succeeds.

## S4 — Drafts and edge cases

1. "New chat" (no message sent) → **Expect**: no "…" on the draft row.
2. Delete the last remaining conversation → sidebar shows the empty state;
   "New chat" still works.

## S5 — Spec-014 regression (SC-003)

1. After deleting one conversation: buckets regroup correctly, Load more
   still appends, resume works, new drafts promote to Today on first
   message — all spec-014 behaviors unchanged.

## S6 — Automated checks

```bash
cd ai-chat-landing
pnpm test          # vitest: store.remove, route mapper, delete machine
pnpm typecheck && pnpm lint
```

## S7 — PDF export regression (cross-feature)

1. Export a conversation via the header ⬇ button after another was deleted
   → spec 013 behavior unchanged.
