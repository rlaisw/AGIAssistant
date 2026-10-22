export const runtime = "nodejs"

import { mapMessagesPage } from "@/lib/history/mappers"

const USER = "ai-chat-ui-user"

/**
 * Dify 1.17 exposes message history at GET /messages?conversation_id=…
 * (not /conversations/{id}/messages) with first_id cursor pagination.
 */
export async function GET(
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

  const { searchParams } = new URL(req.url)
  const limitRaw = Number(searchParams.get("limit") ?? 100)
  const limit = Number.isFinite(limitRaw) ? Math.min(Math.max(limitRaw, 1), 100) : 100
  const cursor = searchParams.get("cursor")
  const q = new URLSearchParams({
    user: USER,
    limit: String(limit),
    conversation_id: id,
  })
  if (cursor) q.set("first_id", cursor)

  let upstream: Response
  try {
    upstream = await fetch(`${apiBase}/messages?${q}`, {
      headers: { Authorization: `Bearer ${apiKey}` },
    })
  } catch (err) {
    console.error("[history] messages fetch failed:", err)
    return Response.json({ error: "messages unavailable" }, { status: 502 })
  }

  if (upstream.status === 404) {
    return Response.json({ error: "conversation not found" }, { status: 404 })
  }
  if (!upstream.ok) {
    const detail = await upstream.text().catch(() => "")
    console.error(`[history] Dify messages error (${upstream.status})`)
    return Response.json(
      { error: `Dify error (${upstream.status}): ${detail.slice(0, 200)}` },
      { status: 502 }
    )
  }

  const page = mapMessagesPage(await upstream.json())
  return Response.json(page)
}
