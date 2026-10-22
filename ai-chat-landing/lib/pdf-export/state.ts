import type { ExportStateName } from "./types"
import { ExportError } from "./types"

type ExportRun = () => Promise<void>

export function createExportState() {
  let state: ExportStateName = "idle"
  let error: ExportError | undefined

  return {
    get: () => state,
    get error() {
      return error
    },
    dismiss() {
      if (state === "error") {
        state = "idle"
        error = undefined
      }
    },
    run(fn: ExportRun): Promise<void> {
      if (state === "busy") return Promise.resolve()
      state = "busy"
      error = undefined
      return fn().then(
        () => {
          state = "idle"
        },
        (err: unknown) => {
          error =
            err instanceof ExportError
              ? err
              : new ExportError("render_failed", undefined, err)
          state = "error"
        }
      )
    },
  }
}
