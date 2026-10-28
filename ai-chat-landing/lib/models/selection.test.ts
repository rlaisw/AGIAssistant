import { describe, expect, it } from "vitest"
import { DEFAULT_MODEL_ID, normalizeSelection } from "./options"
import { nextSelection } from "./selection"

describe("model selection state machine (spec 025, FR-001/FR-002/FR-004)", () => {
  it("S1 single-select: selecting a model leaves exactly that model active", () => {
    expect(nextSelection("deepseek/deepseek-v4.1-flash", { type: "user-select", modelId: "local" })).toBe("local")
    expect(nextSelection("local", { type: "user-select", modelId: "moonshotai/kimi-k3" })).toBe("moonshotai/kimi-k3")
    expect(nextSelection("moonshotai/kimi-k3", { type: "user-select", modelId: "z-ai/glm-5.3-flash" })).toBe("z-ai/glm-5.3-flash")
  })

  it("S2 re-selecting the active model is a no-op — never none active", () => {
    expect(nextSelection("local", { type: "user-select", modelId: "local" })).toBe("local")
    expect(nextSelection("qwen/qwen3.8-flash", { type: "user-select", modelId: "qwen/qwen3.8-flash" })).toBe("qwen/qwen3.8-flash")
  })

  it("S3 FR-004 reset: an unavailable local selection resets to the cloud default", () => {
    expect(
      nextSelection("local", { type: "reset-to-cloud", reason: "local-unavailable" })
    ).toBe("deepseek/deepseek-v4.1-flash")
    expect(
      nextSelection("local", { type: "reset-to-cloud", reason: "local-stream-error" })
    ).toBe("deepseek/deepseek-v4.1-flash")
  })

  it("S4 FR-004 reset on an already-cloud selection is a no-op", () => {
    expect(
      nextSelection("deepseek/deepseek-v4.1-flash", { type: "reset-to-cloud", reason: "local-stream-error" })
    ).toBe("deepseek/deepseek-v4.1-flash")
  })

  it("S5 new conversations, legacy, and unknown values resolve to the cloud default", () => {
    expect(DEFAULT_MODEL_ID).toBe("deepseek/deepseek-v4.1-flash")
    expect(normalizeSelection(undefined)).toBe("deepseek/deepseek-v4.1-flash")
    expect(normalizeSelection(null)).toBe("deepseek/deepseek-v4.1-flash")
    expect(normalizeSelection("gpt-9")).toBe("deepseek/deepseek-v4.1-flash")
    expect(normalizeSelection("local")).toBe("local")
    expect(normalizeSelection("moonshotai/kimi-k3")).toBe("moonshotai/kimi-k3")
    // legacy persisted value from the one-cloud-model era
    expect(normalizeSelection("cloud")).toBe("deepseek/deepseek-v4.1-flash")
  })
})
