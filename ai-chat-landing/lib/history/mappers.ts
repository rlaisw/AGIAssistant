import type { Message } from "@/lib/history/message-type"
import type { ConversationPage, ConversationRecord } from "./types"
import { titleFor } from "./titles"

type DifyConversation = {
  id: string
  name?: string | null
  created_at?: number | null
  updated_at?: number | null
}

type DifyConversationList = {
  data: DifyConversation[]
  has_more?: boolean
  last_id?: string | null
}

const lastActivity = (c: DifyConversation): number | null => {
  const ms = (unixSec?: number | null) =>
    typeof unixSec === "number" && Number.isFinite(unixSec) ? unixSec * 1000 : null
  return ms(c.updated_at) ?? ms(c.created_at)
}

/** contracts §1: Dify page → app records + cursor (server-side use). */
export function mapConversationPage(page: DifyConversationList): ConversationPage {
  const conversations: ConversationRecord[] = (page.data ?? []).map((c) => {
    const title = (c.name ?? "").trim() ? c.name!.trim() : titleFor(c.name, undefined)
    if (!(c.name ?? "").trim()) {
      console.warn("[history] conversation without a name; derived title:", c.id)
    }
    return { difyId: c.id, title, lastActivityAt: lastActivity(c) }
  })
  // Dify 1.17 omits last_id from the list response; the cursor is the last
  // record's id (that's what last_id pagination expects you to pass back).
  // No cursor when exhausted (has_more false) per the contract.
  const hasMore = Boolean(page.has_more)
  return {
    conversations,
    hasMore,
    nextCursor: hasMore
      ? page.last_id ?? conversations.at(-1)?.difyId ?? null
      : null,
  }
}

type DifyMessageRecord = {
  id?: string
  query?: string | null
  answer?: string | null
  created_at?: number | null
  // Dify 1.17 /messages returns retriever_resources top-level; the stream's
  // message_end event nests it under metadata — accept both
  retriever_resources?: { document_name?: string }[] | null
  metadata?: { retriever_resources?: { document_name?: string }[] } | null
}

/** contracts §2: Dify messages records → paired app Message[] (sequential ids). */
type DifyMessagesList = {
  data?: DifyMessageRecord[]
  has_more?: boolean
  first_id?: string | null
}

export function mapMessagesPage(page: DifyMessagesList): { messages: Message[]; hasMore: boolean } {
  const messages: Message[] = []
  for (const rec of page.data ?? []) {
    const query = (rec.query ?? "").trim()
    const answer = (rec.answer ?? "").trim()
    if (query) messages.push({ id: messages.length + 1, role: "user", text: rec.query!, streaming: false })
    if (answer) {
      const resources = rec.retriever_resources ?? rec.metadata?.retriever_resources ?? []
      const names = resources
        .map((r) => r.document_name)
        .filter((n): n is string => Boolean(n))
      const sources = [...new Set(names)]
      messages.push({
        id: messages.length + 1,
        role: "assistant",
        text: rec.answer!,
        streaming: false,
        ...(sources.length ? { sources } : {}),
      })
    }
  }
  return { messages, hasMore: Boolean(page.has_more) }
}
