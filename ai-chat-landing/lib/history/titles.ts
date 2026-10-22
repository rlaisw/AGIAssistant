const MAX_TITLE = 60

/** FR-012: backend name, else first-question fallback (≤60), never "Untitled". */
export function titleFor(difyName: string | null | undefined, firstQuestion?: string): string {
  const name = (difyName ?? "").trim()
  if (name) return name
  const fallback = (firstQuestion ?? "").trim()
  if (fallback) return fallback.slice(0, MAX_TITLE)
  return "New conversation"
}
