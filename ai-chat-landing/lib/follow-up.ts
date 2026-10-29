export type FollowUpSplit = { body: string; followUp?: string }

// the follow-up block is bounded by phrases: an OPENER offers ("Want me
// to…?"), a CLOSER hands the turn back ("Just tell me which…")
const OPENER = /^(?:want\b|would you like|should i|shall i)/i
const CLOSER = /^(?:just (?:say|let|tell)|let me know)/i

// options paragraphs ("A radar…\nA histogram…") sit between opener and
// closer — short lines only, so long content never gets swallowed
const isOptionsParagraph = (p: string) => {
  const lines = p.split("\n").map((l) => l.trim()).filter(Boolean)
  return lines.length > 0 && lines.length <= 6 && lines.every((l) => l.length <= 90)
}

/**
 * Follow-up prompt styling (user request 2026-10-28): the trailing
 * "Want me to…?" block of an answer renders as blue text with a 💡.
 * Pure split — the last paragraph qualifies when it ends with "?" or opens/
 * closes with a follow-up phrase; a closer then walks back over option
 * paragraphs to its opener. The answer keeps at least one body paragraph.
 */
export function splitFollowUp(text: string): FollowUpSplit {
  const paragraphs = text.trim().split(/\n{2,}/)
  if (paragraphs.length < 2) return { body: text }
  const last = paragraphs[paragraphs.length - 1].trim()
  const firstLine = last.split("\n")[0]
  const qualifies = /[?？]$/.test(last) || OPENER.test(firstLine) || CLOSER.test(firstLine)
  if (!qualifies) return { body: text }
  // an opener (or bare ?-question) IS the block; only a closer looks for one
  let start = paragraphs.length - 1
  if (CLOSER.test(firstLine)) {
    for (let back = 1; back <= 3 && paragraphs.length - 1 - back >= 1; back++) {
      const prev = paragraphs[paragraphs.length - 1 - back].trim()
      if (OPENER.test(prev.split("\n")[0])) {
        start = paragraphs.length - 1 - back
        break
      }
      if (!isOptionsParagraph(prev)) break
    }
  }
  return {
    body: paragraphs.slice(0, start).join("\n\n").trim(),
    followUp: paragraphs.slice(start).join("\n\n").trim(),
  }
}
