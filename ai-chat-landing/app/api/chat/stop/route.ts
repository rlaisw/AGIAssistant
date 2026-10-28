// spec 027 (contracts §2): same-origin stop proxy — the Dify service API key
// stays server-side; the browser only ever sees this route.
export const runtime = "nodejs"

const DIFY_USER = "ai-chat-ui-user" // must match the chat proxy's end-user id

export async function POST(req: Request) {
  const { taskId } = (await req.json().catch(() => ({}))) as { taskId?: unknown }
  if (typeof taskId !== "string" || !taskId.trim() || taskId.length > 128) {
    return Response.json({ error: "taskId is required" }, { status: 400 })
  }

  const apiKey = process.env.DIFY_API_KEY
  if (!apiKey) {
    return Response.json({ error: "DIFY_API_KEY is not configured" }, { status: 503 })
  }
  const apiBase = (
    process.env.DIFY_API_BASE_URL ?? "http://localhost/v1"
  ).replace(/\/+$/, "")

  try {
    const upstream = await fetch(
      `${apiBase}/chat-messages/${encodeURIComponent(taskId)}/stop`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${apiKey}`,
        },
        body: JSON.stringify({ user: DIFY_USER }),
        signal: AbortSignal.timeout(10_000),
      }
    )
    // completion race: the backend reports nothing to stop — client treats
    // this as success, never an error (contracts §2)
    if (upstream.status === 404) {
      return Response.json({ result: "no-task" })
    }
    if (!upstream.ok) {
      const detail = (await upstream.text().catch(() => "")).slice(0, 200)
      return Response.json({ error: `stop failed: ${detail}` }, { status: 502 })
    }
    return Response.json({ result: "ok" })
  } catch (error) {
    const message = error instanceof Error ? error.message : "stop request failed"
    return Response.json({ error: `stop failed: ${message.slice(0, 200)}` }, { status: 502 })
  }
}
