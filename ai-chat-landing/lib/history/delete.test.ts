import { describe, expect, it, vi } from "vitest"

import { HistoryError } from "./types"
import { createDeleteState } from "./delete"

function fixture(behavior: "ok" | "fail" | never = "ok") {
  const deleteRequest = vi.fn(async (difyId: string) => {
    if (behavior === "fail") throw new Error("network down")
    void difyId
  })
  return { deleteRequest, state: createDeleteState({ deleteRequest }) }
}

describe("createDeleteState", () => {
  it("starts idle; open() shows the menu with Delete", () => {
    const { state } = fixture()
    expect(state.status).toBe("idle")
    state.open()
    expect(state.status).toBe("menu")
  })

  it("confirm() resolves only after deleteRequest and signals done", async () => {
    const { state, deleteRequest } = fixture()
    state.open()
    state.chooseDelete()
    expect(state.status).toBe("confirming")
    const p = state.confirm("a")
    expect(state.status).toBe("in-flight")
    await p
    expect(deleteRequest).toHaveBeenCalledTimes(1)
    expect(state.status).toBe("done")
    expect(state.error).toBeUndefined()
  })

  it("ignores double-confirm while in-flight", async () => {
    let release!: () => void
    const gate = new Promise<void>((r) => (release = r))
    const deleteRequest = vi.fn(async () => {
      await gate
    })
    const state = createDeleteState({ deleteRequest })
    state.open()
    state.chooseDelete()
    const first = state.confirm("dup")
    const second = state.confirm("dup")
    release()
    await Promise.all([first, second])
    expect(deleteRequest).toHaveBeenCalledTimes(1)
    expect(state.status).toBe("done")
  })

  it("failure keeps the row: status error with delete_failed code", async () => {
    const { state } = fixture("fail" as never)
    state.open()
    state.chooseDelete()
    await state.confirm("a")
    expect(state.status).toBe("error")
    expect(state.error).toBeInstanceOf(HistoryError)
    expect(state.error?.code).toBe("delete_failed")
  })

  it("cancel() makes zero backend calls and resets to idle", () => {
    const { state, deleteRequest } = fixture()
    state.open()
    state.chooseDelete()
    state.cancel()
    expect(state.status).toBe("idle")
    expect(deleteRequest).not.toHaveBeenCalled()
  })

  it("maps a HistoryError through unwrapped", async () => {
    const deleteRequest = vi.fn(async () => {
      throw new HistoryError("delete_failed", "custom reason")
    })
    const state = createDeleteState({ deleteRequest })
    state.open()
    state.chooseDelete()
    await state.confirm("a")
    expect(state.error?.message).toBe("custom reason")
  })
})
