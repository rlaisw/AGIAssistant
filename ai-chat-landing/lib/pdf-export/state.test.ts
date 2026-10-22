import { describe, expect, it } from "vitest"

import { ExportError } from "./types"
import { createExportState } from "./state"

describe("createExportState", () => {
  it("starts idle", () => {
    expect(createExportState().get()).toBe("idle")
  })

  it("moves idle -> busy on run and back to idle on success", async () => {
    const s = createExportState()
    const p = s.run(async () => {})
    expect(s.get()).toBe("busy")
    await p
    expect(s.get()).toBe("idle")
  })

  it("moves busy -> error on failure, then back to idle on dismiss", async () => {
    const s = createExportState()
    await s.run(async () => {
      throw new ExportError("render_failed")
    })
    expect(s.get()).toBe("error")
    expect(s.error?.code).toBe("render_failed")
    s.dismiss()
    expect(s.get()).toBe("idle")
    expect(s.error).toBeUndefined()
  })

  it("ignores re-entry while busy", async () => {
    const s = createExportState()
    let inner = 0
    const first = s.run(async () => {
      inner += 1
    })
    const second = s.run(async () => {
      inner += 100
    })
    await Promise.all([first, second])
    expect(inner).toBe(1)
    expect(s.get()).toBe("idle")
  })

  it("wraps non-ExportError failures as render_failed", async () => {
    const s = createExportState()
    await s.run(async () => {
      throw new Error("boom")
    })
    expect(s.get()).toBe("error")
    expect(s.error?.code).toBe("render_failed")
  })
})
