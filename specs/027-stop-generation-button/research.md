# Research: Stop Generation Button (Phase 0)

**Date**: 2026-10-28 · All stack facts below were verified live on this host unless marked "verify in task".

## R1 — How to halt the backend generation

- **Decision**: call Dify's documented stop endpoint server-side from a new same-origin proxy route (`POST /api/chat/stop` → `POST {DIFY_API_BASE_URL}/chat-messages/<task_id>/stop`, body `{ "user": "ai-chat-ui-user" }` — the same end-user string the chat proxy already sends).
- **Evidence**: verified live — `POST /v1/chat-messages/fake-task-id/stop` on this host returns HTTP 400 `bad_request` (endpoint resolves and validates), not a 404 unknown-route. The service API key therefore never reaches the client (AGENTS.md rule preserved).
- **Alternatives rejected**: client calls Dify directly (leaks the app key); stop-by-disconnect only (rejected — spec FR-006 requires a *verified* backend halt, SC-005); aborting the proxy's upstream reader without the stop call (same rejection — disconnect alone is unverified).

## R1 addendum (implementation finding, 2026-10-28)

Live probe: Dify's stop endpoint returns `200 {"result":"success"}` even for a valid but unknown task id — the "nothing to stop" case is a success at the HTTP layer, not a 404. The route's 404→`no-task` mapping stays as defensive depth (client treats `ok` and `no-task` identically). Also: message history is served at `GET /v1/messages?conversation_id=…`, not `/conversations/{id}/messages` (same quirk the Chat UI proxy already documents).

## R2 addendum (T001, verified 2026-10-28)

Live capture on the deployed app: stream events carry `task_id` at the top level from the very first `workflow_started` event onward (observed `9b0c579b-5cff-4c97-aacb-5ef9147643d7` on every event of a test generation). The R2 design holds: capture first-seen, emit once.

## R2 — How the client learns the task_id

- **Decision**: `app/api/chat/route.ts` already parses every Dify stream event; it starts capturing `event.task_id` (first-seen) and emits one new additive line-delimited event `{ "type": "task", "taskId": "..." }` to the browser. The client stores it on the in-flight generation.
- **Rationale**: stateless (no server-side session map keyed by request), additive (Constitution I — existing consumers ignore unknown event types), and the ID is available precisely when needed (mid-stream, before stop).
- **Alternatives rejected**: server-side map of request → task_id (stateful proxy, cleanup burden); re-deriving at stop time (impossible once the stream is closed); HTTP header (not visible to the streaming body reader).
- **Verify in task**: confirm Dify 1.18 stream events carry `task_id` on this app (standard for `message`/`agent_message`/`reasoning_chunk` events); capture the first event that has one.

## R3 — Abort semantics in the existing client

- **Finding (bug that this feature supersedes)**: `page.tsx` already has an `AbortController` (`abortRef`) and a 120 s watchdog. Today a user-initiated abort (the only path: unmount cleanup) hits the `AbortError && !timedOut` branch which does `return` — **silently leaving `streaming: true` and `busy: true`**: a stuck UI. This dead-silent path is exactly what the stop feature replaces.
- **Decision**: user Stop reuses the same controller. A `stopRequested` flag distinguishes Stop-aborts from watchdog-timeout aborts (`timedOut`) and normal completion. Stop-abort finalizes the message (caption / empty-removal, see R7) and clears `busy`; the watchdog path keeps its existing error UX unchanged.
- **Alternatives rejected**: a second AbortController for stops (same stream, no benefit); tearing down the fetch without abort (leaks the connection).

## R4 — Composer morph

- **Decision**: the existing composer button is the Stop control. It is already `disabled` while `busy` (send guard `!input.trim() || busy || !!applyingModel`), so the morph is: while the viewed conversation is generating, render Stop (label/aria `Stop`) in place of Send; on click → stop. FR-001's disabled-send requirement is already satisfied by `busy`.
- **Alternatives rejected**: separate Stop button (rejected in spec clarification Q1); disabling the composer entirely (over-broad — typing the next question during generation should stay possible; only *sending* is blocked).

## R5 — Single-flight generation vs. background continuation (FR-010)

- **Finding**: today's model is single-flight app-wide: one `abortRef`, one `busy`, send disabled during any generation. Concurrent multi-conversation generation does not exist.
- **Decision**: keep single-flight. FR-010 is satisfied by *not touching the in-flight generation on conversation switch*: the generation continues and keeps updating its own conversation; the Stop morph is visible only while the generating conversation is viewed (its `busy`/stream state is already scoped to that conversation's messages). Spec FR-001 already disables *sending* during a generation, so "one at a time" is the spec-consistent reading — recorded here as the interpretation of record.
- **Alternatives rejected**: full concurrent per-conversation generations (new cancellation bookkeeping, spec does not require it); abort-on-switch (rejected in spec clarification Q1, pass 2).

## R6 — Demo mode (no DIFY_API_KEY)

- **Finding**: without a key the app streams canned replies via `demoStream` (setInterval).
- **Decision**: Stop works in demo mode too — clear the interval, finalize the message with the caption, clear `busy`. No backend call (there is nothing to cancel). The CDP script gets a demo-mode variant of its stop check.

## R7 — Finalize semantics (caption, empty stop, session-only)

- **Decision**: `Message` gains an in-memory `stopped?: boolean` flag. On stop with partial text → keep text + reasoning, set `stopped` (renders a small "Stopped" caption), `streaming: false`. On stop with **no** answer text (thinking phase) → remove the assistant placeholder message entirely (no empty bubble, per spec assumption), keep the user's question. The flag is session-only client state: it survives conversation switches (FR-010) but not a reload (clarification Q2 pass 2) — the resume/history path never restores it, which is exactly the spec's ruling.
- **Alternatives rejected**: persisted stop state (rejected — clarification Q2; would add per-message data surface); leaving an empty assistant bubble with caption (rejected — spec assumption "no fabricated empty answer").

## R8 — Test strategy (spec input: "create test cases and add error handling")

- **Unit (failing-first)**: pure state machine `lib/stop/state.ts` + vitest: morph visibility per state, double-stop no-op (FR-009), completion-race resolution, empty-stop removal, caption set/skip, demo-mode finalize. Follows `lib/pdf-export/*.test.ts` conventions (node-env, no network).
- **Live UI (CDP)**: `scripts/stop-button-check.mjs` per `wide-layout.mjs` conventions: morph visible during generation, mid-stream stop → partial text + caption + composer ready < 1 s, follow-up send works, thinking-phase stop leaves no bubble, demo-mode variant.
- **Backend halt (battery, SC-005)**: stop a live generation, wait a fixed interval, re-fetch the conversation messages via the history API and assert the answer text has not grown. This makes FR-006 a *verified* behavior.
- **Error-handling matrix** (spec input; also in quickstart): stop-route failure → UI still stops cleanly (client abort) + console warn, battery treats backend-halt failure as a defect; completion race; watchdog-timeout regression (unchanged UX); reload-after-stop (caption gone, partial intact); conversation-switch mid-generation.

## R9 — No sidecar / MCP changes

- **Decision**: the sidecar (`agentic-rag-mcp`) is untouched — stopping is a Dify + UI concern. Constitution I's MCP surface is not involved; the only contract is the additive UI stream event and the new same-origin route.
