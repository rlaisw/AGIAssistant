import type { ExportMessage, ExportModel, ExportTurn, ImageRef } from "./types"
import { ExportError } from "./types"

const MD_IMAGE_RE = /!\[([^\]]*)\]\(([^)\s]+)\)/g
const IMAGE_MARKER_RE = /\[image:\s*(\S+?)\]/g

function collectImages(text: string): ImageRef[] {
  const out: ImageRef[] = []
  for (const m of text.matchAll(MD_IMAGE_RE)) {
    out.push({ url: m[2], alt: m[1] })
  }
  for (const m of text.matchAll(IMAGE_MARKER_RE)) {
    out.push({ url: m[1], alt: "screenshot" })
  }
  return out
}

function turnMarkdown(msg: ExportMessage): string {
  let markdown = msg.text
  if (msg.code) {
    const fence = msg.codeName ? `\n\n\`\`\`${msg.codeName}\n${msg.code}\n\`\`\`` : `\n\n\`\`\`\n${msg.code}\n\`\`\``
    markdown += fence
  }
  if (msg.sources?.length) {
    markdown += `\n\n**Sources:** ${msg.sources.map((s) => `[${s}](${s})`).join(" · ")}`
  }
  return markdown
}

export function buildExportModel(messages: ExportMessage[]): ExportModel {
  if (messages.length === 0) {
    throw new ExportError("empty_conversation", "nothing to export")
  }

  const seen = new Set<number>()
  const turns: ExportTurn[] = []
  for (const msg of messages) {
    if (seen.has(msg.id)) continue
    seen.add(msg.id)
    turns.push({
      id: msg.id,
      role: msg.role,
      kind: msg.role === "user" ? "question" : "answer",
      markdown: turnMarkdown(msg),
      citations: msg.sources ?? [],
      images: collectImages(msg.text),
    })
  }

  const firstQuestion = messages.find((m) => m.role === "user")?.text ?? ""
  return {
    title: firstQuestion.slice(0, 80),
    exportedAt: new Date().toISOString(),
    turns,
  }
}
