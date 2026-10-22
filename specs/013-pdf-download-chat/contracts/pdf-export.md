# Contract: PDF Export Module (UI-internal)

The feature touches no MCP tool schemas (Constitution I untouched). Its
contracts are the module boundary inside `ai-chat-landing/lib/pdf-export/`
and one additive HTTP header on existing sidecar routes.

## 1. Module interface (consumed by the chat header button)

```ts
// build the exportable view of a conversation (pure, testable)
buildExportModel(messages: ExportMessage[]): ExportModel   // throws ExportError("empty_conversation")

// filename per FR-006 (pure, testable)
slugifyFilename(firstQuestion?: string): string

// export state machine (pure, testable)
createExportState(): { get(): "idle"|"busy"|"error", run(fn): Promise<void>, dismiss(): void, error?: ExportError }

// image embed/link decision (pure, testable; production path via embedOrDegradeImages)
decideImages(urls: string[], opts): Promise<{url, embed}[]>
embedOrDegradeImages(container: HTMLElement, timeoutMs?): Promise<void>  // replaces failures with labeled links + console warn

// orchestrator (node-testable: render/rasterize/save seams injected)
exportConversation(messages: ExportMessage[], deps: ExportDeps): Promise<void>

type ExportDeps = {
  render: (model: ExportModel) => HTMLElement   // React renderer in prod, stub in tests
  rasterize: (container: HTMLElement) => Promise<CanvasLike>  // html2canvas-pro in prod, stub in tests
  save?: (blob: Blob, filename: string) => void  // browser anchor download in prod, capture in tests
}
```

**Invariants**:
- `exportConversation` rejects with `ExportError` (never a raw exception) on
  `render_failed` or `download_blocked`; it resolves even when some images
  degrade to links.
- Reasoning text is never present in the output model (FR-011).
- Output: one A4-paginated PDF blob, light print palette (FR-005), title
  block + ordered turns.

## 2. Browser download behavior (FR-004)

- Blob → object URL → anchor click (native download, filename from
  `slugifyFilename`); URL revoked after click.
- On `SecurityError`/blocked download: resolve as `ExportError
  ("download_blocked")` — surfaced as a hint, no file delivered.

## 3. Sidecar media routes (additive; enables FR-012 same-stack images)

| Route (existing) | Added header |
|------------------|--------------|
| `GET /exports/<project>/<file>` | `Access-Control-Allow-Origin: *` |
| `GET /decks/<project>/<stem>/slides/<file>` | `Access-Control-Allow-Origin: *` |
| infographic/chart media served by the sidecar | `Access-Control-Allow-Origin: *` |

No route, schema, or status-code changes; MCP `/mcp` and Dify-facing routes
are untouched. Remote third-party images (web research) keep the
attempt-CORS → labeled-link fallback (FR-012).

## 4. New frontend dependencies (Constitution III record)

| Package | Why needed | Loaded |
|---------|-----------|--------|
| `jspdf` | PDF page assembly/writing; no stdlib/platform equivalent exists | lazy `import()` on first export click |
| `html2canvas-pro` | Rasterizes the offscreen render; stock fork chokes on Tailwind 4 oklch colors (R2) | lazy `import()` on first export click |
