import { describe, expect, it } from "vitest"

import { composerMode, decideStopAction, finalizeOnStop, shouldCallBackendStop } from "./state"

// quickstart A1–A7: the pure stop state machine per contracts/stop-generation.md §3

describe("composerMode (A1 — FR-001/FR-010 visibility)", () => {
  it("shows stop only while viewing the generating conversation", () => {
    expect(composerMode({ busy: true, viewingGeneratingConversation: true })).toBe("stop")
  })

  it("shows send while busy but viewing another conversation", () => {
    expect(composerMode({ busy: true, viewingGeneratingConversation: false })).toBe("send")
  })

  it("shows send when idle", () => {
    expect(composerMode({ busy: false, viewingGeneratingConversation: true })).toBe("send")
  })
})

describe("decideStopAction (A2–A4 — FR-009 latch, completion race, empty stop)", () => {
  it("no-ops when no generation is running (A3 — completion race: done already processed)", () => {
    expect(decideStopAction({ busy: false, stopRequested: false, hasAnswerText: true })).toBe("noop")
  })

  it("no-ops when stop was already requested (A2 — double-click guard, FR-009)", () => {
    expect(decideStopAction({ busy: true, stopRequested: true, hasAnswerText: true })).toBe("noop")
  })

  it("removes the empty turn on a thinking-phase stop (A4 — no empty bubble)", () => {
    expect(
      decideStopAction({ busy: true, stopRequested: false, hasAnswerText: false, generationPhase: "thinking" })
    ).toBe("remove-empty-turn")
  })

  it("finalizes a mid-stream stop (A5)", () => {
    expect(
      decideStopAction({ busy: true, stopRequested: false, hasAnswerText: true, generationPhase: "streaming" })
    ).toBe("finalize-stopped")
  })
})

describe("finalizeOnStop (A5/A6 — FR-004/FR-007)", () => {
  it("keeps partial text: patch only flips streaming and sets stopped", () => {
    const patch = finalizeOnStop({ text: "partial answer", reasoning: "thinking…", streaming: true })
    expect(patch).toEqual({ streaming: false, stopped: true })
  })

  it("flags an empty (thinking-phase) message for removal", () => {
    expect(finalizeOnStop({ text: "   ", streaming: true })).toEqual({ remove: true })
  })

  it("keeps a reasoning-only turn — reasoning is content, not an empty bubble", () => {
    expect(finalizeOnStop({ text: "", reasoning: "partial reasoning…", streaming: true })).toEqual({
      streaming: false,
      stopped: true,
    })
  })

  it("removes a reasoning-only turn only when stop has nothing received at all", () => {
    expect(decideStopAction({ busy: true, stopRequested: false, hasAnswerText: false, hasReasoning: true })).toBe(
      "finalize-stopped"
    )
  })

  it("is pure in-memory derivation: the patch carries no persistence keys (A6 — session-only caption)", () => {
    const patch = finalizeOnStop({ text: "x", streaming: true }) as Record<string, unknown>
    expect(Object.keys(patch).sort()).toEqual(["stopped", "streaming"])
  })
})

describe("shouldCallBackendStop (A7 — FR-006 decision)", () => {
  it("skips the backend call in demo mode", () => {
    expect(shouldCallBackendStop({ taskId: "t1", demoMode: true })).toBe(false)
  })

  it("skips when no task id ever arrived", () => {
    expect(shouldCallBackendStop({ taskId: undefined, demoMode: false })).toBe(false)
  })

  it("calls when a task id exists in live mode", () => {
    expect(shouldCallBackendStop({ taskId: "t1", demoMode: false })).toBe(true)
  })
})
