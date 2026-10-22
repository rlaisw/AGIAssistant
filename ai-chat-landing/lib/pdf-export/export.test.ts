import { describe, expect, it, vi } from "vitest"

import type { ExportMessage } from "./types"
import { pageSliceCount } from "./pagination"
import { exportConversation } from "./export"

function msg(partial: Partial<ExportMessage> & Pick<ExportMessage, "id" | "role" | "text">): ExportMessage {
  return { streaming: false, ...partial }
}

const SAMPLE = [
  msg({ id: 1, role: "user", text: "How do I deploy the stack?" }),
  msg({ id: 2, role: "assistant", text: "Follow **DEPLOY.md** step by step." }),
  msg({ id: 3, role: "user", text: "And the ports?" }),
  msg({ id: 4, role: "assistant", text: "28080 sidecar, 28888 searxng.", code: "ls", codeName: "sh" }),
]

function fakeCanvas(width: number, height: number) {
  return {
    width,
    height,
    toDataURL: () => "data:image/jpeg;base64,ZmFrZQ==",
  }
}

function deps(overrides: Partial<Parameters<typeof exportConversation>[1]> = {}) {
  const saved: Array<{ blob: Blob; filename: string }> = []
  const rasterize = vi.fn(async () => fakeCanvas(1240, 1754 * 2))
  return {
    saved,
    deps: {
      render: (() => ({ tagged: true })) as unknown as () => HTMLElement,
      rasterize,
      save: (blob: Blob, filename: string) => {
        saved.push({ blob, filename })
      },
      ...overrides,
    },
  }
}

describe("pageSliceCount", () => {
  it("slices a canvas into A4-ratio pages, never zero", () => {
    expect(pageSliceCount(1240, 1754)).toBe(1)
    expect(pageSliceCount(1240, 1754 * 2)).toBe(2)
    expect(pageSliceCount(1240, 100)).toBe(1)
  })
})

describe("exportConversation", () => {
  it("throws empty_conversation before any rendering when there are no messages", async () => {
    const { deps: d } = deps()
    await expect(exportConversation([], d)).rejects.toMatchObject({
      code: "empty_conversation",
    })
    expect(d.rasterize).not.toHaveBeenCalled()
  })

  it("resolves and saves a PDF blob with the slug filename", async () => {
    const { saved, deps: d } = deps()
    await exportConversation(SAMPLE, d)
    expect(saved).toHaveLength(1)
    expect(saved[0].filename).toBe("how-do-i-deploy-the-stack.pdf")
    expect(saved[0].blob.size).toBeGreaterThan(100)
  })

  it("maps a rasterizer failure to render_failed", async () => {
    const { deps: d } = deps({
      rasterize: async () => {
        throw new Error("canvas exploded")
      },
    })
    await expect(exportConversation(SAMPLE, d)).rejects.toMatchObject({
      code: "render_failed",
    })
  })

  it("maps a save failure to download_blocked", async () => {
    const { deps: d } = deps({
      save: () => {
        throw new Error("blocked")
      },
    })
    await expect(exportConversation(SAMPLE, d)).rejects.toMatchObject({
      code: "download_blocked",
    })
  })

  it("produces a multi-page PDF when the canvas exceeds one A4 page", async () => {
    const { saved, deps: d } = deps()
    await exportConversation(SAMPLE, d)
    const ab = await saved[0].blob.arrayBuffer()
    const text = Buffer.from(ab).toString("latin1")
    expect(text).toMatch(/\/Type\s*\/Pages/)
    const pageObjs = text.match(/\/Type\s*\/Page[^s]/g) ?? []
    expect(pageObjs.length).toBe(2)
  })
})
