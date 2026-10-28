import { normalizeSelection, type ModelId } from "./options"
import { isBadgeValue, type BadgeValue } from "./badge"

export type ModelStorage = {
  getSelection(conversationId: string): ModelId
  setSelection(conversationId: string, model: ModelId): void
  getBadge(conversationId: string, messageIndex: number): BadgeValue
  setBadge(conversationId: string, messageIndex: number, value: BadgeValue): void
  purgeConversation(conversationId: string): void
}

const SELECTION_PREFIX = "agi-model:selection:"
const BADGE_PREFIX = "agi-model:badge:"

type WebStorage = Pick<Storage, "getItem" | "setItem" | "removeItem">

const NULL_STORAGE: WebStorage = {
  getItem: () => null,
  setItem: () => {},
  removeItem: () => {},
}

/**
 * Browser-side, per-conversation persistence (FR-003/FR-008). All access is
 * guarded: private-mode or corrupted storage degrades to the cloud default
 * instead of throwing (error case 7). Badge keys are message ordinals within
 * the Dify message order — stable across reload/resume; absence = cloud
 * (the backfill rule: every pre-feature reply was cloud-served).
 */
export function createModelStorage(input: WebStorage | null | undefined): ModelStorage {
  const storage: WebStorage = input ?? NULL_STORAGE
  const read = (key: string): unknown => {
    try {
      const raw = storage.getItem(key)
      return raw === null ? undefined : JSON.parse(raw)
    } catch {
      return undefined
    }
  }
  const write = (key: string, value: unknown): void => {
    try {
      storage.setItem(key, JSON.stringify(value))
    } catch {
      // best effort: never break the chat over storage
    }
  }

  return {
    getSelection(conversationId) {
      return normalizeSelection(read(SELECTION_PREFIX + conversationId))
    },
    setSelection(conversationId, model) {
      write(SELECTION_PREFIX + conversationId, model)
    },
    getBadge(conversationId, messageIndex) {
      const map = read(BADGE_PREFIX + conversationId)
      const value = typeof map === "object" && map !== null
        ? (map as Record<string, unknown>)[String(messageIndex)]
        : undefined
      return isBadgeValue(value) ? value : "cloud"
    },
    setBadge(conversationId, messageIndex, value) {
      const raw = read(BADGE_PREFIX + conversationId)
      const map =
        typeof raw === "object" && raw !== null && !Array.isArray(raw)
          ? { ...(raw as Record<string, unknown>) }
          : {}
      map[String(messageIndex)] = value
      write(BADGE_PREFIX + conversationId, map)
    },
    purgeConversation(conversationId) {
      try {
        storage.removeItem(SELECTION_PREFIX + conversationId)
        storage.removeItem(BADGE_PREFIX + conversationId)
      } catch {
        // best effort
      }
    },
  }
}
