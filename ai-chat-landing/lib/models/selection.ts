import { DEFAULT_MODEL_ID, normalizeSelection, type ModelId } from "./options"

export type SelectionEvent =
  | { type: "user-select"; modelId: ModelId }
  | { type: "reset-to-cloud"; reason: "local-unavailable" | "local-stream-error" }

/**
 * Single-select state machine (FR-001/FR-002/FR-004): the selection is one
 * value by construction — never both, never neither. The FR-004 reset rule
 * (clarify decision, Option A) is the only system-initiated change: a local
 * selection that cannot serve resets to the cloud default and never
 * auto-resumes.
 */
export function nextSelection(current: ModelId, event: SelectionEvent): ModelId {
  if (event.type === "user-select") return event.modelId
  if (current === "local") return DEFAULT_MODEL_ID
  return normalizeSelection(current)
}
