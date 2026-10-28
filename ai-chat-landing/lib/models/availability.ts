/**
 * Fetch the host-side /api/models probe when the drop-down opens (SC-002,
 * 5 s budget) — returns whether the LOCAL model is usable. Cloud entries are
 * never probed (clarify decision: local-only status). Any error, timeout, or
 * malformed payload degrades to false — never guessed.
 */
export async function fetchAvailability(
  fetchImpl: typeof fetch = fetch,
  timeoutMs = 5000
): Promise<boolean> {
  try {
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), timeoutMs)
    try {
      const res = await fetchImpl("/api/models", { signal: controller.signal })
      if (!res.ok) return false
      const body = (await res.json()) as { models?: { id?: string; available?: boolean }[] }
      const models = Array.isArray(body?.models) ? body.models : []
      return models.find((m) => m.id === "local")?.available === true
    } finally {
      clearTimeout(timer)
    }
  } catch {
    return false
  }
}
