import type { ConversationRecord } from "./types"

/**
 * Case-insensitive literal substring match (spec 018). No regex — metacharacters
 * are always literal. Caller trims the query first.
 */
export function matchesQuery(text: string, query: string): boolean {
  return text.toLowerCase().includes(query.toLowerCase())
}

/**
 * Filter sidebar records: title match for every row, plus content match only
 * for rows whose conversation messages are currently loaded (getContent returns
 * text). Unopened rows get `undefined` → title-only (the FR-009 boundary).
 */
export function filterHistory(
  records: ConversationRecord[],
  getContent: (difyId: string) => string | undefined,
  query: string
): ConversationRecord[] {
  const q = query.trim()
  if (!q) return records
  return records.filter((record) => {
    if (matchesQuery(record.title, q)) return true
    const content = getContent(record.difyId)
    return content !== undefined && matchesQuery(content, q)
  })
}
