import type { BucketedConversations, BucketId, ConversationRecord } from "./types"
import { BUCKET_LABELS, BUCKET_ORDER } from "./types"

const MS_PER_DAY = 86_400_000

/**
 * Local calendar-day bucketing per FR-002:
 * today = since local midnight; yesterday = [−1d, 0) midnights;
 * previous-7-days = [−8d, −1d); last-month = [−38d, −8d);
 * few-months-ago = older (floor, FR-007).
 */
export function bucketOf(lastActivityAt: number | null, now: Date): BucketId {
  if (lastActivityAt === null || !Number.isFinite(lastActivityAt)) {
    console.warn("[history] invalid timestamp; grouping into the floor bucket:", lastActivityAt)
    return "few-months-ago"
  }
  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime()
  const age = startOfToday - lastActivityAt
  if (age <= 0) return "today"
  if (age <= MS_PER_DAY) return "yesterday"
  if (age <= 8 * MS_PER_DAY) return "previous-7-days"
  if (age <= 38 * MS_PER_DAY) return "last-month"
  return "few-months-ago"
}

export function groupConversations(
  records: ConversationRecord[],
  now: Date = new Date()
): BucketedConversations {
  // dedupe by difyId keeping the fresher record; session beats fetched
  const freshest = new Map<string, ConversationRecord>()
  for (const r of records) {
    const prev = freshest.get(r.difyId)
    const a = prev?.lastActivityAt ?? Number.NEGATIVE_INFINITY
    const b = r.lastActivityAt ?? Number.NEGATIVE_INFINITY
    if (!prev || b >= a) freshest.set(r.difyId, r)
  }

  const byBucket = new Map<BucketId, ConversationRecord[]>()
  for (const r of [...freshest.values()].sort(cmpRecords)) {
    const id = bucketOf(r.lastActivityAt, now)
    const list = byBucket.get(id) ?? []
    list.push(r)
    byBucket.set(id, list)
  }

  return BUCKET_ORDER.filter((id) => byBucket.has(id)).map((id) => ({
    id,
    label: BUCKET_LABELS[id],
    items: byBucket.get(id)!,
  }))
}

/** most-recent-first; nulls last (stable on ties) */
function cmpRecords(a: ConversationRecord, b: ConversationRecord): number {
  const av = a.lastActivityAt
  const bv = b.lastActivityAt
  if (av === null && bv === null) return 0
  if (av === null) return 1
  if (bv === null) return -1
  return bv - av
}
