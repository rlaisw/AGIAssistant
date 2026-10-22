import { describe, expect, it } from "vitest"

import { titleFor } from "./titles"

describe("titleFor", () => {
  it("passes a backend name through", () => {
    expect(titleFor("Q3 planning", "anything")).toBe("Q3 planning")
  })

  it("falls back to the first question when the name is empty or missing", () => {
    expect(titleFor("", "How do I deploy the stack?")).toBe("How do I deploy the stack?")
    expect(titleFor(null, "How do I deploy the stack?")).toBe("How do I deploy the stack?")
    expect(titleFor(undefined, "How do I deploy the stack?")).toBe("How do I deploy the stack?")
  })

  it("caps the fallback at 60 chars", () => {
    const name = titleFor("", "x".repeat(200))
    expect(name.length).toBeLessThanOrEqual(60)
  })

  it("never returns 'Untitled' or an empty string", () => {
    expect(titleFor("", "")).not.toBe("Untitled")
    expect(titleFor(null, undefined).length).toBeGreaterThan(0)
    expect(titleFor("   ", "").length).toBeGreaterThan(0)
  })
})
