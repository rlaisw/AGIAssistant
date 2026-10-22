import { describe, expect, it, vi } from "vitest"

import type { Message } from "./message-type"
import { mapConversationPage, mapMessagesPage } from "./mappers"

const unix = (ms: number) => Math.floor(ms / 1000)

describe("mapConversationPage", () => {
  it("maps a Dify page to records with hasMore/nextCursor", () => {
    const out = mapConversationPage({
      data: [
        { id: "c1", name: "Q3 planning", created_at: unix(1_000_000), updated_at: unix(2_000_000) },
        { id: "c2", name: "", created_at: unix(3_000_000), updated_at: undefined },
      ],
      has_more: true,
      last_id: "c2",
    })
    expect(out.conversations).toEqual([
      { difyId: "c1", title: "Q3 planning", lastActivityAt: 2_000_000 },
      { difyId: "c2", title: "New conversation", lastActivityAt: 3_000_000 },
    ])
    expect(out.hasMore).toBe(true)
    expect(out.nextCursor).toBe("c2") // derived from last record (Dify 1.17 omits last_id)
  })

  it("falls back to created_at and nulls when both timestamps are absent", () => {
    const out = mapConversationPage({
      data: [
        { id: "c1", name: "n", created_at: 5, updated_at: null },
        { id: "c2", name: "n", created_at: null, updated_at: null },
      ],
      has_more: false,
    })
    expect(out.conversations[0].lastActivityAt).toBe(5_000)
    expect(out.conversations[1].lastActivityAt).toBeNull()
    expect(out.hasMore).toBe(false)
    expect(out.nextCursor).toBeNull()
  })

  it("warns once per untitled record and derives a title, never 'Untitled'", () => {
    const warn = vi.spyOn(console, "warn").mockImplementation(() => {})
    const out = mapConversationPage({
      data: [{ id: "c1", name: "  ", created_at: unix(1), updated_at: unix(1) }],
      has_more: false,
    })
    expect(out.conversations[0].title).not.toBe("Untitled")
    expect(out.conversations[0].title.length).toBeGreaterThan(0)
    expect(warn).toHaveBeenCalled()
    warn.mockRestore()
  })
})

describe("mapMessagesPage", () => {
  it("pairs query/answer into Message[] with sequential ids", () => {
    const out = mapMessagesPage({
      data: [
        { id: "m1", query: "hi", answer: "hello", created_at: unix(1) },
        { id: "m2", query: "bye?", answer: "see you", created_at: unix(2) },
      ],
      has_more: false,
    })
    expect(out.messages).toEqual([
      { id: 1, role: "user", text: "hi", streaming: false },
      { id: 2, role: "assistant", text: "hello", streaming: false },
      { id: 3, role: "user", text: "bye?", streaming: false },
      { id: 4, role: "assistant", text: "see you", streaming: false },
    ] satisfies Message[])
    expect(out.hasMore).toBe(false)
  })

  it("maps retriever_resources to deduped sources on the assistant turn", () => {
    const out = mapMessagesPage({
      data: [
        {
          id: "m1",
          query: "q",
          answer: "a",
          created_at: unix(1),
          metadata: {
            retriever_resources: [
              { document_name: "handbook.md" },
              { document_name: "handbook.md" },
              { document_name: "spec.md" },
            ],
          },
        },
      ],
      has_more: true,
    })
    expect(out.messages[1].sources).toEqual(["handbook.md", "spec.md"])
    expect(out.hasMore).toBe(true)
  })

  it("skips records with neither query nor answer", () => {
    const out = mapMessagesPage({
      data: [{ id: "m1", created_at: unix(1) }, { id: "m2", query: "q", answer: "", created_at: unix(2) }],
      has_more: false,
    })
    expect(out.messages.map((m) => m.text)).toEqual(["q"])
    expect(out.messages[0].role).toBe("user")
  })
})
