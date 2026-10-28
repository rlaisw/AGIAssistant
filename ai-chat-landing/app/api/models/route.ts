export const runtime = "nodejs"

const MODEL_NAME = "qwen3-8b-nothink"

/**
 * Host-side availability probe (contracts §1): Ollama is reachable from the
 * Next.js server on the same host — the browser never learns the address
 * (contract §5). Cloud is always reported available (local-only status).
 * Any failure, timeout, or malformed body means local: false — never guessed.
 */
export async function GET() {
  const base = (
    process.env.OLLAMA_BASE_URL ?? "http://127.0.0.1:11434"
  ).replace(/\/+$/, "")

  let localAvailable = false
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), 2000)
  try {
    const res = await fetch(`${base}/api/tags`, {
      signal: controller.signal,
      cache: "no-store",
    })
    if (res.ok) {
      const body = (await res.json().catch(() => null)) as
        | { models?: { name?: unknown }[] }
        | null
      const names = Array.isArray(body?.models)
        ? body.models.map((m) => String(m?.name ?? ""))
        : []
      localAvailable = names.some((n) => n === MODEL_NAME || n.startsWith(`${MODEL_NAME}:`))
    }
  } catch {
    localAvailable = false
  } finally {
    clearTimeout(timer)
  }

  return Response.json(
    {
      models: [
        { id: "cloud", available: true },
        { id: "local", available: localAvailable },
      ],
    },
    { headers: { "Cache-Control": "no-store" } }
  )
}
