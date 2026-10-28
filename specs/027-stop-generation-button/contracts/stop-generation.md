# Contract: Stop Generation (UI-internal + one proxy route)

The feature touches no MCP tool schemas (Constitution I untouched). Its contracts are: one **additive** event in the existing chat stream, one new same-origin route, and the pure state-machine module the UI consumes.

## 1. Chat stream event (additive to the existing NDJSON contract)

```ts
// app/api/chat/route.ts — StreamEvent union gains one member; existing members byte-identical
type StreamEvent =
  | { type: "chunk" | "reasoning" | "replace" | "reasoning-replace", text: string }
  | { type: "sources", sources: string[] }
  | { type: "task", taskId: string, conversationId?: string }  // NEW: emitted once, first Dify event carrying task_id (conversation_id included so a stopped first turn can still register its conversation — updated during implementation 2026-10-28, additive)
  | { type: "done", conversationId?: string }
  | { type: "error", message: string }
  | { type: "ping" }
```

**Invariants**:
- Existing consumers that switch on known event types are unaffected (unknown-event tolerance is the backward-compatibility rule).
- The `task` event is emitted at most once per stream; if Dify never sends a `task_id`, no `task` event is emitted and the client's Stop still works client-side (backend-halt call skipped, FR-006 honesty preserved).
- Ordering: `task` may arrive any time after the first Dify event; consumers must not assume it precedes the first `chunk`.

## 2. Stop route (new same-origin proxy)

```ts
// app/api/chat/stop/route.ts
POST /api/chat/stop
  body:  { taskId: string }        // non-empty string, ≤ 128 chars
  200 →  { result: "ok" | "no-task" }
  400 →  { error: "taskId is required" }
  502 →  { error: "stop failed: <upstream reason ≤ 200 chars>" }
```

**Invariants**:
- The route forwards to the backend's generation-cancel endpoint using the **same end-user identifier** the chat proxy sends (`ai-chat-ui-user`); the service API key stays server-side (AGENTS.md rule — never reaches the browser).
- `no-task` means the backend reports nothing to stop (completion race) — the client treats it as success, never as an error.
- The route is idempotent: repeated calls for the same task are safe; the backend's verdict is passed through, not second-guessed.
- The route never mutates conversation state; halting is the backend's job.

## 3. Stop state machine (pure, testable — consumed by page.tsx)

```ts
// lib/stop/state.ts (node-env vitest covers every branch)
// what the composer renders — FR-001/FR-010
composerMode({ busy, viewingGeneratingConversation }): "send" | "stop"

// what a Stop activation does — FR-009 no-op latch, R3/R7 finalize
// (hasReasoning added 2026-10-28 during implementation: a reasoning-only turn
// is content, not an empty bubble — removal requires text AND reasoning empty)
decideStopAction({ busy, stopRequested, hasAnswerText, hasReasoning?, generationPhase })
  : "noop"                                  // not generating, or stop already requested
  | "finalize-stopped"                      // has partial text or reasoning → keep it, caption "Stopped"
  | "remove-empty-turn"                     // nothing received at all → no assistant bubble

// message finalization — FR-004/FR-007
finalizeOnStop(message: { text, reasoning, streaming, stopped })
  : { streaming: false, stopped: true } | { remove: true }   // remove only when text AND reasoning are both empty

// backend-halt call decision — FR-006 + error matrix
shouldCallBackendStop({ taskId?: string, demoMode: boolean }): boolean
```

**Invariants**:
- `composerMode` shows "stop" only while the viewed conversation is generating; all other states show the normal send control.
- Once `stopRequested` latches, later activations return `"noop"` — no duplicate state changes, no duplicate backend calls.
- `finalizeOnStop` never blanks already-received text or reasoning.
- The UI abort path (AbortController) and the backend-halt call are independent: a failed backend call never blocks the visible stop (client aborts regardless; failure warns to console and surfaces as an acceptance-battery defect).
- The watchdog-timeout path (`timedOut`) is distinct from user stop: it keeps the existing error UX byte-for-byte.
