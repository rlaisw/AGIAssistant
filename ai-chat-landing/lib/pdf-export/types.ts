export type ExportRole = "user" | "assistant"

/**
 * Structural subset of the chat app's Message (app/page.tsx) that the export
 * needs. The real Message satisfies this without changes; the pure transform
 * module must not import from the app page (keeps React/Next out of tests).
 */
export type ExportMessage = {
  id: number
  role: ExportRole
  text: string
  reasoning?: string
  code?: string
  codeName?: string
  sources?: string[]
  streaming?: boolean
}

export type ImageRef = {
  url: string
  alt: string
}

export type ExportTurn = {
  id: number
  role: ExportRole
  kind: "question" | "answer"
  markdown: string
  citations: string[]
  images: ImageRef[]
}

export type ExportModel = {
  title: string
  exportedAt: string
  turns: ExportTurn[]
}

export type ExportErrorCode = "empty_conversation" | "render_failed" | "download_blocked"

export class ExportError extends Error {
  readonly code: ExportErrorCode

  constructor(code: ExportErrorCode, message?: string, readonly cause?: unknown) {
    super(message ?? code)
    this.name = "ExportError"
    this.code = code
  }
}

export type ExportStateName = "idle" | "busy" | "error"
