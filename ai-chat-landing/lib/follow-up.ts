export type FollowUpSplit = { body: string; followUp?: string }

/**
 * Follow-up prompt styling (user request 2026-10-28): the trailing
 * "Want me to…?" paragraph of an answer renders as blue text with a 💡.
 * Pure split — heuristic: the LAST paragraph that ends with "?", and only
 * when the answer has at least one other paragraph (a lone question is the
 * answer itself, not a follow-up).
 */
export function splitFollowUp(text: string): FollowUpSplit {
  const paragraphs = text.trim().split(/\n{2,}/)
  if (paragraphs.length < 2) return { body: text }
  const last = paragraphs[paragraphs.length - 1].trim()
  if (!/[?？]$/.test(last)) return { body: text }
  return {
    body: paragraphs.slice(0, -1).join("\n\n").trim(),
    followUp: last,
  }
}
