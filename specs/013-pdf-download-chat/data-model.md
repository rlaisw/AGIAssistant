# Data Model: PDF Download of Chat Conversations

All types live in `ai-chat-landing/lib/pdf-export/` (new module; pure-logic
parts importable by vitest without React).

## Entities

### ExportModel (transform of the existing chat model — no new persistence)

Built from `Message { id, role, text, reasoning?, code?, codeName?, sources?,
streaming? }` / `Conversation { id, title, messages }` (`app/page.tsx`):

```ts
type ExportTurn = {
  id: number            // message id, monotonic (FR-009 ordering)
  role: "user" | "assistant"
  kind: "question" | "answer"
  markdown: string       // text as-is (markdown reuses the app renderer)
  code?: string          // codeName/code artifact → fenced block in markdown
  codeName?: string
  citations: string[]    // sources → rendered as a "Sources" link list (FR-002)
  images: ImageRef[]     // ![alt](url) + [image: url] markers (FR-012)
}
type ExportModel = {
  title: string          // document title block (conversation title or first
                          // question, capped) + export timestamp
  turns: ExportTurn[]    // completed turns; streaming turn = partial text,
                          // never duplicated (filter by id)
}
```

**Validation**: `buildExportModel(messages)` throws `ExportError
{code:"empty_conversation"}` when no completed turns exist (FR-001/edge).
`reasoning` is dropped at transform time (FR-011). Deck action bars and
infographic/chart URLs pass through as markdown links (FR-010).

### ExportState machine (FR-007/FR-008)

```text
idle ──click──► busy ──success──► idle (download fires)
                 │ └─failure──► error ──dismiss/auto──► idle
                 └─click while busy = ignored (no transition)
```

- Transitions are the only mutation surface; the icon renders from state.
- Every busy→error transition carries an `ExportError` (below).

### ExportError (R6 taxonomy)

```ts
type ExportErrorCode =
  | "empty_conversation"   // nothing to export (icon also disabled upstream)
  | "render_failed"        // rasterizer/pagination threw → visible error (FR-007)
  | "download_blocked"    // browser refused the blob download → hint (edge)
type ExportError = { code: ExportErrorCode; cause?: unknown }
```
`image_unavailable` is intentionally NOT an ExportError: it is a per-image
silent degrade to a labeled link inside the document (FR-012), logged to
console for diagnosis, never shown to the user.

### Filename (FR-006, R4)

`slugifyFilename(firstQuestion | undefined): string`
- slug: lowercase, non-alphanumeric → `-`, collapse runs, trim, cap 40 chars,
  `.pdf` suffix; empty → `chat-YYYYMMDD-HHmmss.pdf` (local clock).

## Test matrix (Constitution II — written before implementation)

| Test (vitest) | Asserts |
|---------------|---------|
| slugify basic/unicode/40-cap/empty-fallback | FR-006 |
| buildExportModel: ordering, no duplicate streaming ids, reasoning dropped | FR-002/009/011 |
| buildExportModel: citations → link list; `[image: url]` → ImageRef | FR-002/010/012 |
| buildExportModel: empty input throws `empty_conversation` | FR-001 |
| ExportState: full transition table incl. busy re-entry ignored | FR-008 |
| ExportError mapping: render_failed / download_blocked messages | FR-007 |
| image-wait helper (stubbed Image load/timeout): resolve/fail/timeout | FR-012 |
| orchestrator (node-env, render/rasterize/save seams stubbed): success→blob download; throw→error state | FR-002/007 |
| pagination slice math: canvas → A4 pages, no zero-height page | FR-003/edge |

## State & storage

No persistence anywhere (FR-004): the model is built in memory at click time
from the live conversation; the only output is the downloaded blob.
