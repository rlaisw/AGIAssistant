import type { HistoryError } from "./types"
import { HistoryError as HistoryErrorClass } from "./types"

export type DeleteRequest = (difyId: string) => Promise<void>

export type DeleteStatus = "idle" | "menu" | "confirming" | "in-flight" | "done" | "error"

export function createDeleteState({ deleteRequest }: { deleteRequest: DeleteRequest }) {
  let status: DeleteStatus = "idle"
  let error: HistoryError | undefined
  let inFlight: Promise<void> | null = null

  /** FR-005: backend failure is wrapped as delete_failed, row stays. */
  const wrap = (err: unknown): HistoryError =>
    err instanceof HistoryErrorClass
      ? err
      : new HistoryErrorClass("delete_failed", undefined, err)

  return {
    open(): void {
      if (status === "idle" || status === "error") {
        status = "menu"
        error = undefined
      }
    },
    chooseDelete(): void {
      if (status === "menu") status = "confirming"
    },
    cancel(): void {
      if (status === "confirming" || status === "menu" || status === "error") {
        status = "idle"
        error = undefined
      }
    },
    confirm(difyId: string): Promise<void> {
      if (status !== "confirming" || inFlight) return inFlight ?? Promise.resolve()
      status = "in-flight"
      inFlight = deleteRequest(difyId)
        .then(() => {
          status = "done"
          error = undefined
        })
        .catch((err: unknown) => {
          error = wrap(err)
          status = "error"
        })
        .finally(() => {
          inFlight = null
        })
      return inFlight
    },
    get status() {
      return status
    },
    get error(): HistoryError | undefined {
      return error
    },
  }
}
