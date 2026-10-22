import { describe, expect, it, vi } from "vitest"

import type { ConversationPage } from "./types"
import { HistoryError } from "./types"
import { createHistoryState } from "./state"

const page = (ids: string[], hasMore: boolean): ConversationPage => ({
  conversations: ids.map((id) => ({ difyId: id, title: id, lastActivityAt: Number(id) })),
  hasMore,
  nextCursor: hasMore ? "cursor-after-" + ids[ids.length - 1] : null,
})

function okFetch(pages: ConversationPage[]) {
  let call = 0
  return vi.fn(async () => pages[Math.min(call++, pages.length - 1)])
}

describe("createHistoryState", () => {
  it("starts idle, loads to ready with records on load()", async () => {
    const fetchPage = okFetch([page(["3", "2", "1"], false)])
    const s = createHistoryState({ fetchPage })
    expect(s.status).toBe("idle")
    const p = s.load()
    expect(s.status).toBe("loading")
    await p
    expect(s.status).toBe("ready")
    expect(s.records.map((r) => r.difyId)).toEqual(["3", "2", "1"])
    expect(s.error).toBeUndefined()
  })

  it("maps a fetch failure to HistoryError(history_unavailable) in error state", async () => {
    const fetchPage = vi.fn(async () => {
      throw new Error("network down")
    })
    const s = createHistoryState({ fetchPage })
    await s.load()
    expect(s.status).toBe("error")
    expect(s.error).toBeInstanceOf(HistoryError)
    expect(s.error?.code).toBe("history_unavailable")
  })

  it("loadMore appends the next page and threads the cursor", async () => {
    const fetchPage = vi.fn(async (cursor?: string) => {
      if (!cursor) return page(["5", "4"], true)
      expect(cursor).toBe("cursor-after-4")
      return page(["3"], false)
    })
    const s = createHistoryState({ fetchPage })
    await s.load()
    expect(s.hasMore).toBe(true)
    await s.loadMore()
    expect(s.records.map((r) => r.difyId)).toEqual(["5", "4", "3"])
    expect(s.hasMore).toBe(false)
    expect(fetchPage).toHaveBeenCalledTimes(2)
  })

  it("ignores loadMore while a loadMore is in flight", async () => {
    let release!: () => void
    const gate = new Promise<void>((r) => (release = r))
    const fetchPage = vi.fn(async (cursor?: string) => {
      if (!cursor) return page(["9"], true)
      await gate
      return page(["8"], false)
    })
    const s = createHistoryState({ fetchPage })
    await s.load()
    const first = s.loadMore()
    const second = s.loadMore()
    release()
    await Promise.all([first, second])
    expect(fetchPage).toHaveBeenCalledTimes(2)
    expect(s.records.map((r) => r.difyId)).toEqual(["9", "8"])
  })

  it("makes no further fetches once exhausted", async () => {
    const fetchPage = okFetch([page(["1"], false)])
    const s = createHistoryState({ fetchPage })
    await s.load()
    await s.loadMore()
    await s.loadMore()
    expect(fetchPage).toHaveBeenCalledTimes(1)
  })

  it("retry from error clears the error and reloads", async () => {
    let fail = true
    const fetchPage = vi.fn(async () => {
      if (fail) throw new Error("down")
      return page(["1"], false)
    })
    const s = createHistoryState({ fetchPage })
    await s.load()
    expect(s.status).toBe("error")
    fail = false
    await s.retry()
    expect(s.status).toBe("ready")
    expect(s.error).toBeUndefined()
  })

  it("preserves a HistoryError as-is (no double wrap)", async () => {
    const fetchPage = vi.fn(async () => {
      throw new HistoryError("history_unavailable", "custom")
    })
    const s = createHistoryState({ fetchPage })
    await s.load()
    expect(s.error?.message).toBe("custom")
  })
})

describe("createHistoryState remove", () => {
  it("drops the record by difyId and leaves others untouched", async () => {
    const fetchPage = vi.fn(async () => ({
      conversations: [
        { difyId: "a", title: "A", lastActivityAt: 3 },
        { difyId: "b", title: "B", lastActivityAt: 2 },
      ],
      hasMore: false,
      nextCursor: null,
    }))
    const s = createHistoryState({ fetchPage })
    await s.load()
    s.remove("a")
    expect(s.records.map((r) => r.difyId)).toEqual(["b"])
  })

  it("is a no-op for a missing difyId", async () => {
    const fetchPage = vi.fn(async () => ({
      conversations: [{ difyId: "a", title: "A", lastActivityAt: 1 }],
      hasMore: false,
      nextCursor: null,
    }))
    const s = createHistoryState({ fetchPage })
    await s.load()
    s.remove("nope")
    expect(s.records.map((r) => r.difyId)).toEqual(["a"])
  })
})
