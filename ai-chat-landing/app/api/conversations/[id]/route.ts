export const runtime = "nodejs"

const USER = "ai-chat-ui-user"

export async function DELETE(
  req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const apiKey = process.env.DIFY_API_KEY
  if (!apiKey) {
    return Response.json({ error: "DIFY_API_KEY is not configured" }, { status: 503 })
  }
  const apiBase = (
    process.env.DIFY_API_BASE_URL ?? "http://localhost/v1"
  ).replace(/\/+$/, "")

  const { id } = await params
  if (!id || !/^[A-Za-z0-9_-]+$/.test(id)) {
    return Response.json({ error: "invalid conversation id" }, { status: 400 })
  }

  let upstream: Response
  try {
    upstream = await fetch(
      `${apiBase}/conversations/${encodeURIComponent(id)}`,
      {
        method: "DELETE",
        headers: { Authorization: `Bearer ${apiKey}`, "Content-Type": "application/json" },
        // Dify 1.17 expects user in the JSON body for DELETE (WhereisUserArg.JSON)
        body: JSON.stringify({ user: USER }),
      }
    )
  } catch (err) {
    console.error("[history] delete fetch failed:", err)
    return Response.json({ error: "delete failed" }, { status: 502 })
  }

  if (upstream.status === 404) {
    return Response.json({ error: "conversation not found" }, { status: 404 })
  }
  if (!upstream.ok) {
    const detail = await upstream.text().catch(() => "")
    console.error(`[history] Dify delete error (${upstream.status})`)
    return Response.json(
      { error: `Dify error (${upstream.status}): ${detail.slice(0, 200)}` },
      { status: 502 }
    )
  }

  return Response.json({ ok: true })
}
