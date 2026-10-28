/**
 * Stop-generation state machine (spec 027) — pure functions only.
 * The wiring in app/page.tsx owns effects (abort, fetch, DOM); every
 * decision here is synchronous and side-effect free, per
 * specs/027-stop-generation-button/contracts/stop-generation.md §3.
 */

export type ComposerMode = "send" | "stop"

export type StopAction = "noop" | "finalize-stopped" | "remove-empty-turn"

export type StopMessage = {
  text: string
  reasoning?: string
  streaming: boolean
  stopped?: boolean
}

/** FR-001/FR-010: Stop replaces Send only while the viewed conversation is generating. */
export function composerMode(input: {
  busy: boolean
  viewingGeneratingConversation: boolean
}): ComposerMode {
  return input.busy && input.viewingGeneratingConversation ? "stop" : "send"
}

/**
 * FR-009 latch + race + empty-stop rules. `noop` when nothing is running
 * (completion race — done already processed) or stop already latched
 * (double-click). Thinking-phase or text-less stops remove the empty turn;
 * mid-stream stops finalize the partial answer.
 */
export function decideStopAction(input: {
  busy: boolean
  stopRequested: boolean
  hasAnswerText: boolean
  hasReasoning?: boolean
  generationPhase?: "thinking" | "streaming"
}): StopAction {
  if (!input.busy || input.stopRequested) return "noop"
  // a reasoning-only turn still has content — remove only a truly empty one
  if (
    (input.generationPhase === "thinking" || !input.hasAnswerText) &&
    !input.hasReasoning
  )
    return "remove-empty-turn"
  return "finalize-stopped"
}

/**
 * FR-004/FR-007: finalization patch. Empty turns are flagged for removal
 * (no fabricated empty bubble); everything else keeps its text/reasoning —
 * the caller applies this patch to the in-memory message only (the caption
 * is session-only; nothing here persists).
 */
export function finalizeOnStop(
  message: StopMessage
): { streaming: false; stopped: true } | { remove: true } {
  // remove only a turn with NOTHING received — reasoning alone is content (FR-004)
  if (!message.text.trim() && !message.reasoning?.trim()) return { remove: true }
  return { streaming: false, stopped: true }
}

/** FR-006: only a live-mode generation with a known task id can be halted server-side. */
export function shouldCallBackendStop(input: { taskId?: string; demoMode: boolean }): boolean {
  return !input.demoMode && typeof input.taskId === "string" && input.taskId.length > 0
}
