import { describe, expect, it } from "vitest"

import { parseDeckLink } from "./deck-url"

describe("parseDeckLink", () => {
  it("derives the page URL from an exports URL", () => {
    const link = parseDeckLink(
      "http://localhost:28080/exports/dify_20261018/dify_20261018_032504.pptx"
    )
    expect(link).not.toBeNull()
    expect(link!.kind).toBe("download")
    expect(link!.projectId).toBe("dify_20261018")
    expect(link!.stem).toBe("dify_20261018_032504")
    expect(link!.downloadUrl).toBe(
      "http://localhost:28080/exports/dify_20261018/dify_20261018_032504.pptx"
    )
    expect(link!.pageUrl).toBe(
      "http://localhost:28080/decks/dify_20261018/dify_20261018_032504/"
    )
  })

  it("derives the downloads URL from a decks page URL", () => {
    const link = parseDeckLink(
      "http://localhost:28080/decks/dify_20261018/dify_20261018_032504/"
    )
    expect(link).not.toBeNull()
    expect(link!.kind).toBe("page")
    expect(link!.downloadUrl).toBe(
      "http://localhost:28080/exports/dify_20261018/dify_20261018_032504.pptx"
    )
    expect(link!.pageUrl).toBe(
      "http://localhost:28080/decks/dify_20261018/dify_20261018_032504/"
    )
  })

  it("accepts a decks URL without the trailing slash", () => {
    const link = parseDeckLink(
      "http://localhost:28080/decks/dify_20261018/dify_20261018_032504"
    )
    expect(link).not.toBeNull()
    expect(link!.kind).toBe("page")
  })

  it("returns null for non-deck URLs", () => {
    expect(parseDeckLink("https://www.google.com")).toBeNull()
    expect(parseDeckLink("https://learn.microsoft.com/x")).toBeNull()
    expect(parseDeckLink("/exports/relative.pptx")).toBeNull()
    expect(parseDeckLink("/decks/relative/")).toBeNull()
    expect(parseDeckLink("http://localhost:3000/some/other/route")).toBeNull()
    expect(parseDeckLink("not a url")).toBeNull()
    expect(parseDeckLink("")).toBeNull()
  })

  it("returns null for malformed deck-family URLs", () => {
    expect(parseDeckLink("http://localhost:28080/exports/onlyproject/")).toBeNull()
    expect(
      parseDeckLink("http://localhost:28080/exports/p/stem.pdf")
    ).toBeNull()
    expect(parseDeckLink("http://localhost:28080/decks/p/")).toBeNull()
    expect(
      parseDeckLink("http://localhost:28080/decks/p/stem/extra/")
    ).toBeNull()
  })
})
