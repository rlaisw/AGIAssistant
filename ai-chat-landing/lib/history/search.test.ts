import { describe, expect, it } from "vitest"
import { filterHistory, matchesQuery } from "./search"
import { groupConversations } from "./buckets"
import type { ConversationRecord } from "./types"

const rec = (difyId: string, title: string): ConversationRecord => ({
  difyId,
  title,
  lastActivityAt: Date.now(),
})

const records: ConversationRecord[] = [
  rec("a1", "Generate a PowerPoint for create bar chart"),
  rec("a2", "SQL query optimization"),
  rec("a3", "Onboarding email sequence"),
]

const noContent = () => undefined

describe("sidebar search filter (spec 018, contract T1–T8)", () => {
  it("T1 empty query returns all records", () => {
    expect(filterHistory(records, noContent, "")).toHaveLength(3)
  })

  it("T2 whitespace-only query returns all records", () => {
    expect(filterHistory(records, noContent, "   ")).toHaveLength(3)
  })

  it("T3 case-insensitivity: BAR, bar, Bar produce identical sets", () => {
    const upper = filterHistory(records, noContent, "BAR")
    const lower = filterHistory(records, noContent, "bar")
    const mixed = filterHistory(records, noContent, "Bar")
    expect(upper).toEqual(lower)
    expect(lower).toEqual(mixed)
    expect(lower.map((r) => r.difyId)).toEqual(["a1"])
    expect(matchesQuery("Generate a PowerPoint for create bar chart", "BAR")).toBe(true)
  })

  it("T4 content hit: query in a loaded message (not in title) includes the row", () => {
    const getContent = (difyId: string) =>
      difyId === "a2" ? "The leading wildcard forces a full scan of all rows." : undefined
    const result = filterHistory(records, getContent, "wildcard")
    expect(result.map((r) => r.difyId)).toEqual(["a2"])
  })

  it("T5 title-only fallback (the FR-009 honesty boundary): query present only in an unopened row's body does NOT match", () => {
    const result = filterHistory(records, noContent, "habits")
    expect(result).toHaveLength(0)
  })

  it("T6 emoji query matches literally without crashing", () => {
    const withEmoji = [...records, rec("a4", "📊 chart review")]
    expect(filterHistory(withEmoji, noContent, "📊").map((r) => r.difyId)).toEqual(["a4"])
  })

  it("T7 regex metacharacters are literal, not wildcards", () => {
    expect(filterHistory(records, noContent, ".*")).toHaveLength(0)
    expect(filterHistory([...records, rec("a5", "price is 4.*5")], noContent, ".*").map((r) => r.difyId)).toEqual(["a5"])
  })

  it("T8 bucket collapse: matches in only one bucket hide every other bucket", () => {
    const buckets = groupConversations(filterHistory(records, noContent, "powerpoint"))
    expect(buckets).toHaveLength(1)
    expect(buckets[0].items.map((r) => r.difyId)).toEqual(["a1"])
  })
})
