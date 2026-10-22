import { describe, expect, it, vi } from "vitest"

import { decideImages, embedOrDegradeImages } from "./image-wait"

function stubImageWith(result: "load" | "error" | "timeout") {
  return class StubImage {
    onload: (() => void) | null = null
    onerror: (() => void) | null = null
    src = ""
    constructor() {
      setTimeout(() => {
        if (result === "load") this.onload?.()
        else if (result === "error") this.onerror?.()
      }, result === "timeout" ? 10_000 : 0)
    }
  }
}

describe("decideImages", () => {
  it("resolves embed for an image that loads", async () => {
    vi.useFakeTimers()
    const Image = stubImageWith("load")
    const p = decideImages(["http://x/a.png"], { ImageCtor: Image as unknown as typeof Image, timeoutMs: 1000 })
    await vi.runAllTimersAsync()
    expect(await p).toEqual([{ url: "http://x/a.png", embed: true }])
    vi.useRealTimers()
  })

  it("resolves link-degrade for an image that errors", async () => {
    vi.useFakeTimers()
    const Image = stubImageWith("error")
    const p = decideImages(["http://x/b.png"], { ImageCtor: Image as unknown as typeof Image, timeoutMs: 1000 })
    await vi.runAllTimersAsync()
    expect(await p).toEqual([{ url: "http://x/b.png", embed: false }])
    vi.useRealTimers()
  })

  it("resolves link-degrade on timeout", async () => {
    vi.useFakeTimers()
    const Image = stubImageWith("timeout")
    const p = decideImages(["http://x/c.png"], { ImageCtor: Image as unknown as typeof Image, timeoutMs: 50 })
    await vi.advanceTimersByTimeAsync(60)
    expect(await p).toEqual([{ url: "http://x/c.png", embed: false }])
    vi.useRealTimers()
  })

  it("decides each image independently", async () => {
    vi.useFakeTimers()
    const results = ["load", "error"] as const
    const Image = class {
      onload: (() => void) | null = null
      onerror: (() => void) | null = null
      src = ""
      constructor() {
        setTimeout(() => {
          if (this.src.includes("good")) this.onload?.()
          else this.onerror?.()
        }, 0)
      }
    }
    const p = decideImages(["http://x/good.png", "http://x/bad.png"], {
      ImageCtor: Image as unknown as typeof Image,
      timeoutMs: 1000,
    })
    await vi.runAllTimersAsync()
    expect(await p).toEqual([
      { url: "http://x/good.png", embed: true },
      { url: "http://x/bad.png", embed: false },
    ])
    void results
    vi.useRealTimers()
  })
})

type StubImg = {
  complete: boolean
  naturalWidth: number
  src: string
  alt: string
  listeners: { load?: () => void; error?: () => void }
  addEventListener(type: "load" | "error", fn: () => void): void
  replacedWith: unknown
  replaceWith(node: unknown): void
}

function makeImg(complete = false, naturalWidth = 0): StubImg {
  const img = {
    complete,
    naturalWidth,
    src: "http://x/pic.png",
    alt: "alt text",
    listeners: {} as StubImg["listeners"],
    replacedWith: null as unknown,
    addEventListener(type: "load" | "error", fn: () => void) {
      img.listeners[type] = fn
    },
    replaceWith(node: unknown) {
      img.replacedWith = node
    },
  } as StubImg
  return img
}

function makeDoc() {
  const created: Record<string, unknown[]> = {}
  return {
    created,
    createElement(tag: string) {
      const node: Record<string, unknown> = { tag }
      created[tag] = [...(created[tag] ?? []), node]
      return node
    },
  }
}

function makeContainer(imgs: StubImg[]) {
  return {
    querySelectorAll: (sel: string) => {
      void sel
      return [...imgs]
    },
  } as unknown as HTMLElement
}

describe("embedOrDegradeImages", () => {
  it("keeps an already-complete image untouched", async () => {
    const doc = makeDoc()
    const img = makeImg(true, 320)
    await embedOrDegradeImages(makeContainer([img]), { doc, timeoutMs: 50 })
    expect(img.replacedWith).toBeNull()
    expect(doc.created["a"]).toBeUndefined()
  })

  it("keeps an image that loads in time", async () => {
    vi.useFakeTimers()
    const doc = makeDoc()
    const img = makeImg()
    const p = embedOrDegradeImages(makeContainer([img]), { doc, timeoutMs: 1000 })
    await vi.advanceTimersByTimeAsync(10)
    img.naturalWidth = 320 // browsers set dimensions on load
    img.listeners.load?.()
    await p
    expect(img.replacedWith).toBeNull()
    vi.useRealTimers()
  })

  it("degrades a failed image to a labeled link and warns (FR-012, R6)", async () => {
    const doc = makeDoc()
    const img = makeImg()
    const warn = vi.spyOn(console, "warn").mockImplementation(() => {})
    const p = embedOrDegradeImages(makeContainer([img]), { doc, timeoutMs: 1000 })
    img.listeners.error?.()
    await p
    expect(img.replacedWith).not.toBeNull()
    expect(doc.created["a"]).toHaveLength(1)
    const link = doc.created["a"][0] as Record<string, unknown>
    expect(link.href).toBe("http://x/pic.png")
    expect(warn).toHaveBeenCalledOnce()
    warn.mockRestore()
  })

  it("degrades a timed-out image to a labeled link", async () => {
    vi.useFakeTimers()
    const doc = makeDoc()
    const img = makeImg()
    const warn = vi.spyOn(console, "warn").mockImplementation(() => {})
    const p = embedOrDegradeImages(makeContainer([img]), { doc, timeoutMs: 50 })
    await vi.advanceTimersByTimeAsync(60)
    await p
    expect(img.replacedWith).not.toBeNull()
    expect(doc.created["a"]).toHaveLength(1)
    warn.mockRestore()
    vi.useRealTimers()
  })
})
