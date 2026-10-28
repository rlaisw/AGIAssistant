import { describe, expect, it } from "vitest"
import { badgeModel, badgeNote, FALLBACK_NOTE, isBadgeValue, type BadgeValue } from "./badge"

describe("reply model badge (spec 025 FR-008 + spec 026 fallback variants)", () => {
  it("B1 badge values resolve to the producing model", () => {
    expect(badgeModel("local")).toBe("local")
    expect(badgeModel("moonshotai/kimi-k3")).toBe("moonshotai/kimi-k3")
    expect(badgeModel("deepseek/deepseek-v4.1-flash")).toBe("deepseek/deepseek-v4.1-flash")
  })

  it("B2 the fallback variant badges as the model that actually served (spec 026 D6)", () => {
    const v: BadgeValue = "moonshotai/kimi-k3|fallback"
    expect(badgeModel(v)).toBe("moonshotai/kimi-k3")
    expect(badgeModel("deepseek/deepseek-v4.1-flash|fallback")).toBe("deepseek/deepseek-v4.1-flash")
  })

  it("B3 legacy stored badge values resolve to the cloud default", () => {
    expect(badgeModel("cloud")).toBe("deepseek/deepseek-v4.1-flash")
    expect(badgeModel("cloud-fallback")).toBe("deepseek/deepseek-v4.1-flash")
  })

  it("B4 the persistent inline note rides on every fallback variant (FR-004)", () => {
    expect(badgeNote("cloud-fallback")).toBe(FALLBACK_NOTE)
    expect(badgeNote("moonshotai/kimi-k3|fallback")).toBe(FALLBACK_NOTE)
    expect(badgeNote("moonshotai/kimi-k3")).toBeUndefined()
    expect(badgeNote("local")).toBeUndefined()
    expect(FALLBACK_NOTE).toBe("Local model unavailable — answered by the cloud model instead.")
  })

  it("B5 value validation accepts catalog ids and fallback forms only", () => {
    expect(isBadgeValue("local")).toBe(true)
    expect(isBadgeValue("moonshotai/kimi-k3|fallback")).toBe(true)
    expect(isBadgeValue("cloud-fallback")).toBe(true)
    expect(isBadgeValue("gpt-9|fallback")).toBe(false)
    expect(isBadgeValue("moonshotai/kimi-k3|bogus")).toBe(false)
    expect(isBadgeValue(42)).toBe(false)
  })
})
