import { describe, expect, it, vi } from "vitest"

import { needsProxy, proxySrc, rewriteCrossOriginImages } from "./image-proxy"
import { embedOrDegradeImages } from "./image-wait"

const ORIGIN = "http://localhost:3000"

describe("needsProxy", () => {
  it("flags cross-origin http(s) images", () => {
    expect(needsProxy("https://learn.microsoft.com/a.png", ORIGIN)).toBe(true)
    expect(needsProxy("http://localhost:28080/img/x.png", ORIGIN)).toBe(true)
  })

  it("passes same-origin, data: and unparseable sources", () => {
    expect(needsProxy(`${ORIGIN}/local.png`, ORIGIN)).toBe(false)
    expect(needsProxy("data:image/png;base64,AAAA", ORIGIN)).toBe(false)
    expect(needsProxy("not a url", ORIGIN)).toBe(false)
  })
})

describe("proxySrc", () => {
  it("builds an encoded same-origin proxy path", () => {
    expect(proxySrc("https://a.b/c d.png")).toBe(
      "/api/image-proxy?url=" + encodeURIComponent("https://a.b/c d.png")
    )
  })
})

type StubImg = {
  src: string
  alt: string
  attrs: Record<string, string>
  complete: boolean
  naturalWidth: number
  listeners: { load?: () => void; error?: () => void }
  setAttribute(k: string, v: string): void
  getAttribute(k: string): string | null
  addEventListener(type: "load" | "error", fn: () => void): void
  replacedWith: unknown
  replaceWith(node: unknown): void
}

function makeImg(src: string): StubImg {
  const img: StubImg = {
    src,
    alt: "shot",
    attrs: {},
    complete: false,
    naturalWidth: 0,
    listeners: {},
    setAttribute(k, v) {
      img.attrs[k] = v
    },
    getAttribute(k) {
      return img.attrs[k] ?? null
    },
    addEventListener(type, fn) {
      img.listeners[type] = fn
    },
    replacedWith: null,
    replaceWith(node: unknown) {
      img.replacedWith = node
    },
  }
  return img
}

function makeContainer(imgs: StubImg[]) {
  return { querySelectorAll: () => [...imgs] } as unknown as HTMLElement
}

describe("rewriteCrossOriginImages", () => {
  it("rewrites only cross-origin images and keeps the original URL", () => {
    const external = makeImg("https://uit.stanford.edu/step3-2_0.png")
    const local = makeImg("http://localhost:3000/local.png")
    rewriteCrossOriginImages(makeContainer([external, local]), ORIGIN)
    expect(external.src).toBe(
      "/api/image-proxy?url=" + encodeURIComponent("https://uit.stanford.edu/step3-2_0.png")
    )
    expect(external.attrs["data-orig-src"]).toBe("https://uit.stanford.edu/step3-2_0.png")
    expect(local.src).toBe("http://localhost:3000/local.png")
    expect(local.attrs["data-orig-src"]).toBeUndefined()
  })

  it("degrades a rewritten image to a link with the ORIGINAL url", async () => {
    const img = makeImg("https://uit.stanford.edu/step3-2_0.png")
    rewriteCrossOriginImages(makeContainer([img]), ORIGIN)
    const created: Record<string, unknown>[] = []
    const doc = {
      createElement: (tag: string) => {
        const node: Record<string, unknown> = { tag }
        created.push(node)
        return node
      },
    }
    const warn = vi.spyOn(console, "warn").mockImplementation(() => {})
    const p = embedOrDegradeImages(makeContainer([img]), { doc, timeoutMs: 1000 })
    img.listeners.error?.()
    await p
    expect(created).toHaveLength(1)
    expect(created[0].href).toBe("https://uit.stanford.edu/step3-2_0.png")
    warn.mockRestore()
  })
})
