import { describe, expect, it, vi } from "vitest"

import type { ConversationRecord } from "./types"
import { bucketOf, groupConversations } from "./buckets"

// frozen "now": Wednesday 2026-10-21 12:00 local
const NOW = new Date(2026, 9, 21, 12, 0, 0)
const MS_PER_DAY = 86_400_000
const startOf = (d: Date) => new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime()

function atDaysAgo(days: number, hour = 10): number {
  return startOf(NOW) - days * MS_PER_DAY + hour * 3_600_000
}

describe("bucketOf", () => {
  it("sorts one record per bucket at a frozen now", () => {
    expect(bucketOf(atDaysAgo(0), NOW)).toBe("today") // 10:00 today
    expect(bucketOf(atDaysAgo(1), NOW)).toBe("yesterday")
    expect(bucketOf(atDaysAgo(5), NOW)).toBe("previous-7-days")
    expect(bucketOf(atDaysAgo(20), NOW)).toBe("last-month")
    expect(bucketOf(atDaysAgo(90), NOW)).toBe("few-months-ago")
  })

  it("keeps 00:01 and 23:59 of the same local day in Today (local time)", () => {
    const midnight = startOf(NOW) + 60_000
    const lateNight = startOf(NOW) + 23 * 3_600_000 + 59 * 60_000
    expect(bucketOf(midnight, NOW)).toBe("today")
    expect(bucketOf(lateNight, NOW)).toBe("today")
  })

  it("puts exact midnight boundaries into the older bucket", () => {
    const t = startOf(NOW)
    expect(bucketOf(t - 1, NOW)).toBe("yesterday") // 1ms before today's midnight
    expect(bucketOf(t, NOW)).toBe("today")
    expect(bucketOf(t - MS_PER_DAY, NOW)).toBe("yesterday") // yesterday midnight = still yesterday (start, inclusive)
    expect(bucketOf(t - 8 * MS_PER_DAY, NOW)).toBe("previous-7-days")
    expect(bucketOf(t - 38 * MS_PER_DAY, NOW)).toBe("last-month")
    expect(bucketOf(t - 38 * MS_PER_DAY - 1, NOW)).toBe("few-months-ago")
  })

  it("degrades null/NaN timestamps to the floor bucket", () => {
    expect(bucketOf(null, NOW)).toBe("few-months-ago")
    expect(bucketOf(Number.NaN, NOW)).toBe("few-months-ago")
  })
})

function rec(difyId: string, lastActivityAt: number | null, title = difyId): ConversationRecord {
  return { difyId, title, lastActivityAt }
}

describe("groupConversations", () => {
  it("omits empty buckets and keeps the fixed section order", () => {
    const out = groupConversations([rec("a", atDaysAgo(0)), rec("b", atDaysAgo(90))], NOW)
    expect(out.map((b) => b.id)).toEqual(["today", "few-months-ago"])
  })

  it("orders within a bucket most-recent-first; null timestamps land in the floor bucket last", () => {
    const out = groupConversations(
      [rec("old", atDaysAgo(0, 8)), rec("null", null), rec("new", atDaysAgo(0, 11))],
      NOW
    )
    expect(out[0].items.map((i) => i.difyId)).toEqual(["new", "old"])
    const floor = out.find((b) => b.id === "few-months-ago")
    expect(floor?.items.map((i) => i.difyId)).toEqual(["null"])
  })

  it("dedupes by difyId keeping the fresher record", () => {
    const out = groupConversations(
      [rec("dup", atDaysAgo(30)), rec("dup", atDaysAgo(0))],
      NOW
    )
    const all = out.flatMap((b) => b.items)
    expect(all).toHaveLength(1)
    expect(all[0].lastActivityAt).toBe(atDaysAgo(0))
  })

  it("never mutates input and never throws on bad timestamps", () => {
    const input = [rec("x", Number.NaN), rec("y", -1)]
    const snapshot = JSON.stringify(input)
    const warn = vi.spyOn(console, "warn").mockImplementation(() => {})
    expect(() => groupConversations(input, NOW)).not.toThrow()
    expect(JSON.stringify(input)).toBe(snapshot)
    warn.mockRestore()
  })
})
