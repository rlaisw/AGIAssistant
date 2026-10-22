# Quickstart: Validate Time-Grouped Chat History

End-to-end manual validation; the unit matrix lives in data-model.md and
runs via `pnpm test` (node env, no network).

## Prerequisites

Stack running (Dify + sidecar + `pnpm dev` on :3000) with at least a few
past conversations on the Dify app (send a couple of chats now, and use
the `verify` battery's chats as older history if available).

## S1 — Buckets visible (US1)

1. Open http://localhost:3000 and reload.
   **Expect**: sidebar loads history from the backend (brief loading state),
   conversations grouped under Today / Yesterday / Previous 7 days / Last
   month / Few months ago — only non-empty headings shown; within a group
   most-recent first (SC-001/SC-003 spot check).

## S2 — Resume (US2)

1. Click a conversation under an older bucket.
   **Expect**: its message history loads in the chat pane (question +
   answer pairs, sources shown as in live chats).
2. Send a follow-up message.
   **Expect**: the reply arrives in that conversation and the sidebar entry
   jumps to Today without a reload (FR-005/FR-006).

## S3 — Draft lifecycle (FR-014)

1. Click "New chat" and reload before typing anything.
   **Expect**: no empty conversation appears in history after reload.
2. Send one message in the new chat.
   **Expect**: it now appears under Today and survives another reload.

## S4 — Load more (FR-013)

1. With more conversations than one backend page (or after several chat
   sessions), scroll the sidebar to the bottom.
   **Expect**: a "Load more" control; each click appends older
   conversations; the control disappears when the last page is exhausted.

## S5 — Error handling (FR-008/FR-011)

1. Stop the Dify nginx container (`docker stop docker-nginx-1`), reload the
   app.
   **Expect**: an honest "history unavailable" notice in the sidebar; "New
   chat" still works and new conversations still send once Dify is back
   (`docker start docker-nginx-1`).
2. Resume any conversation while Dify is up: chat-pane errors are
   per-action only, the sidebar never blanks.

## S6 — Automated checks

```bash
cd ai-chat-landing
pnpm test          # vitest: bucket math, boundaries, state machine, mappers
pnpm typecheck && pnpm lint
```
**Expect**: all green; no network access from tests (fetch seams stubbed).

## S7 — PDF export regression (cross-feature)

1. Resume an old conversation and click the ⬇ header export.
   **Expect**: the loaded history exports as before — grouping changes
   nothing about the export path (spec 013 contract intact).
