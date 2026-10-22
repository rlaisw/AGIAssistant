/**
 * Structural subset of the chat app's Message (app/page.tsx) — pure history
 * modules must not import from the app page (keeps React/Next out of tests;
 * same boundary pattern as spec 013's ExportMessage).
 */
export type Message = {
  id: number
  role: "user" | "assistant"
  text: string
  reasoning?: string
  code?: string
  codeName?: string
  sources?: string[]
  streaming?: boolean
}
