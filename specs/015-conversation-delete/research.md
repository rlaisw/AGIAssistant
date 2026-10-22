# Research: Delete Conversation

## R1: Backend delete — reuse the spec-014 proxy pattern

**Decision**: one additive route handler, `DELETE /api/conversations/[id]`,
proxying Dify's service-API `DELETE /conversations/{conversation_id}` with
`user: "ai-chat-ui-user"` and the server-side `DIFY_API_KEY` — identical
posture to `/api/chat` and spec 014's two GET routes.

**Rationale**: FR-003 requires backend-real deletion; the key never reaches
the client; the pattern is proven twice already. Verified against the live
Dify 1.17 (`/app/api/controllers/service_api/app/conversation.py` exposes
`delete` on `/conversations/<uuid:conversation_id>`).

**Alternatives**: client-side Dify call (rejected — key leak); soft-hide only
(rejected — violates FR-003, resurrects on reload).

## R2: Menu component — reuse the app's existing Base UI dropdown

**Decision**: the per-row "…" menu reuses the app's existing
`DropdownMenu` components (same family as the header's "Conversation
options" menu), with a destructive-styled Delete item. v1 contains Delete
only, structured so Rename can be added later as a sibling (Clarification
2026-10-21).

**Rationale**: zero new dependencies, visual consistency, keyboard
accessibility for free (FR-007).

## R3: Confirmation — inline in the dropdown, not a modal

**Decision**: choosing Delete swaps the menu content to a small
confirmation ("Delete this chat? This cannot be undone." + Delete/Cancel)
inside the same dropdown, with the destructive item disabled while the
request is in flight.

**Rationale**: a modal for a one-line confirm is heavyweight; the inline
pattern keeps context (the row is right there), cancel is the visually
primary path, and the in-flight disable satisfies FR-006 without extra
state plumbing. The dropdown close-on-outside-click gives cancel-by-default
semantics for free.

**Alternatives**: full-screen AlertDialog (rejected — heavyweight);
"click Delete twice" (rejected — ambiguous, error-prone).

## R4: Sidebar store removal — extend spec 014's history state

**Decision**: add a `remove(difyId)` seam to `createHistoryState` that
removes the record from the in-memory store (re-render regroups buckets
instantly), and delete from the backend FIRST: the row only disappears
when the backend call succeeds (FR-005 — a failure keeps the row).

**Rationale**: spec 014's `upsert`/`touch` already mutate the store the
same way; `remove` completes the set. Backend-first ordering guarantees the
honesty invariant: local state never disagrees with the backend.

**Alternatives**: optimistic removal with rollback (rejected — honest-failure
path requires keeping the row anyway, and rollback UI is worse than a
brief in-flight disable).

## R5: Active-conversation deletion + mid-stream abort

**Decision**: deleting the conversation that is open in the chat pane calls
the existing abort path (`abortRef.current?.abort()` — the watchdog/stream
machinery already in `send()`) before switching `activeId` to a fresh draft
via the existing `newChat()` flow. US2/AC1 + the mid-stream edge case.

**Rationale**: reuses the abort mechanism verbatim; no stream writes can
land in a removed conversation; the pane never shows a dangling reference.

## R6: Error taxonomy (user requirement: explicit error handling)

**Decision**: extend spec 014's `HistoryError` family with
`delete_failed` (backend 4xx/5xx/network). Row stays; the dropdown shows a
brief inline error and closes. Console gets the reason; the user-facing
copy is honest ("Could not delete — please try again"). No local-only
removal ever (Constitution IV).

## R7: Test strategy (user requirement: tests-first, Constitution II)

**Decision**: node-env vitest with the seams proven in specs 013/014:
`remove` store seam, route mapper (Dify status → success/`delete_failed`),
and the delete-state machine (idle → confirming → in-flight → done/failed,
double-submit guard). Route tested through an injected fetch stub; UI
wiring via the quickstart manual pass. No network, no browser.
