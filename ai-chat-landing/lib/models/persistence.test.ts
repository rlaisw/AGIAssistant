import { beforeEach, describe, expect, it } from "vitest"
import { createModelStorage } from "./persistence"

function memoryStorage() {
  const m = new Map<string, string>()
  return {
    getItem: (k: string) => m.get(k) ?? null,
    setItem: (k: string, v: string) => void m.set(k, v),
    removeItem: (k: string) => void m.delete(k),
  }
}

describe("model persistence (spec 025, FR-003/FR-005/FR-008)", () => {
  let backing: ReturnType<typeof memoryStorage>
  let storage: ReturnType<typeof createModelStorage>

  beforeEach(() => {
    backing = memoryStorage()
    storage = createModelStorage(backing)
  })

  it("P1 selection round-trip per conversation", () => {
    storage.setSelection("conv-a", "local")
    expect(storage.getSelection("conv-a")).toBe("local")
    storage.setSelection("conv-a", "moonshotai/kimi-k3")
    expect(storage.getSelection("conv-a")).toBe("moonshotai/kimi-k3")
  })

  it("P2 absent selection key resolves to the cloud default, never throws", () => {
    expect(storage.getSelection("missing")).toBe("deepseek/deepseek-v4.1-flash")
  })

  it("P3 corrupt stored values resolve to the cloud default (backfill rule)", () => {
    backing.setItem("agi-model:selection:corrupt", "{not json")
    expect(storage.getSelection("corrupt")).toBe("deepseek/deepseek-v4.1-flash")
    backing.setItem("agi-model:selection:corrupt2", JSON.stringify("gpt-9"))
    expect(storage.getSelection("corrupt2")).toBe("deepseek/deepseek-v4.1-flash")
  })

  it("P4 badge entries are written once and read back by message index", () => {
    storage.setBadge("conv-a", 1, "local")
    storage.setBadge("conv-a", 3, "cloud-fallback")
    expect(storage.getBadge("conv-a", 1)).toBe("local")
    expect(storage.getBadge("conv-a", 3)).toBe("cloud-fallback")
  })

  it("P5 badge map miss resolves to the cloud default (pre-feature backfill)", () => {
    expect(storage.getBadge("conv-a", 0)).toBe("cloud")
    expect(storage.getBadge("missing", 99)).toBe("cloud")
  })

  it("P6 corrupt badge map resolves to the cloud default without data loss for later writes", () => {
    backing.setItem("agi-model:badge:conv-a", "~~corrupt~~")
    expect(storage.getBadge("conv-a", 2)).toBe("cloud")
    storage.setBadge("conv-a", 2, "local")
    expect(storage.getBadge("conv-a", 2)).toBe("local")
  })

  it("P7 purge removes both keys on conversation delete (FR-005 interplay)", () => {
    storage.setSelection("conv-a", "local")
    storage.setBadge("conv-a", 1, "local")
    storage.purgeConversation("conv-a")
    expect(backing.getItem("agi-model:selection:conv-a")).toBeNull()
    expect(backing.getItem("agi-model:badge:conv-a")).toBeNull()
  })

  it("P8 unreadable storage degrades to defaults and never throws (private mode)", () => {
    const throwing = {
      getItem: () => {
        throw new Error("denied")
      },
      setItem: () => {
        throw new Error("denied")
      },
      removeItem: () => {
        throw new Error("denied")
      },
    }
    const s = createModelStorage(throwing)
    expect(s.getSelection("conv-a")).toBe("deepseek/deepseek-v4.1-flash")
    expect(() => s.setSelection("conv-a", "local")).not.toThrow()
    expect(s.getBadge("conv-a", 1)).toBe("cloud")
  })
})
