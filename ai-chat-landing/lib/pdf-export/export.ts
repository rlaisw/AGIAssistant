import type { ExportMessage, ExportModel } from "./types"
import { ExportError } from "./types"
import { buildExportModel } from "./transform"
import { slugifyFilename } from "./slugify"
import { pageSliceCount } from "./pagination"

export type CanvasLike = {
  width: number
  height: number
  toDataURL(type?: string, quality?: number): string
}

/** Rasterizes a fully-laid-out export container (html2canvas-pro in prod). */
export type Rasterizer = (container: HTMLElement) => Promise<CanvasLike>

/** Builds the offscreen export container (React renderer in prod). */
export type RenderFn = (model: ExportModel) => HTMLElement

export type ExportDeps = {
  render: RenderFn
  rasterize: Rasterizer
  save?: (blob: Blob, filename: string) => void
}

const A4_MM = { width: 210, height: 297 }

function pdfFromCanvas(canvas: CanvasLike, model: ExportModel): Promise<Blob> {
  return (async () => {
    const { jsPDF } = await import("jspdf")
    const doc = new jsPDF({ unit: "mm", format: "a4", orientation: "portrait" })
    const pages = pageSliceCount(canvas.width, canvas.height)
    const imageHeightMm = (canvas.height / canvas.width) * A4_MM.width
    const image = canvas.toDataURL("image/jpeg", 0.92)
    // shortcut: full image re-embedded per page with negative offsets — each
    // page clips its slice; fine at v1 sizes, re-crop with a canvas when decks
    // of pages make the file noticeably large
    for (let i = 0; i < pages; i++) {
      if (i > 0) doc.addPage()
      doc.addImage(
        image,
        "JPEG",
        0,
        -(i * imageHeightMm) / pages,
        A4_MM.width,
        imageHeightMm,
        undefined,
        "FAST"
      )
    }
    doc.setProperties({ title: model.title })
    const ab = doc.output("arraybuffer")
    return new Blob([ab], { type: "application/pdf" })
  })()
}

/**
 * Orchestrates one export: transform -> render -> rasterize -> PDF -> save.
 * Rejects with ExportError (never a raw exception). Images that failed to
 * load have already degraded to links inside the rendered container.
 */
export async function exportConversation(
  messages: ExportMessage[],
  deps: ExportDeps
): Promise<void> {
  const model = buildExportModel(messages)

  let canvas: CanvasLike
  try {
    canvas = await deps.rasterize(deps.render(model))
  } catch (err) {
    if (!(err instanceof ExportError)) console.error("[pdf-export] render failed:", err)
    throw err instanceof ExportError
      ? err
      : new ExportError("render_failed", undefined, err)
  }

  let blob: Blob
  try {
    blob = await pdfFromCanvas(canvas, model)
  } catch (err) {
    throw new ExportError("render_failed", undefined, err)
  }

  const filename = slugifyFilename(
    messages.find((m) => m.role === "user" && m.text.trim())?.text
  )
  const save = deps.save ?? browserSave
  try {
    save(blob, filename)
  } catch (err) {
    throw new ExportError("download_blocked", undefined, err)
  }
}

function browserSave(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = filename
  a.rel = "noopener"
  a.click()
  setTimeout(() => URL.revokeObjectURL(url), 5000)
}
