export type DeckLink = {
  kind: "download" | "page"
  projectId: string
  stem: string
  downloadUrl: string
  pageUrl: string
}

const SEGMENT = "[A-Za-z0-9][A-Za-z0-9_-]*"
const EXPORTS_RE = new RegExp(`^/exports/(${SEGMENT})/(${SEGMENT})\\.pptx$`)
const DECKS_RE = new RegExp(`^/decks/(${SEGMENT})/(${SEGMENT})/?$`)

export function parseDeckLink(href: string): DeckLink | null {
  let url: URL
  try {
    url = new URL(href)
  } catch {
    return null
  }
  if (url.protocol !== "http:" && url.protocol !== "https:") return null
  const path = url.pathname
  const exports = EXPORTS_RE.exec(path)
  if (exports) {
    return {
      kind: "download",
      projectId: exports[1],
      stem: exports[2],
      downloadUrl: `${url.origin}${path}`,
      pageUrl: `${url.origin}/decks/${exports[1]}/${exports[2]}/`,
    }
  }
  const decks = DECKS_RE.exec(path)
  if (decks) {
    return {
      kind: "page",
      projectId: decks[1],
      stem: decks[2],
      downloadUrl: `${url.origin}/exports/${decks[1]}/${decks[2]}.pptx`,
      pageUrl: `${url.origin}/decks/${decks[1]}/${decks[2]}/`,
    }
  }
  return null
}
