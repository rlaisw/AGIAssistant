# Data Model: Stop Generation Button (Phase 1)

All new state is client-side, in-memory, and session-only. Nothing is persisted to Dify or the proxy; the backend conversation history is untouched by this feature.

## 1. Message (client view model — additive field)

Existing `Message` in `ai-chat-landing/app/page.tsx` (id, role, text, reasoning, sources, code, streaming, …) gains:

| Field | Type | Meaning | Lifecycle |
|---|---|---|---|
| `stopped` | `boolean?` | the turn ended by user stop; drives the "Stopped" caption and suppresses completion affordances | set at finalize; lives in React state only — survives conversation switching, lost on reload (spec clarification: session-only) |

## 2. GenerationState (per in-flight send; single-flight app-wide)

Owned by the `send()` call in `page.tsx`; not a persisted entity.

```text
{
  conversationId   // which conversation the generation belongs to (FR-010 visibility)
  taskId?           // Dify task id, captured from the first stream event that carries it (R2)
  phase            // "thinking" (no answer text yet) | "streaming" (some answer text arrived)
  stopRequested    // true once the user activated Stop (one-way latch; FR-009 no-op guard)
  timedOut         // watchdog abort (existing behavior, orthogonal to Stop)
}
```

*Implementation sync (2026-10-28, convergence I1):* the concrete in-flight record in `page.tsx` (`genRef`) is `{ convId, assistantId, title, model, taskId, isDemo }` — `convId` is this entity's `conversationId` (conversation-scoped so updates survive view switches, FR-010), `phase` is **derived** at stop time from whether answer text or reasoning has arrived (not stored; see contracts §3 `decideStopAction`), and `stopRequested` / `timedOut` live as a component ref and a `send()` closure flag respectively rather than on the record itself.

### State transitions

```text
idle ──send()──▶ thinking ──first chunk──▶ streaming ──┬─done──────────────▶ complete  (existing)
   ▲                                                    ├─stop(with text)──▶ stopped   (caption, FR-007)
   └───────────────── stop(no text) ── thinking ────────┘   = remove assistant placeholder, back to idle
                                                        └─watchdog/error──▶ error    (existing, unchanged)
```

Rules (from the spec):
- `stopRequested` latches; a second activation is a no-op (FR-009).
- Stop during `thinking` with no answer text → no assistant message remains (no empty bubble).
- Stop during `streaming` → partial text + partial reasoning kept and frozen (FR-004), caption shown (FR-007).
- The stop UI action and morph visibility are derived from `busy` + the viewed conversation == the generation's conversation (FR-001/FR-010).

## 3. Stream event (additive — see contracts/stop-generation.md)

| Event | Payload | When |
|---|---|---|
| `task` (NEW) | `{ "type": "task", "taskId": "<dify task id>", "conversationId": "<dify conversation id>" }` | once, first Dify event carrying a `task_id` (conversationId included so the conversation registers in the sidebar mid-generation and a stopped first turn still resumes from history — updated 2026-10-28, additive) |

Existing event types (`chunk`, `reasoning`, `replace`, `sources`, `ping`, `done`, `error`) are unchanged — Constitution I.

## 4. Stop request / response (same-origin route)

| Field | Type | Rules |
|---|---|---|
| request `taskId` | string | required, non-empty; forwarded to the backend stop endpoint with the proxy's end-user identifier |
| response `result` | `"ok" \| "no-task"` | `ok` = backend accepted the halt; `no-task` = backend reports nothing to stop (race with completion) — client treats as success |
| response `error` | string | HTTP 502 only when the backend stop call itself failed — client still stops cleanly and warns (R8 error matrix) |

## Validation rules (from requirements)

- Unknown/absent `taskId` on the client → Stop still aborts the local stream and finalizes; only the backend-halt call is skipped (battery flags a persistent failure, FR-006).
- The caption renders only on a stopped turn that has text; it never renders on complete or error turns.
- No new persisted data anywhere: reload shows the same partial transcript without the caption (durable record, spec FR-007).
