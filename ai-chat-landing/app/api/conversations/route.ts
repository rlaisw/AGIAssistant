export const runtime = "nodejs"

import { mapConversationPage } from "@/lib/history/mappers"

const USER = "ai-chat-ui-user"

export async function GET(req: Request) {
  const apiKey = process.env.DIFY_API_KEY
  if (!apiKey) {
    return Response.json({ error: "DIFY_API_KEY is not configured" }, { status: 503 })
  }
  const apiBase = (
    process.env.DIFY_API_BASE_URL ?? "http://localhost/v1"
  ).replace(/\/+$/, "")

  const { searchParams } = new URL(req.url)
  const cursor = searchParams.get("cursor")
  const limitRaw = Number(searchParams.get("limit") ?? 20)
  const limit = Number.isFinite(limitRaw) ? Math.min(Math.max(limitRaw, 1), 100) : 20

  const params = new URLSearchParams({ user: USER, limit: String(limit) })
  if (cursor) params.set("last_id", cursor)

  let upstream: Response
  try {
    upstream = await fetch(`${apiBase}/conversations?${params}`, {
      headers: { Authorization: `Bearer ${apiKey}` },
    })
  } catch (err) {
    console.error("[history] conversations fetch failed:", err)
    return Response.json({ error: "history unavailable" }, { status: 502 })
  }

  if (!upstream.ok) {
    const detail = await upstream.text().catch(() => "")
    console.error(`[history] Dify conversations error (${upstream.status})`)
    return Response.json(
      { error: `Dify error (${upstream.status}): ${detail.slice(0, 200)}` },
      { status: 502 }
    )
  }

  const page = mapConversationPage(await upstream.json())
  return Response.json(page)
}
