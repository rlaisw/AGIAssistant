import { afterEach, describe, expect, it, vi } from "vitest"
import { GET } from "./route"

const tagsBody = (names: string[]) =>
  ({ ok: true, json: () => Promise.resolve({ models: names.map((name) => ({ name })) }) }) as Response

afterEach(() => {
  vi.unstubAllGlobals()
  vi.restoreAllMocks()
})

describe("GET /api/models (spec 025, contracts §1 — cloud never probed, address never leaked)", () => {
  it("M1 reachable + no-think model present → local available", async () => {
    process.env.OLLAMA_BASE_URL = "http://ollama.test:11434"
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(tagsBody(["qwen3:8b", "qwen3-8b-nothink"]))
    )
    const res = await GET()
    const body = (await res.json()) as { models: { id: string; available: boolean }[] }
    expect(body.models).toEqual([
      { id: "cloud", available: true },
      { id: "local", available: true },
    ])
  })

  it("M2 reachable + model missing → local unavailable", async () => {
    process.env.OLLAMA_BASE_URL = "http://ollama.test:11434"
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(tagsBody(["qwen3:8b"])))
    const body = (await (await GET()).json()) as { models: { id: string; available: boolean }[] }
    expect(body.models.find((m) => m.id === "local")?.available).toBe(false)
  })

  it("M3 connection refused → local unavailable, cloud still true", async () => {
    process.env.OLLAMA_BASE_URL = "http://ollama.test:11434"
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("refused")))
    const body = (await (await GET()).json()) as { models: { id: string; available: boolean }[] }
    expect(body.models).toEqual([
      { id: "cloud", available: true },
      { id: "local", available: false },
    ])
  })

  it("M4 malformed Ollama response → local unavailable", async () => {
    process.env.OLLAMA_BASE_URL = "http://ollama.test:11434"
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: true, json: () => Promise.reject(new Error("bad")) } as Response)
    )
    const body = (await (await GET()).json()) as { models: { id: string; available: boolean }[] }
    expect(body.models.find((m) => m.id === "local")?.available).toBe(false)
  })

  it("M5 the Ollama address never appears in the browser payload (contract §5)", async () => {
    process.env.OLLAMA_BASE_URL = "http://secret-host:11434"
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(tagsBody(["qwen3-8b-nothink"])))
    const raw = await (await GET()).text()
    expect(raw).not.toContain("11434")
    expect(raw).not.toContain("secret-host")
  })
})
