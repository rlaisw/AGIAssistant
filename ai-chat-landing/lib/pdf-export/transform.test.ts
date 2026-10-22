import { describe, expect, it } from "vitest"

import type { ExportMessage } from "./types"
import { ExportError } from "./types"
import { buildExportModel } from "./transform"

function msg(partial: Partial<ExportMessage> & Pick<ExportMessage, "id" | "role" | "text">): ExportMessage {
  return { streaming: false, ...partial }
}

describe("buildExportModel", () => {
  it("keeps turns in chronological order with kinds", () => {
    const model = buildExportModel([
      msg({ id: 1, role: "user", text: "first question" }),
      msg({ id: 2, role: "assistant", text: "first answer" }),
      msg({ id: 3, role: "user", text: "second question" }),
    ])
    expect(model.turns.map((t) => t.id)).toEqual([1, 2, 3])
    expect(model.turns.map((t) => t.kind)).toEqual([
      "question",
      "answer",
      "question",
    ])
  })

  it("drops reasoning everywhere (FR-011)", () => {
    const model = buildExportModel([
      msg({ id: 1, role: "user", text: "q" }),
      msg({ id: 2, role: "assistant", text: "a", reasoning: "SECRET ROUTING" }),
    ])
    expect(JSON.stringify(model)).not.toContain("SECRET ROUTING")
  })

  it("maps sources to citations (FR-002)", () => {
    const model = buildExportModel([
      msg({ id: 2, role: "assistant", text: "a", sources: ["handbook.md", "spec.md"] }),
    ])
    expect(model.turns[0].citations).toEqual(["handbook.md", "spec.md"])
  })

  it("folds code/codeName into a fenced block", () => {
    const model = buildExportModel([
      msg({ id: 2, role: "assistant", text: "here", code: "print(1)", codeName: "demo.py" }),
    ])
    expect(model.turns[0].markdown).toContain("```demo.py")
    expect(model.turns[0].markdown).toContain("print(1)")
  })

  it("collects [image: url] markers and markdown images (FR-012)", () => {
    const model = buildExportModel([
      msg({
        id: 2,
        role: "assistant",
        text: "![a diagram](http://x/dia.png)\n[image: http://x/shot.jpg]",
      }),
    ])
    expect(model.turns[0].images).toEqual([
      { url: "http://x/dia.png", alt: "a diagram" },
      { url: "http://x/shot.jpg", alt: "screenshot" },
    ])
  })

  it("includes a streaming turn exactly once, as partial text (FR-009)", () => {
    const model = buildExportModel([
      msg({ id: 1, role: "user", text: "q" }),
      msg({ id: 2, role: "assistant", text: "partial so far", streaming: true }),
      msg({ id: 2, role: "assistant", text: "partial so far", streaming: true }),
    ])
    expect(model.turns.filter((t) => t.id === 2)).toHaveLength(1)
    expect(model.turns[1].markdown).toContain("partial so far")
  })

  it("throws empty_conversation when there are no completed turns (FR-001)", () => {
    expect(() => buildExportModel([])).toThrowError(ExportError)
    try {
      buildExportModel([])
    } catch (e) {
      expect((e as ExportError).code).toBe("empty_conversation")
    }
  })

  it("derives the document title from the first user question", () => {
    const model = buildExportModel([msg({ id: 1, role: "user", text: "How do I deploy the stack?" })])
    expect(model.title).toContain("How do I deploy the stack?")
  })
})
