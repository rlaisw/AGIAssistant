export const runtime = "nodejs"

type StreamEvent = {
  type: "chunk" | "reasoning" | "replace" | "sources" | "done" | "error" | "ping"
  text?: string
  sources?: string[]
  message?: string
  conversationId?: string
}

export async function POST(req: Request) {
  const { query, conversationId, aiModel } = await req.json()
  if (!query || typeof query !== "string") {
    return Response.json({ error: "query is required" }, { status: 400 })
  }

  const apiKey = process.env.DIFY_API_KEY
  if (!apiKey) {
    return Response.json({ error: "DIFY_API_KEY is not configured" }, { status: 503 })
  }

  const apiBase = (
    process.env.DIFY_API_BASE_URL ?? "http://localhost/v1"
  ).replace(/\/+$/, "")

  const upstream = await fetch(`${apiBase}/chat-messages`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      // spec 026: cloud selection is global (the published app is patched);
      // sends carry only the local switch. Absent input = cloud (else branch),
      // battery and legacy callers stay byte-identical when aiModel is omitted.
      inputs:
        aiModel === "local"
          ? { ai_model: "local" }
          : aiModel
            ? { ai_model: "cloud" }
            : {},
      query,
      response_mode: "streaming",
      conversation_id: conversationId ?? "",
      user: "ai-chat-ui-user",
    }),
  })

  if (!upstream.ok || !upstream.body) {
    const detail = await upstream.text().catch(() => "")
    return Response.json(
      { error: `Dify error (${upstream.status}): ${detail.slice(0, 200)}` },
      { status: 502 }
    )
  }

  const encoder = new TextEncoder()
  const decoder = new TextDecoder()
  const reader = upstream.body.getReader()

  const stream = new ReadableStream({
    async start(controller) {
      const send = (event: StreamEvent) =>
        controller.enqueue(encoder.encode(JSON.stringify(event) + "\n"))
      let buffer = ""
      let difyConversationId: string | undefined

      try {
        for (;;) {
          const { done, value } = await reader.read()
          if (done) break
          buffer += decoder.decode(value, { stream: true })
          let boundary = buffer.indexOf("\n\n")
          while (boundary >= 0) {
            const block = buffer.slice(0, boundary)
            buffer = buffer.slice(boundary + 2)
            boundary = buffer.indexOf("\n\n")
            for (const line of block.split("\n")) {
              if (!line.startsWith("data:")) {
                if (
                  line.startsWith("event:") &&
                  line.slice(6).trim() === "ping"
                ) {
                  send({ type: "ping" })
                }
                continue
              }
              let event: Record<string, unknown>
              try {
                event = JSON.parse(line.slice(5).trim())
              } catch {
                continue
              }
              if (
                typeof event.conversation_id === "string" &&
                !difyConversationId
              ) {
                difyConversationId = event.conversation_id
              }
              switch (event.event) {
                case "message":
                case "agent_message":
                  if (event.answer) send({ type: "chunk", text: String(event.answer) })
                  break
                case "reasoning_chunk": {
                  const data = event.data as { reasoning?: string } | undefined
                  if (data?.reasoning) send({ type: "reasoning", text: data.reasoning })
                  break
                }
                case "message_replace":
                  if (event.answer) send({ type: "replace", text: String(event.answer) })
                  break
                case "message_end": {
                  const metadata = event.metadata as
                    | { retriever_resources?: { document_name?: string }[] }
                    | undefined
                  const names = (metadata?.retriever_resources ?? [])
                    .map((r) => r.document_name)
                    .filter((n): n is string => Boolean(n))
                  const sources = [...new Set(names)]
                  if (sources.length) send({ type: "sources", sources })
                  break
                }
                case "error":
                  send({
                    type: "error",
                    message: typeof event.message === "string" ? event.message : "Dify stream error",
                  })
                  break
              }
            }
          }
        }
        send({ type: "done", conversationId: difyConversationId })
      } catch (error) {
        send({
          type: "error",
          message: error instanceof Error ? error.message : "stream error",
        })
      } finally {
        controller.close()
      }
    },
    cancel() {
      reader.cancel().catch(() => {})
    },
  })

  return new Response(stream, {
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
      "Cache-Control": "no-cache",
    },
  })
}
