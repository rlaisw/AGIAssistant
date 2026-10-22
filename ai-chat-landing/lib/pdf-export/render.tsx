"use client"

import { flushSync } from "react-dom"
import { createRoot } from "react-dom/client"

import { Markdown } from "@/components/markdown"
import { embedOrDegradeImages } from "@/lib/pdf-export/image-wait"
import type { ExportDeps, RenderFn } from "@/lib/pdf-export/export"
import type { ExportModel } from "@/lib/pdf-export/types"

// Print palette: inline rgb() only — no Tailwind classes inside the export
// container, so computed styles never contain oklch (rasterizer safety, R2)
// and dark mode cannot bleed into the PDF (FR-005).
const CONTAINER_CSS = `
  * { box-sizing: border-box; }
  body { margin: 0; }
`

function styleBlock(): string {
  return CONTAINER_CSS
}

const PALETTE = {
  bg: "rgb(255, 255, 255)",
  text: "rgb(23, 23, 23)",
  muted: "rgb(113, 113, 113)",
  user: "rgb(243, 244, 246)",
  border: "rgb(229, 231, 235)",
}

export function buildExportContainer(model: ExportModel): HTMLElement {
  const host = document.createElement("div")
  host.setAttribute("style", `background:${PALETTE.bg};color:${PALETTE.text};font-family:ui-sans-serif,system-ui,sans-serif;font-size:12px;line-height:1.55;width:744px;padding:32px;position:absolute;left:-99999px;top:0;`)
  const style = document.createElement("style")
  style.textContent = styleBlock()
  host.appendChild(style)

  const title = document.createElement("h1")
  title.setAttribute("style", `font-size:18px;font-weight:600;margin:0 0 4px 0;`)
  title.textContent = model.title || "Conversation"
  host.appendChild(title)

  const meta = document.createElement("p")
  meta.setAttribute("style", `color:${PALETTE.muted};font-size:10px;margin:0 0 20px 0;`)
  meta.textContent = `Exported ${new Date(model.exportedAt).toLocaleString()} · AgenticRAG Chat`
  host.appendChild(meta)

  const mount = document.createElement("div")
  host.appendChild(mount)
  return host
}

const ExportBody = ({ model }: { model: ExportModel }) => (
  <>
    {model.turns.map((turn) => (
      <div key={turn.id} style={{ marginBottom: 16 }}>
        <div
          style={{
            fontSize: 10,
            fontWeight: 700,
            letterSpacing: "0.04em",
            textTransform: "uppercase",
            color: turn.role === "user" ? PALETTE.muted : PALETTE.text,
            marginBottom: 4,
          }}
        >
          {turn.role === "user" ? "You" : "Assistant"}
        </div>
        <div
          style={
            turn.role === "user"
              ? {
                  background: PALETTE.user,
                  border: `1px solid ${PALETTE.border}`,
                  borderRadius: 8,
                  padding: "8px 12px",
                }
              : undefined
          }
        >
          <Markdown>{turn.markdown}</Markdown>
        </div>
      </div>
    ))}
  </>
)

export const renderExportModel: RenderFn = (model: ExportModel): HTMLElement => {
  const host = buildExportContainer(model)
  const mount = host.lastElementChild as HTMLElement
  const root = createRoot(mount)
  flushSync(() => root.render(<ExportBody model={model} />))
  return host
}

export async function rasterizeExport(container: HTMLElement) {
  // FR-012: wait for images, degrade unfetchable ones to labeled links
  await embedOrDegradeImages(container)
  // html2canvas rasterizes via a cloned iframe of the document — the
  // container MUST be attached or the clone lookup fails
  document.body.appendChild(container)
  try {
    const { default: html2canvas } = await import("html2canvas-pro")
    return await html2canvas(container, {
      scale: Math.min(2, window.devicePixelRatio || 1),
      useCORS: true,
      backgroundColor: PALETTE.bg,
    })
  } finally {
    container.remove()
  }
}

export function createExportDeps(): ExportDeps {
  return {
    render: renderExportModel,
    rasterize: rasterizeExport,
  }
}

