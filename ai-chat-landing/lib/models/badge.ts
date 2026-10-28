import { DEFAULT_MODEL_ID, isModelId, type ModelId } from "./options"

/**
 * Per-reply model provenance (FR-008). A `|fallback` suffix marks the FR-004
 * reset: Local was selected but unavailable, and the reply was actually
 * served by the globally configured cloud model — the badge names the model
 * that served, the note persists in the stream (spec 026, research D6).
 */
export type BadgeValue = ModelId | "cloud" | "cloud-fallback" | `${ModelId}|fallback`

export const FALLBACK_NOTE =
  "Local model unavailable — answered by the cloud model instead."

export function isBadgeValue(value: unknown): value is BadgeValue {
  if (typeof value !== "string") return false
  if (value === "cloud" || value === "cloud-fallback") return true
  const [id, suffix] = value.split("|")
  return isModelId(id) && (suffix === undefined || suffix === "fallback")
}

export function badgeModel(value: BadgeValue): ModelId {
  const [id, suffix] = value.split("|")
  if (isModelId(id)) return id
  if (suffix === undefined && isModelId(value)) return value
  return DEFAULT_MODEL_ID
}

export function badgeNote(value: BadgeValue): string | undefined {
  return value === "cloud-fallback" || value.endsWith("|fallback")
    ? FALLBACK_NOTE
    : undefined
}
