import { describe, expect, it } from "vitest"

import { slugifyFilename } from "./slugify"

describe("slugifyFilename", () => {
  it("slugs a plain question", () => {
    expect(slugifyFilename("How do I deploy the stack?")).toBe(
      "how-do-i-deploy-the-stack.pdf"
    )
  })

  it("strips punctuation and collapses separator runs", () => {
    expect(slugifyFilename("What's new:  -- v2 (2026)!")).toBe("whats-new-v2-2026.pdf")
  })

  it("caps the slug at 40 characters", () => {
    const long = "a".repeat(80)
    const name = slugifyFilename(long)
    expect(name.endsWith(".pdf")).toBe(true)
    expect(name.length).toBe(44) // 40 + ".pdf"
  })

  it("degrades unicode/emoji to hyphens without crashing", () => {
    const name = slugifyFilename("計劃 plan 🚀 launch")
    expect(name).toMatch(/^[a-z0-9-]+\.pdf$/)
  })

  it("falls back to a timestamp when the question is empty or slugless", () => {
    const name = slugifyFilename("")
    expect(name).toMatch(/^chat-\d{8}-\d{6}\.pdf$/)
    expect(slugifyFilename("???")).toMatch(/^chat-\d{8}-\d{6}\.pdf$/)
  })

  it("falls back to a timestamp when no question is given", () => {
    expect(slugifyFilename(undefined)).toMatch(/^chat-\d{8}-\d{6}\.pdf$/)
  })
})
