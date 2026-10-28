import { describe, expect, it, vi } from "vitest"
import { fetchAvailability } from "./availability"

const jsonResponse = (body: unknown, ok = true) =>
  ({
    ok,
    json: () => Promise.resolve(body),
  }) as Response

describe("availability probe (spec 025, FR-004/SC-002, cloud never probed)", () => {
  it("A1 healthy probe: local available → true", async () => {
    const fetchImpl = vi.fn().mockResolvedValue(
      jsonResponse({ models: [{ id: "cloud", available: true }, { id: "local", available: true }] })
    )
    expect(await fetchAvailability(fetchImpl as unknown as typeof fetch)).toBe(true)
    expect(fetchImpl.mock.calls[0][0]).toBe("/api/models")
  })

  it("A2 local unavailable → false", async () => {
    const fetchImpl = vi.fn().mockResolvedValue(
      jsonResponse({ models: [{ id: "cloud", available: true }, { id: "local", available: false }] })
    )
    expect(await fetchAvailability(fetchImpl as unknown as typeof fetch)).toBe(false)
  })

  it("A3 HTTP failure degrades to false — never guessed", async () => {
    const fetchImpl = vi.fn().mockResolvedValue(jsonResponse({ broken: true }, false))
    expect(await fetchAvailability(fetchImpl as unknown as typeof fetch)).toBe(false)
  })

  it("A4 malformed payload degrades to false", async () => {
    const fetchImpl = vi.fn().mockResolvedValue(jsonResponse({ nope: 1 }))
    expect(await fetchAvailability(fetchImpl as unknown as typeof fetch)).toBe(false)
  })

  it("A5 probe timeout (5 s budget) degrades to false", async () => {
    const fetchImpl = ((_input: unknown, init?: RequestInit) =>
      new Promise<Response>((_resolve, reject) => {
        init?.signal?.addEventListener("abort", () => reject(new DOMException("aborted", "AbortError")))
      })) as unknown as typeof fetch
    expect(await fetchAvailability(fetchImpl, 30)).toBe(false)
  })

  it("A6 network rejection degrades to false", async () => {
    const fetchImpl = vi.fn().mockRejectedValue(new Error("refused"))
    expect(await fetchAvailability(fetchImpl as unknown as typeof fetch)).toBe(false)
  })
})
